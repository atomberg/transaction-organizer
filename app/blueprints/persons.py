from datetime import datetime
from flask import Blueprint, request, render_template, flash, current_app as app
from models.db_session import Session
from models.person import Person, get_persons

bp = Blueprint('persons', __name__, url_prefix='/persons')


@bp.add_app_template_filter
def display_newlines(value):
    return value.replace('\n', '<br>')


@bp.route('/', methods=['GET'])
def get_all():
    """Display all persons in a table."""
    return render_template('person_table.html.j2', persons=get_persons())


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
        tax_year=app.config.get('TAX_YEAR')
    )


@bp.route('/<int:person_id>/edit', methods=['GET'])
def edit(person_id):
    """Edit a person by id."""
    return render_template(
        'person_edit.html.j2',
        person=Person.get_by_id(person_id).to_dict()
    )


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
        amount=sum([t.amount for t in p.transactions if t.date.year == year])
    )
