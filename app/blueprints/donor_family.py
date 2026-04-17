"""Donor-first UI routes.

This pass keeps legacy person workflow for compatibility while introducing a
family-of-max-two workflow for donor management.
"""

from datetime import datetime

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask import current_app as app

from app import db
from app.models.family import Family, FamilyMember
from app.models.person import Person, get_persons
from app.models.tax_receipt import get_receipts_for_person

bp = Blueprint('donor_family', __name__)


def _active_membership_for_person(person_id):
    return (
        FamilyMember.query.filter(
            FamilyMember.person_id == person_id,
            FamilyMember.deleted_at.is_(None),
        )
        .order_by(FamilyMember.created_at.desc())
        .first()
    )


def _active_family_for_person(person_id):
    membership = _active_membership_for_person(person_id)
    if membership is None:
        return None
    family = Family.get_by_id(membership.family_id)
    if family is None or family.deleted_at is not None:
        return None
    return family


def _active_family_members(family_id):
    return (
        FamilyMember.query.filter(
            FamilyMember.family_id == family_id,
            FamilyMember.deleted_at.is_(None),
        )
        .order_by(FamilyMember.created_at.asc(), FamilyMember.id.asc())
        .all()
    )


def _sync_member_addresses(family):
    members = _active_family_members(family.id)
    for member in members:
        person = Person.get_by_id(member.person_id)
        if person is None:
            continue
        person.address = family.address
        person.updated_at = datetime.now()
        db.session.add(person)


def _default_family_name(person):
    return f'{person.last_name} Household'


def _ensure_family_for_person(person):
    family = _active_family_for_person(person.id)
    if family is not None:
        return family

    family = Family(
        display_name=_default_family_name(person),
        address=person.address or '',
        notes=person.notes or '',
    )
    db.session.add(family)
    db.session.flush()

    db.session.add(FamilyMember(family_id=family.id, person_id=person.id))
    db.session.commit()
    return family


def _donor_rows(query_text=''):
    rows = []
    q = (query_text or '').strip().lower()
    tax_year = int(app.config.get('TAX_YEAR') or datetime.now().year)
    for person in get_persons():
        family = _active_family_for_person(person.id)
        donation_total = sum(
            transaction.amount
            for transaction in person.transactions
            if transaction.date.year == tax_year
        )
        row = {
            'person_id': person.id,
            'first_name': person.first_name,
            'last_name': person.last_name,
            'email': person.email or '',
            'phone': person.phone or '',
            'family_id': family.id if family else None,
            'donation_total': donation_total,
        }
        haystack = f"{row['last_name']} {row['first_name']} {row['email']} {row['phone']}".lower()
        if q and q not in haystack:
            continue
        rows.append(row)
    return rows


def _family_view_model(family):
    memberships = _active_family_members(family.id)
    members = []
    primary_membership_id = memberships[0].id if memberships else None
    for membership in memberships:
        person = Person.get_by_id(membership.person_id)
        if person is None:
            continue
        members.append(
            {
                'person_id': person.id,
                'full_name': person.full_name,
                'email': person.email or '',
                'phone': person.phone or '',
                'is_primary': membership.id == primary_membership_id,
            }
        )
    return {
        'id': family.id,
        'display_name': family.display_name,
        'address': family.address or '',
        'notes': family.notes or '',
        'member_count': len(members),
        'members': members,
        'last_modified': family.updated_at.strftime('%c'),
        'created_at': family.created_at.strftime('%c'),
    }


@bp.route('/')
def home():
    return redirect(url_for('donor_family.donors'))


@bp.route('/donors', methods=['GET'])
def donors():
    query_text = request.args.get('q', '')
    tax_year = int(app.config.get('TAX_YEAR') or datetime.now().year)
    return render_template(
        'donor_table.html.j2',
        donors=_donor_rows(query_text=query_text),
        query_text=query_text,
        tax_year=tax_year,
    )


@bp.route('/donors/add', methods=['GET'])
def donor_add_form():
    return render_template('donor_add.html.j2')


@bp.route('/donors/add', methods=['POST'])
def donor_create():
    first_name = request.values.get('first_name', '').strip()
    last_name = request.values.get('last_name', '').strip()
    if not first_name or not last_name:
        flash('First name and last name are required.')
        return redirect(url_for('donor_family.donor_add_form'))

    person = Person(
        first_name=first_name,
        last_name=last_name,
        phone=request.values.get('phone', '').strip(),
        email=request.values.get('email', '').strip(),
        address=request.values.get('address', '').strip(),
    )
    db.session.add(person)
    db.session.flush()

    family = Family(
        display_name=_default_family_name(person),
        address=person.address or '',
        notes='',
    )
    db.session.add(family)
    db.session.flush()

    db.session.add(FamilyMember(family_id=family.id, person_id=person.id))
    db.session.commit()

    flash('Donor created. Family of one was created automatically.')
    return redirect(url_for('donor_family.donor_get', donor_id=person.id))


@bp.route('/donors/<int:donor_id>', methods=['GET'])
def donor_get(donor_id):
    person = Person.get_by_id(donor_id)
    if person is None:
        return ('Donor not found', 404)

    family = _ensure_family_for_person(person)
    selected_year = int(request.values.get('year', app.config.get('TAX_YEAR')))

    return render_template(
        'donor_get.html.j2',
        donor={
            'id': person.id,
            'full_name': person.full_name,
            'email': person.email or '',
            'phone': person.phone or '',
        },
        family=_family_view_model(family),
        tax_year=selected_year,
    )


@bp.route('/donors/<int:donor_id>/edit', methods=['GET'])
def donor_edit(donor_id):
    person = Person.get_by_id(donor_id)
    if person is None:
        return ('Donor not found', 404)

    family = _ensure_family_for_person(person)
    return render_template(
        'donor_edit.html.j2',
        donor={
            'id': person.id,
            'first_name': person.first_name,
            'last_name': person.last_name,
            'full_name': person.full_name,
            'email': person.email or '',
            'phone': person.phone or '',
            'last_modified': person.updated_at.strftime('%c'),
            'created_at': person.created_at.strftime('%c'),
        },
    )


@bp.route('/donors/<int:donor_id>/edit', methods=['POST'])
def donor_update(donor_id):
    person = Person.get_by_id(donor_id)
    if person is None:
        return ('Donor not found', 404)

    family = _ensure_family_for_person(person)

    person.first_name = request.values.get('first_name', '').strip()
    person.last_name = request.values.get('last_name', '').strip()
    person.email = request.values.get('email', '').strip()
    person.phone = request.values.get('phone', '').strip()
    person.updated_at = datetime.now()
    db.session.add(person)

    address_updated = False
    if 'address' in request.values:
        family.address = request.values.get('address', '').strip()
        address_updated = True
    if 'notes' in request.values:
        family.notes = request.values.get('notes', '').strip()
    family.updated_at = datetime.now()
    db.session.add(family)
    if address_updated:
        _sync_member_addresses(family)

    db.session.commit()
    flash('Donor details saved.')
    return redirect(url_for('donor_family.donor_get', donor_id=donor_id))


def _soft_remove_person(person_id):
    person = Person.get_by_id(person_id)
    if person is None:
        return 'missing'
    if person.transactions:
        return 'has_transactions'

    membership = _active_membership_for_person(person_id)
    family = Family.get_by_id(membership.family_id) if membership else None

    if membership is not None:
        membership.deleted_at = datetime.now()
        membership.updated_at = datetime.now()
        db.session.add(membership)

    person.deleted_at = datetime.now()
    person.updated_at = datetime.now()
    db.session.add(person)

    if family is not None:
        active_remaining = _active_family_members(family.id)
        if len(active_remaining) == 0:
            family.deleted_at = datetime.now()
            family.updated_at = datetime.now()
            db.session.add(family)

    db.session.commit()
    return 'removed'


@bp.route('/donors/<int:donor_id>/remove', methods=['POST'])
def remove_donor(donor_id):
    status = _soft_remove_person(donor_id)
    if status == 'missing':
        return ('Donor not found', 404)
    if status == 'has_transactions':
        flash('Cannot remove donor with transactions. Use person compatibility workflow if needed.')
        return redirect(url_for('donor_family.donor_get', donor_id=donor_id))
    flash('Donor removed.')
    return redirect(url_for('donor_family.donors'))


@bp.route('/donors/<int:donor_id>/members/<int:person_id>/remove', methods=['POST'])
def remove_donor_member(donor_id, person_id):
    family = _active_family_for_person(donor_id)
    if family is None:
        return ('Donor not found', 404)

    if not any(member.person_id == person_id for member in _active_family_members(family.id)):
        return ('Family member not found', 404)

    status = _soft_remove_person(person_id)
    if status == 'missing':
        return ('Donor not found', 404)
    if status == 'has_transactions':
        flash('Cannot remove donor with transactions. Use person compatibility workflow if needed.')
        return redirect(url_for('donor_family.donor_get', donor_id=donor_id))

    flash('Donor removed.')

    if person_id != donor_id:
        return redirect(url_for('donor_family.donor_get', donor_id=donor_id))

    refreshed_family = _active_family_for_person(donor_id)
    if refreshed_family is None:
        return redirect(url_for('donor_family.donors'))
    remaining = _active_family_members(refreshed_family.id)
    if not remaining:
        return redirect(url_for('donor_family.donors'))
    return redirect(url_for('donor_family.donor_get', donor_id=remaining[0].person_id))


@bp.route('/donors/<int:donor_id>/family', methods=['POST'])
def donor_update_family_address(donor_id):
    person = Person.get_by_id(donor_id)
    if person is None:
        return ('Donor not found', 404)

    family = _ensure_family_for_person(person)
    family.address = request.values.get('address', '').strip()
    family.notes = request.values.get('notes', '').strip()
    family.updated_at = datetime.now()
    db.session.add(family)
    _sync_member_addresses(family)
    db.session.commit()

    flash('Family details updated for all members.')
    return redirect(url_for('donor_family.donor_get', donor_id=donor_id))


@bp.route('/donors/<int:donor_id>/spouse/add', methods=['GET'])
def add_spouse_form(donor_id):
    person = Person.get_by_id(donor_id)
    if person is None:
        return ('Donor not found', 404)

    family = _ensure_family_for_person(person)
    family_view = _family_view_model(family)
    if family_view['member_count'] >= 2:
        flash('This family already has two members.')
        return redirect(url_for('donor_family.donor_get', donor_id=donor_id))

    return render_template(
        'spouse_add.html.j2',
        donor={
            'id': person.id,
            'full_name': person.full_name,
        },
        family=family_view,
        default_last_name=person.last_name,
        shared_address=family.address or '',
    )


@bp.route('/donors/<int:donor_id>/spouse/add', methods=['POST'])
def add_spouse(donor_id):
    person = Person.get_by_id(donor_id)
    if person is None:
        return ('Donor not found', 404)

    family = _ensure_family_for_person(person)
    if len(_active_family_members(family.id)) >= 2:
        flash('Cannot add spouse: family already has two members.')
        return redirect(url_for('donor_family.donor_get', donor_id=donor_id))

    first_name = request.values.get('first_name', '').strip()
    last_name = request.values.get('last_name', '').strip()
    if not first_name or not last_name:
        flash('Spouse first name and last name are required.')
        return redirect(url_for('donor_family.add_spouse_form', donor_id=donor_id))

    spouse = Person(
        first_name=first_name,
        last_name=last_name,
        phone=request.values.get('phone', '').strip(),
        email=request.values.get('email', '').strip(),
        address=family.address or '',
    )
    db.session.add(spouse)
    db.session.flush()

    db.session.add(FamilyMember(family_id=family.id, person_id=spouse.id))
    db.session.commit()

    flash('Spouse added to family.')
    return redirect(url_for('donor_family.donor_get', donor_id=spouse.id))


@bp.route('/donors/<int:donor_id>/receipts', methods=['GET'])
def donor_receipt_history(donor_id):
    person = Person.get_by_id(donor_id)
    if person is None:
        return ('Donor not found', 404)

    selected_year = request.values.get('year')
    tax_year = int(selected_year) if selected_year else None
    receipts = get_receipts_for_person(person.id, tax_year=tax_year)

    return render_template(
        'donor_receipts.html.j2',
        donor={
            'id': person.id,
            'display_name': person.full_name,
            'mailing_address': person.address or '',
            'legacy_person_id': person.id,
        },
        receipts=receipts,
        selected_year=selected_year or '',
    )
