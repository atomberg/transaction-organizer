"""API behavior tests for /donors/* routes."""

from datetime import date

from sqlalchemy import select

from app import db
from app.models.family import Family, FamilyMember
from app.models.person import Person
from app.models.tax_receipt import TaxReceipt, TaxReceiptItem
from app.models.transaction import Transaction


def _active_membership(person_id):
    return db.session.execute(
        select(FamilyMember).where(FamilyMember.person_id == person_id, FamilyMember.deleted_at.is_(None))
    ).scalar_one_or_none()


def _create_person(first_name='Jane', last_name='Doe', address='123 Main St'):
    person = Person(
        first_name=first_name,
        last_name=last_name,
        phone='(111) 222-3333',
        email='jane@example.com',
        address=address,
    )
    db.session.add(person)
    db.session.commit()
    return person


def _create_family_for_person(person):
    family = Family(display_name=f'{person.last_name} Household', address=person.address or '', notes='')
    db.session.add(family)
    db.session.flush()
    db.session.add(FamilyMember(family_id=family.id, person_id=person.id))
    db.session.commit()
    return family


def test_donors_index_and_not_found_routes(test_client):
    assert test_client.get('/donors').status_code == 200
    assert test_client.get('/donors/999999').status_code == 404
    assert test_client.get('/donors/999999/edit').status_code == 404
    assert test_client.get('/donors/999999/spouse/add').status_code == 404
    assert test_client.get('/donors/999999/receipts').status_code == 404


def test_create_donor_form_and_submit(test_client, app):
    form_response = test_client.get('/donors/add')
    assert form_response.status_code == 200

    invalid_response = test_client.post('/donors/add', data={'first_name': '', 'last_name': ''}, follow_redirects=True)
    assert invalid_response.status_code == 200
    assert b'First name and last name are required' in invalid_response.data

    create_response = test_client.post(
        '/donors/add',
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
    assert b'Donor created. Family of one was created automatically.' in create_response.data

    with app.app_context():
        person = db.session.execute(select(Person).where(Person.first_name == 'Primary')).scalar_one()
        membership = _active_membership(person.id)
        assert membership is not None
        family = db.session.get(Family, membership.family_id)
        assert family is not None
        assert family.address == '100 Charity Way'


def test_edit_donor_get_and_post(test_client, app):
    with app.app_context():
        donor = _create_person(first_name='Edit', last_name='Target', address='7 Main St')
        _create_family_for_person(donor)
        donor_id = donor.id

    get_response = test_client.get(f'/donors/{donor_id}/edit')
    assert get_response.status_code == 200
    assert b'Save changes' in get_response.data

    post_response = test_client.post(
        f'/donors/{donor_id}/edit',
        data={
            'first_name': 'Edited',
            'last_name': 'Name',
            'email': 'edited@example.com',
            'phone': '555-1234',
        },
        follow_redirects=True,
    )
    assert post_response.status_code == 200
    assert b'Donor details saved.' in post_response.data

    with app.app_context():
        refreshed = db.session.get(Person, donor_id)
        assert refreshed.first_name == 'Edited'
        assert refreshed.last_name == 'Name'
        assert refreshed.email == 'edited@example.com'
        assert refreshed.phone == '555-1234'


def test_family_update_endpoint_updates_shared_address_and_notes(test_client, app):
    with app.app_context():
        donor = _create_person(first_name='Alex', last_name='Shared', address='1 Old St')
        family = _create_family_for_person(donor)
        donor_id = donor.id

        spouse = _create_person(first_name='Jamie', last_name='Shared', address='1 Old St')
        db.session.add(FamilyMember(family_id=family.id, person_id=spouse.id))
        db.session.commit()
        spouse_id = spouse.id

    response = test_client.post(
        f'/donors/{donor_id}/family',
        data={'address': '22 New Shared Ave', 'notes': 'Shared family note'},
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b'Family details updated for all members.' in response.data

    with app.app_context():
        donor_refreshed = db.session.get(Person, donor_id)
        spouse_refreshed = db.session.get(Person, spouse_id)
        membership = _active_membership(donor_id)
        family_refreshed = db.session.get(Family, membership.family_id)
        assert donor_refreshed.address == '22 New Shared Ave'
        assert spouse_refreshed.address == '22 New Shared Ave'
        assert family_refreshed.notes == 'Shared family note'


def test_spouse_add_get_and_post(test_client, app):
    with app.app_context():
        donor = _create_person(first_name='Alex', last_name='House', address='12 Shared Rd')
        _create_family_for_person(donor)
        donor_id = donor.id

    spouse_form = test_client.get(f'/donors/{donor_id}/spouse/add')
    assert spouse_form.status_code == 200
    assert b'readonly' in spouse_form.data

    spouse_create = test_client.post(
        f'/donors/{donor_id}/spouse/add',
        data={
            'first_name': 'Taylor',
            'last_name': 'House',
            'email': 'taylor@example.com',
            'phone': '555-0199',
        },
        follow_redirects=True,
    )
    assert spouse_create.status_code == 200
    assert b'Spouse added to family.' in spouse_create.data

    blocked = test_client.post(
        f'/donors/{donor_id}/spouse/add',
        data={'first_name': 'Third', 'last_name': 'House'},
        follow_redirects=True,
    )
    assert blocked.status_code == 200
    assert b'family already has two members' in blocked.data


def test_remove_member_endpoint_removes_only_target_member(test_client, app):
    with app.app_context():
        donor = _create_person(first_name='Host', last_name='Family')
        family = _create_family_for_person(donor)
        donor_id = donor.id

        spouse = _create_person(first_name='Guest', last_name='Family')
        db.session.add(FamilyMember(family_id=family.id, person_id=spouse.id))
        db.session.commit()
        spouse_id = spouse.id

    response = test_client.post(
        f'/donors/{donor_id}/members/{spouse_id}/remove',
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b'Donor removed.' in response.data

    with app.app_context():
        donor_membership = _active_membership(donor_id)
        spouse_membership = _active_membership(spouse_id)
        spouse_person = db.session.get(Person, spouse_id)
        assert donor_membership is not None
        assert spouse_membership is None
        assert spouse_person.deleted_at is not None


def test_remove_donor_endpoint_blocks_when_transactions_exist(test_client, app):
    with app.app_context():
        donor = _create_person(first_name='Txn', last_name='Blocked')
        _create_family_for_person(donor)
        donor_id = donor.id
        db.session.add(
            Transaction(
                person_id=donor_id,
                date=date(2026, 1, 1),
                method='Cash',
                amount=10.0,
                accepted_by='Treasurer',
            )
        )
        db.session.commit()

    response = test_client.post(f'/donors/{donor_id}/remove', follow_redirects=True)
    assert response.status_code == 200
    assert b'Cannot remove donor with transactions.' in response.data

    with app.app_context():
        still_present = db.session.get(Person, donor_id)
        assert still_present.deleted_at is None


def test_remove_donor_endpoint_removes_family_when_last_member(test_client, app):
    with app.app_context():
        donor = _create_person(first_name='Solo', last_name='Remove')
        family = _create_family_for_person(donor)
        donor_id = donor.id
        family_id = family.id

    response = test_client.post(f'/donors/{donor_id}/remove', follow_redirects=False)
    assert response.status_code == 302
    assert response.headers['Location'].endswith('/donors')

    with app.app_context():
        removed_person = db.session.get(Person, donor_id)
        removed_family = db.session.get(Family, family_id)
        assert removed_person.deleted_at is not None
        assert removed_family.deleted_at is not None


def test_donor_receipts_endpoint_renders(test_client, app):
    with app.app_context():
        donor = _create_person(first_name='Receipt', last_name='Owner')
        _create_family_for_person(donor)
        donor_id = donor.id

    response = test_client.get(f'/donors/{donor_id}/receipts')
    assert response.status_code == 200
    assert b'Receipt history for donor recipient' in response.data


def test_donor_receipt_preview_aggregates_family_transactions(test_client, app):
    with app.app_context():
        primary = _create_person(first_name='Primary', last_name='Receipt', address='5 Shared St')
        family = _create_family_for_person(primary)
        spouse = _create_person(first_name='Spouse', last_name='Receipt', address='5 Shared St')
        db.session.add(FamilyMember(family_id=family.id, person_id=spouse.id))
        db.session.commit()

        db.session.add(
            Transaction(
                person_id=primary.id,
                date=date(2026, 1, 3),
                method='Cash',
                amount=15.0,
                accepted_by='Treasurer',
            )
        )
        db.session.add(
            Transaction(
                person_id=spouse.id,
                date=date(2026, 2, 10),
                method='Cash',
                amount=25.0,
                accepted_by='Treasurer',
            )
        )
        db.session.commit()
        spouse_id = spouse.id

    response = test_client.get(f'/donors/{spouse_id}/receipt/2026')
    assert response.status_code == 200
    assert b'Eligible Amount: 40.00' in response.data


def test_donor_receipt_issue_uses_primary_recipient_and_family_contributors(test_client, app, monkeypatch):
    with app.app_context():
        primary = _create_person(first_name='Primary', last_name='Owner', address='8 Canonical St')
        family = _create_family_for_person(primary)
        spouse = _create_person(first_name='Spouse', last_name='Owner', address='8 Canonical St')
        db.session.add(FamilyMember(family_id=family.id, person_id=spouse.id))
        db.session.commit()

        tx_primary = Transaction(
            person_id=primary.id,
            date=date(2026, 3, 4),
            method='Cash',
            amount=11.0,
            accepted_by='Treasurer',
        )
        tx_spouse = Transaction(
            person_id=spouse.id,
            date=date(2026, 4, 5),
            method='Cash',
            amount=29.0,
            accepted_by='Treasurer',
        )
        db.session.add_all([tx_primary, tx_spouse])
        db.session.commit()
        spouse_id = spouse.id
        primary_id = primary.id
        tx_primary_id = tx_primary.id
        tx_spouse_id = tx_spouse.id

    monkeypatch.setattr(
        'app.blueprints.donor_family.render_pdf',
        lambda _url: app.response_class(b'%PDF-test', mimetype='application/pdf'),
    )
    response = test_client.get(f'/donors/{spouse_id}/receipt/2026/pdf')
    assert response.status_code == 200
    assert response.mimetype == 'application/pdf'

    with app.app_context():
        receipt = db.session.execute(
            select(TaxReceipt).where(TaxReceipt.receipt_type == 'annual_donor')
        ).scalar_one()
        assert receipt.person_id == primary_id
        assert receipt.total_amount == 40.0

        item_tx_ids = {
            item.transaction_id
            for item in db.session.execute(select(TaxReceiptItem)).scalars().all()
        }
        assert tx_primary_id in item_tx_ids
        assert tx_spouse_id in item_tx_ids


def test_donor_receipt_history_is_shared_for_any_family_member_view(test_client, app, monkeypatch):
    with app.app_context():
        primary = _create_person(first_name='Primary', last_name='SharedHistory', address='1 Hist St')
        family = _create_family_for_person(primary)
        spouse = _create_person(first_name='Spouse', last_name='SharedHistory', address='1 Hist St')
        db.session.add(FamilyMember(family_id=family.id, person_id=spouse.id))
        db.session.commit()

        db.session.add(
            Transaction(
                person_id=spouse.id,
                date=date(2026, 6, 1),
                method='Cash',
                amount=50.0,
                accepted_by='Treasurer',
            )
        )
        db.session.commit()
        spouse_id = spouse.id
        primary_id = primary.id

    monkeypatch.setattr(
        'app.blueprints.donor_family.render_pdf',
        lambda _url: app.response_class(b'%PDF-test', mimetype='application/pdf'),
    )
    test_client.get(f'/donors/{primary_id}/receipt/2026/pdf')

    primary_history = test_client.get(f'/donors/{primary_id}/receipts')
    spouse_history = test_client.get(f'/donors/{spouse_id}/receipts')
    assert primary_history.status_code == 200
    assert spouse_history.status_code == 200
    assert b'annual_donor' in primary_history.data
    assert b'annual_donor' in spouse_history.data
