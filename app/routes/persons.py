from datetime import date, datetime
from fastapi import APIRouter, Request, Depends, Form
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from app.crud.persons import get_person_by_id
from app.dependencies import get_db, get_settings, Settings

from flask_weasyprint import HTML, render_pdf
from typing import Optional
from app.schemas import PersonCreate, PersonUpdate
from app.crud.persons import get_person_by_id, get_persons, create_person, update_person, remove_person
from app.templates.persons import (
    fill_person_add_template,
    fill_person_data_template,
    fill_person_edit_template,
    fill_person_get_template,
    fill_person_table_template,
    fill_year_tax_receipt_template,
)

router = APIRouter()


@router.get('/', response_class=HTMLResponse)
async def persons_table_view(request: Request, db: Session = Depends(get_db)):
    """Display all persons in a table."""
    return fill_person_table_template(request, db)


@router.get('/form', response_class=HTMLResponse)
async def add_new_person_form_view(request: Request, db: Session = Depends(get_db)):
    """Render the form to add a new person."""
    return fill_person_add_template(request)


@router.post('/', response_class=HTMLResponse)
async def create_person_view(
    request: Request,
    first_name: str = Form('first_name'),
    last_name: str = Form('last_name'),
    phone: Optional[str] = Form('phone'),
    email: Optional[str] = Form('email'),
    address: Optional[str] = Form('address'),
    db: Session = Depends(get_db),
):
    """Add a new person."""
    p = PersonCreate(first_name, last_name, phone, email, address)
    create_person(db, p)
    return fill_person_table_template(request, db)


@router.get('/{person_id}', response_class=HTMLResponse)
async def person_summary_view(
    request: Request, person_id: int, db: Session = Depends(get_db), config: Settings = Depends(get_settings)
):
    """Get a person by id."""
    year = config.tax_year
    return fill_person_get_template(request, db, person_id, year)


@router.get('/{person_id}/edit', response_class=HTMLResponse)
async def edit_person_view(request: Request, person_id: int, db: Session = Depends(get_db)):
    """Edit a person by id."""
    return fill_person_edit_template(request, db, person_id)


@router.post('/{person_id}', response_class=HTMLResponse)
async def update_person_view(
    request: Request,
    person_id: int,
    first_name: str = Form('first_name'),
    last_name: str = Form('last_name'),
    phone: Optional[str] = Form('phone'),
    email: Optional[str] = Form('email'),
    address: Optional[str] = Form('address'),
    notes: Optional[str] = Form('notes'),
    db: Session = Depends(get_db),
):
    """Update a person by id."""
    p = PersonUpdate(first_name, last_name, phone, email, address, notes, updated_at=datetime.now())
    update_person(db, person_id, new_values=p)

    return fill_person_edit_template(request, db, person_id)


@router.delete('/{person_id}', response_class=HTMLResponse)
@router.get('/{person_id}/delete')
async def delete_person_view(request: Request, person_id: int, db: Session = Depends(get_db)):
    """Delete a person by id."""
    p = get_person_by_id(db, person_id)
    if len(p.transactions) > 0:
        # flash('Cannot delete a person with transactions. Please delete those first.')
        return fill_person_edit_template(request, db, person_id)
    else:
        db.session.delete(p)
        db.session.commit()
        return persons_table_view(request, db)


@router.get('/data', response_class=HTMLResponse)
async def person_data_view(request: Request, db: Session = Depends(get_db)):
    """Get all of persons data."""
    return fill_person_data_template(request, db)


@router.get('/{person_id}/receipt/{year}', response_class=HTMLResponse)
async def person_tax_receipt_view(
    request: Request,
    person_id: int,
    year: int,
    db: Session = Depends(get_db),
    config: Settings = Depends(get_settings),
):
    """Get a person's tax receipt by id."""
    return fill_year_tax_receipt_template(
        request, person_id, config.organisation_name, config.treasurer_name, year, db
    )


@router.get('/{person_id}/receipt/{year}/pdf')
async def receipt_pdf(request: Request, person_id, year):
    """Get a person's tax receipt by id in PDF form."""
    return render_pdf(request.url_for('persons.receipt', person_id=person_id, year=year))


@router.get('/receipts/{year}')
async def all_receipts_pdf_view(request: Request, year: int, db: Session = Depends(get_db)):
    """Get a person's tax receipt by id in PDF form."""
    docs = {}
    for p in get_persons(db):
        if sum([t.amount for t in p.transactions if t.date.year == year and not t.receipt]) > 0:
            docs[p.full_name] = HTML(request.url_for('persons.receipt', person_id=p.id, year=year)).render()

    if len(docs) == 0:
        return None

    all_pages = []
    final_doc = None
    for full_name, doc in docs.items():
        final_doc = doc
        doc.pages[0].bookmarks = [(1, full_name, doc.pages[0].bookmarks[0][2], 'open')]
        for page in doc.pages[1:]:
            page.bookmarks = []
        all_pages.extend(doc.pages)

    final_doc.metadata.title = f'Tax receipts for {year}'
    pdf = final_doc.copy(all_pages).write_pdf()
    return app.response_class(pdf, mimetype='application/pdf')
