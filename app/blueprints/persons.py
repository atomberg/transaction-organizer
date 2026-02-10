"""Routes for managing people and receipt generation."""

from datetime import datetime
from pathlib import Path

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask import current_app as app
from flask_weasyprint import HTML, render_pdf

from app import db
from app.models.person import Person, get_persons
from app.models.tax_receipt import (
    TaxReceipt,
    get_receipts_for_person,
    issue_annual_person_receipt,
)

bp = Blueprint('persons', __name__, url_prefix='/persons')


@bp.add_app_template_filter
def display_newlines(value):
    return value.replace('\n', '<br>')


def _org_value():
    return app.config.get('ORG') or app.config.get('ORGANISATION_NAME') or 'Unknown organisation'


def _treasurer_value():
    return app.config.get('TREASURER_NAME') or app.config.get('TREASURER') or 'Unknown treasurer'


def _signature_url():
    if app.config.get('SIGNATURE_IMAGE_URL'):
        return app.config['SIGNATURE_IMAGE_URL']

    static_dir = Path(app.root_path) / 'static'
    if (static_dir / 'signature.png').exists():
        return '/static/signature.png'
    if (static_dir / 'signature.jpg').exists():
        return '/static/signature.jpg'
    return '/static/sample-signature.png'


def _receipt_context_from_record(receipt_record):
    return {
        'org': receipt_record.org_snapshot,
        'treasurer': receipt_record.treasurer_snapshot,
        'tax_year': receipt_record.tax_year,
        'receipt_number': receipt_record.receipt_number,
        'receipt_date': receipt_record.issued_at.strftime('%B %e, %Y'),
        'name': receipt_record.name_snapshot,
        'address': receipt_record.address_snapshot,
        'amount': receipt_record.total_amount,
        'signature_url': _signature_url(),
    }


@bp.route('/', methods=['GET'])
def get_all():
    """Display all persons in a table."""
    return render_template('person_table.html.j2', persons=get_persons(), year=datetime.now().year)


@bp.route('/form', methods=['GET'])
def add_form():
    """Render the form to add a new person."""
    return render_template('person_add.html.j2')


@bp.route('/', methods=['POST'])
def add():
    """Add a new person."""
    p = Person(
        first_name=request.values['first_name'],
        last_name=request.values['last_name'],
        phone=request.values['phone'],
        email=request.values['email'],
        address=request.values['address'],
    )
    db.session.add(p)
    db.session.commit()
    return get_all()


@bp.route('/<int:person_id>', methods=['GET'])
def get(person_id):
    """Get a person by id."""
    person = Person.get_by_id(person_id)
    if person is None:
        return ('Person not found', 404)
    selected_year = int(request.values.get('year', app.config.get('TAX_YEAR')))
    return render_template(
        'person_get.html.j2',
        person=person.to_dict(),
        tax_year=selected_year,
    )


@bp.route('/<int:person_id>/edit', methods=['GET'])
def edit(person_id):
    """Edit a person by id."""
    return render_template('person_edit.html.j2', person=Person.get_by_id(person_id).to_dict())


@bp.route('/<int:person_id>', methods=['POST'])
def update(person_id):
    """Update a person by id."""
    p = Person.get_by_id(person_id)
    p.first_name = request.values['first_name']
    p.last_name = request.values['last_name']
    p.phone = request.values['phone']
    p.email = request.values['email']
    p.address = request.values['address']
    p.notes = request.values['notes']
    p.updated_at = datetime.now()

    db.session.add(p)
    db.session.commit()

    return get(person_id)


@bp.route('/<int:person_id>', methods=['DELETE'])
@bp.route('/<int:person_id>/delete', methods=['GET'])
def delete(person_id):
    """Delete a person by id."""
    p = Person.get_by_id(person_id)
    if len(p.transactions) > 0:
        flash('Cannot delete a person with transactions. Please delete those first.')
        return edit(person_id)
    else:
        db.session.delete(p)
        db.session.commit()
        return get_all()


@bp.route('/data', methods=['GET'])
def get_data():
    """Get all of persons data."""
    return render_template('person_data.html.j2', persons=get_persons())


@bp.route('/<int:person_id>/receipt/<int:year>', methods=['GET'])
def receipt(person_id, year):
    """Get a person's tax receipt by id."""
    p = Person.get_by_id(person_id)
    if p is None:
        return ('Person not found', 404)
    return render_template(
        'tax_receipt.html.j2',
        org=_org_value(),
        treasurer=_treasurer_value(),
        tax_year=year,
        receipt_number=p.id,
        receipt_date=datetime.now().strftime("%B %e, %Y"),
        name=p.full_name,
        address=p.address,
        amount=sum([t.amount for t in p.transactions if t.date.year == year and not t.receipt]),
        signature_url=_signature_url(),
    )


@bp.route('/<int:person_id>/receipt/<int:year>/pdf', methods=['GET'])
def receipt_pdf(person_id, year):
    """Get a person's tax receipt by id in PDF form."""
    person = Person.get_by_id(person_id)
    if person is None:
        return ('Person not found', 404)
    try:
        receipt_record = issue_annual_person_receipt(
            person,
            year,
            _org_value(),
            _treasurer_value(),
        )
    except ValueError as exc:
        flash(str(exc))
        return redirect(url_for('persons.get', person_id=person_id, year=year))

    return render_pdf(url_for('persons.receipt_by_id', receipt_id=receipt_record.id))


@bp.route('/receipts/<int:receipt_id>', methods=['GET'])
def receipt_by_id(receipt_id):
    """Render a previously issued tax receipt."""
    receipt_record = TaxReceipt.get_by_id(receipt_id)
    if receipt_record is None:
        return ('Receipt not found', 404)
    return render_template('tax_receipt.html.j2', **_receipt_context_from_record(receipt_record))


@bp.route('/receipts/<int:receipt_id>/pdf', methods=['GET'])
def receipt_pdf_by_id(receipt_id):
    """Download a previously issued tax receipt as PDF."""
    receipt_record = TaxReceipt.get_by_id(receipt_id)
    if receipt_record is None:
        return ('Receipt not found', 404)
    return render_pdf(url_for('persons.receipt_by_id', receipt_id=receipt_record.id))


@bp.route('/<int:person_id>/receipts', methods=['GET'])
def receipt_history(person_id):
    """Show all issued receipts for one person."""
    person = Person.get_by_id(person_id)
    if person is None:
        return ('Person not found', 404)
    selected_year = request.values.get('year')
    tax_year = int(selected_year) if selected_year else None
    receipts = get_receipts_for_person(person_id, tax_year=tax_year)
    return render_template(
        'person_receipts.html.j2',
        person=person.to_dict(),
        receipts=receipts,
        selected_year=selected_year or '',
    )


@bp.route('/receipts/<int:year>/', methods=['GET'])
def all_receipts_pdf(year):
    """Get a person's tax receipt by id in PDF form."""
    docs = {}
    for p in get_persons():
        if sum([t.amount for t in p.transactions if t.date.year == year and not t.receipt]) > 0:
            docs[p.full_name] = HTML(url_for('persons.receipt', person_id=p.id, year=year)).render()

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
