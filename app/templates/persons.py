from datetime import datetime
from fastapi import Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from ..crud.persons import get_persons, get_person_by_id


def currency_format(value):
    return f'{value:.2f}'


def display_newlines(value):
    return value.replace('\n', '<br>')


templates = Jinja2Templates(directory="app/templates")
templates.env.filters['currency_format'] = currency_format
templates.env.filters['display_newlines'] = display_newlines


def fill_person_add_template(request: Request) -> HTMLResponse:
    """Fill the input template with latest transactions."""
    return templates.TemplateResponse('person_add.html.j2', dict(request=request))


def fill_person_data_template(request: Request, db: Session) -> HTMLResponse:
    """Fill the data template."""
    template_data = dict(request=request, persons=get_persons(db))
    return templates.TemplateResponse('person_data.html.j2', template_data)


def fill_person_edit_template(request: Request, db: Session, person_id: int) -> HTMLResponse:
    """Fill the edit template with data from the given person."""
    template_data = dict(request=request, person=get_person_by_id(db, person_id))
    return templates.TemplateResponse('person_edit.html.j2', template_data)


def fill_person_get_template(request: Request, db: Session, person_id: int, tax_year: int) -> HTMLResponse:
    """Fill the edit template with data from given transaction."""
    template_data = dict(request=request, person=get_person_by_id(db, person_id), tax_year=tax_year)
    return templates.TemplateResponse('person_get.html.j2', template_data)


def fill_person_table_template(request: Request, db: Session) -> HTMLResponse:
    template_data = dict(request=request, persons=get_persons(db), year=datetime.now().year)
    return templates.TemplateResponse('person_table.html.j2', template_data)


def fill_year_tax_receipt_template(
    request: Request, person_id: int, organisation_name: str, treasurer_name: str, year: int, db: Session
) -> HTMLResponse:
    p = get_person_by_id(db, person_id)
    template_data = dict(
        request=request,
        org=organisation_name,
        treasurer=treasurer_name,
        tax_year=year,
        receipt_number=p.id,
        receipt_date=datetime.now().strftime("%B %e, %Y"),
        name=p.full_name,
        address=p.address,
        amount=sum([t.amount for t in p.transactions if t.date.year == year and not t.receipt]),
    )
    return templates.TemplateResponse('tax_receipt.html.j2', template_data)
