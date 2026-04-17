"""Pass 1 donor UI contract tests."""

from sqlalchemy import select

from app import db
from app.models.family import Family, FamilyMember
from app.models.person import Person


def _create_person(first_name='Jane', last_name='Doe', address='123 Main St', phone='(111) 222-3333'):
    person = Person(
        first_name=first_name,
        last_name=last_name,
        phone=phone,
        email='jane@example.com',
        address=address,
    )
    db.session.add(person)
    db.session.commit()
    return person


def test_root_redirects_to_donor_workflow(test_client):
    response = test_client.get('/', follow_redirects=False)
    assert response.status_code == 302
    assert response.headers['Location'].endswith('/donors')


def test_menu_driven_donor_creation_creates_family_of_one(test_client, app):
    form_response = test_client.get('/donors/form')
    assert form_response.status_code == 200
    assert b'Creating a donor automatically creates a family of one' in form_response.data
    assert b'Last name' in form_response.data
    assert b'First name' in form_response.data

    create_response = test_client.post(
        '/donors',
        data={
            'first_name': 'Primary',
            'last_name': 'Donor',
            'email': 'primary@example.com',
            'phone': '555-0100',
            'address': '100 Charity Way',
        },
        follow_redirects=True,
    )
    assert create_response.status_code == 200
    assert b'Family #1' in create_response.data
    assert b'Add donor' in create_response.data
    assert b'Back' in create_response.data

    with app.app_context():
        person = db.session.execute(select(Person).where(Person.first_name == 'Primary')).scalar_one()
        membership = db.session.execute(
            select(FamilyMember).where(FamilyMember.person_id == person.id, FamilyMember.deleted_at.is_(None))
        ).scalar_one()
        family = db.session.get(Family, membership.family_id)
        assert family is not None
        assert family.address == '100 Charity Way'


def test_add_spouse_limited_to_two_members_and_shared_family_view(test_client, app):
    with app.app_context():
        donor = _create_person(first_name='Alex', last_name='House', address='12 Shared Rd')
        family = Family(display_name='House Household', address='12 Shared Rd')
        db.session.add(family)
        db.session.flush()
        db.session.add(FamilyMember(family_id=family.id, person_id=donor.id))
        db.session.commit()
        donor_id = donor.id

    spouse_form = test_client.get(f'/donors/{donor_id}/spouse/add')
    assert spouse_form.status_code == 200
    assert b'readonly' in spouse_form.data

    spouse_create = test_client.post(
        f'/donors/{donor_id}/spouse',
        data={
            'first_name': 'Taylor',
            'last_name': 'House',
            'email': 'taylor@example.com',
            'phone': '555-0199',
        },
        follow_redirects=True,
    )
    assert spouse_create.status_code == 200
    assert b'Spouse added to family' in spouse_create.data

    with app.app_context():
        spouse = db.session.execute(select(Person).where(Person.first_name == 'Taylor')).scalar_one()
        spouse_membership = db.session.execute(
            select(FamilyMember).where(FamilyMember.person_id == spouse.id, FamilyMember.deleted_at.is_(None))
        ).scalar_one()
        donor_membership = db.session.execute(
            select(FamilyMember).where(FamilyMember.person_id == donor_id, FamilyMember.deleted_at.is_(None))
        ).scalar_one()
        assert spouse_membership.family_id == donor_membership.family_id
        assert spouse.address == '12 Shared Rd'

    # Third member should be blocked.
    blocked = test_client.post(
        f'/donors/{donor_id}/spouse',
        data={'first_name': 'Third', 'last_name': 'House'},
        follow_redirects=True,
    )
    assert blocked.status_code == 200
    assert b'family already has two members' in blocked.data


def test_clicking_either_spouse_opens_same_family_view(test_client, app):
    with app.app_context():
        donor = _create_person(first_name='Jordan', last_name='Same', address='9 Unity St')
        spouse = _create_person(first_name='Jamie', last_name='Same', address='9 Unity St')
        family = Family(display_name='Same Household', address='9 Unity St')
        db.session.add(family)
        db.session.flush()
        db.session.add(FamilyMember(family_id=family.id, person_id=donor.id))
        db.session.add(FamilyMember(family_id=family.id, person_id=spouse.id))
        db.session.commit()
        donor_id = donor.id
        spouse_id = spouse.id

    donor_view = test_client.get(f'/donors/{donor_id}')
    spouse_view = test_client.get(f'/donors/{spouse_id}')
    assert donor_view.status_code == 200
    assert spouse_view.status_code == 200
    assert b'Family #1' in donor_view.data
    assert b'Family #1' in spouse_view.data
    assert b'Jordan' in donor_view.data and b'Jamie' in donor_view.data
    assert b'Jordan' in spouse_view.data and b'Jamie' in spouse_view.data
    assert donor_view.data.count(b'Yes') == 1
    assert donor_view.data.count(b'No') >= 1
    assert b'Open same family' not in donor_view.data
    assert b'Person compatibility view' not in donor_view.data
    assert b'Add donor' in donor_view.data
    assert b'Remove' in donor_view.data
    assert b'Back' in donor_view.data
    assert b'Edit' in donor_view.data
    assert b'Notes' in donor_view.data
    assert b'Last modified' in donor_view.data
    assert b'Created on' in donor_view.data
    assert b'Preview' in donor_view.data
    assert b'Issue/PDF' in donor_view.data
    assert f'/donors/{donor_id}/edit'.encode() in donor_view.data
    assert f'/donors/{spouse_id}/edit'.encode() in donor_view.data


def test_donor_edit_page_exists_and_is_link_target(test_client, app):
    with app.app_context():
        donor = _create_person(first_name='Edit', last_name='Target', address='77 Edit St')
        family = Family(display_name='Target Household', address='77 Edit St')
        db.session.add(family)
        db.session.flush()
        db.session.add(FamilyMember(family_id=family.id, person_id=donor.id))
        db.session.commit()
        donor_id = donor.id

    donor_view = test_client.get(f'/donors/{donor_id}')
    assert donor_view.status_code == 200
    assert f'/donors/{donor_id}/edit'.encode() in donor_view.data

    edit_page = test_client.get(f'/donors/{donor_id}/edit')
    assert edit_page.status_code == 200
    assert b'Save changes' in edit_page.data


def test_person_list_kept_for_compatibility(test_client, app):
    with app.app_context():
        _create_person(first_name='Compat', last_name='Person')

    response = test_client.get('/persons/')
    assert response.status_code == 200
    assert b'All people (compatibility view)' in response.data


def test_donor_list_has_split_name_and_current_year_donations_column(test_client, app):
    with app.app_context():
        app.config['TAX_YEAR'] = 2026
        _create_person(first_name='Filter', last_name='Target', address='10 First St', phone='1234567890')

    response = test_client.get('/donors')
    assert response.status_code == 200
    assert b'Last name' in response.data
    assert b'First name' in response.data
    assert b'Donations 2026' in response.data
    assert b'Shared Family Address' not in response.data
    assert b'Family Size' not in response.data
    assert b'View' in response.data
    assert b'Person compatibility view' not in response.data
    assert b'(123) 456-7890' in response.data
