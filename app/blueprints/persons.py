from datetime import date, datetime
from flask import Blueprint, request, render_template
from models.db_session import Session
from models.person import Person, get_persons_table


bp = Blueprint('persons', __name__, url_prefix='/persons')


@bp.route('/', methods=['GET'])
def get_all():
    """Get all persons."""
    return render_template(
        'person_table.html.j2',
        today=date.today().strftime('%Y-%m-%d'),
        # suppliers=get_suppliers(),
        # categories=get_categories(),
        table_rows=get_persons_table(3, False)
    )


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
    # import pdb
    # pdb.set_trace()
    return render_template(
        'person_get.html.j2',
        person=Person.get_by_id(person_id).to_dict()
    )


@bp.route('/<int:person_id>/edit', methods=['GET'])
def edit(person_id):
    """Get a person by id."""
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
@bp.route('/<int:person_id>/delete', methods=['POST'])
def delete(person_id):
    """Delete a persons by id."""
    p = Person.get_by_id(person_id)
    p.deleted_at = datetime.now()
    Session.add(p)
    Session.commit()
    return get_all()
