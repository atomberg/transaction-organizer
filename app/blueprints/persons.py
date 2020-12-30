from datetime import datetime

from flask import Blueprint, current_app as app, flash, render_template, request, url_for

from flask_weasyprint import HTML, render_pdf

from models.db_session import Session
from models.person import Person, get_persons

bp = Blueprint('persons', __name__, url_prefix='/persons')


@bp.add_app_template_filter
def display_newlines(value):
    return value.replace('\n', '<br>')


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
    Session.add(p)
    Session.commit()
    return get_all()


@bp.route('/<int:person_id>', methods=['GET'])
def get(person_id):
    """Get a person by id."""
    return render_template(
        'person_get.html.j2',
        person=Person.get_by_id(person_id).to_dict(),
        tax_year=app.config.get('TAX_YEAR'),
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

    Session.add(p)
    Session.commit()

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
        Session.delete(p)
        Session.commit()
        return get_all()


@bp.route('/data', methods=['GET'])
def get_data():
    """Get all of persons data."""
    return render_template('person_data.html.j2', persons=get_persons())


@bp.route('/<int:person_id>/receipt/<int:year>', methods=['GET'])
def receipt(person_id, year):
    """Get a person's tax receipt by id."""
    p = Person.get_by_id(person_id)
    return render_template(
        'tax_receipt.html.j2',
        org=app.config.get('ORG'),
        treasurer=app.config.get('TREASURER'),
        tax_year=year,
        receipt_number=p.id,
        receipt_date=datetime.now().strftime("%B %e, %Y"),
        name=p.full_name,
        address=p.address,
        amount=sum([t.amount for t in p.transactions if t.date.year == year and not t.receipt]),
    )


@bp.route('/<int:person_id>/receipt/<int:year>/pdf', methods=['GET'])
def receipt_pdf(person_id, year):
    """Get a person's tax receipt by id in PDF form."""
    return render_pdf(url_for('persons.receipt', person_id=person_id, year=year))


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
