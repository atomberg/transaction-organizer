"""Integration tests for person and transaction routes."""

from datetime import date

from sqlalchemy import select

from app import db
from app.models.person import Person
from app.models.tax_receipt import TaxReceipt, TaxReceiptItem
from app.models.transaction import Transaction


def create_person(first_name='Jane', last_name='Doe'):
    person = Person(
        first_name=first_name,
        last_name=last_name,
        phone='(111) 222-3333',
        email='jane@example.com',
        address='123 Main St',
    )
    db.session.add(person)
    db.session.commit()
    return person


def create_transaction(person_id, amount=20.0, day=date(2024, 1, 1), receipt=False):
    transaction = Transaction(
        person_id=person_id,
        date=day,
        method='Cash',
        amount=amount,
        accepted_by='Treasurer',
        memo='Membership',
    )
    transaction.receipt = receipt
    db.session.add(transaction)
    db.session.commit()
    return transaction


def test_person_add_route(test_client, app):
    response = test_client.post(
        '/persons/',
        data={
            'first_name': 'Mary',
            'last_name': 'Smith',
            'phone': '555-0100',
            'email': 'mary@charity.org',
            'address': '100 Charity Way',
        },
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b'Mary' in response.data
    assert b'Smith' in response.data

    with app.app_context():
        people = db.session.execute(select(Person)).scalars().all()
        assert len(people) == 1
        assert people[0].email == 'mary@charity.org'


def test_person_update_route(test_client, app):
    with app.app_context():
        person = create_person()
        person_id = person.id

    response = test_client.post(
        f'/persons/{person_id}',
        data={
            'first_name': 'Janet',
            'last_name': 'Doe',
            'phone': '555-0101',
            'email': 'janet@example.com',
            'address': '456 Updated Ave',
            'notes': 'Paid membership',
        },
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b'Janet' in response.data

    with app.app_context():
        updated = db.session.get(Person, person_id)
        assert updated is not None
        assert updated.first_name == 'Janet'
        assert updated.notes == 'Paid membership'


def test_person_delete_blocked_when_transactions_exist(test_client, app):
    with app.app_context():
        person = create_person(first_name='Alex', last_name='Member')
        person_id = person.id
        create_transaction(person_id)

    response = test_client.get(f'/persons/{person_id}/delete', follow_redirects=True)
    assert response.status_code == 200
    assert b'Cannot delete a person with transactions' in response.data

    with app.app_context():
        assert db.session.get(Person, person_id) is not None


def test_person_delete_route(test_client, app):
    with app.app_context():
        person = create_person(first_name='Delete', last_name='Me')
        person_id = person.id

    response = test_client.get(f'/persons/{person_id}/delete', follow_redirects=True)
    assert response.status_code == 200

    with app.app_context():
        assert db.session.get(Person, person_id) is None


def test_transaction_add_route(test_client, app):
    with app.app_context():
        person = create_person(first_name='Donor', last_name='One')
        person_id = person.id

    response = test_client.post(
        '/transactions/',
        data={
            'person_id': str(person_id),
            'day': '2024-02-15',
            'method': 'Credit',
            'amount': '55.25',
            'accepted_by': 'Treasurer',
            'memo': 'AGM membership',
        },
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b'Latest transactions' in response.data
    assert b'55.25' in response.data

    with app.app_context():
        transactions = db.session.execute(select(Transaction)).scalars().all()
        assert len(transactions) == 1
        assert transactions[0].method == 'Credit'
        assert transactions[0].amount == 55.25


def test_transaction_update_and_delete_routes(test_client, app):
    with app.app_context():
        person = create_person(first_name='Update', last_name='Txn')
        person_id = person.id
        transaction = create_transaction(person_id, amount=30.0)
        transaction_id = transaction.id

    update_response = test_client.post(
        f'/transactions/{transaction_id}',
        data={
            'person_id': str(person_id),
            'day': '2024-03-01',
            'method': 'Cheque',
            'amount': '40.00',
            'accepted_by': 'Assistant',
            'memo': 'Updated memo',
            'receipt_issued': 'True',
        },
        follow_redirects=True,
    )
    assert update_response.status_code == 200
    assert b'40.0' in update_response.data or b'40.00' in update_response.data

    with app.app_context():
        updated = db.session.get(Transaction, transaction_id)
        assert updated is not None
        assert updated.method == 'Cheque'
        assert updated.receipt is True

    delete_response = test_client.get(f'/transactions/{transaction_id}/delete', follow_redirects=True)
    assert delete_response.status_code == 200

    with app.app_context():
        assert db.session.get(Transaction, transaction_id) is None


def test_person_receipt_route_filters_year_and_issued_receipts(test_client, app):
    with app.app_context():
        person = create_person(first_name='Receipt', last_name='Member')
        person_id = person.id
        create_transaction(person_id, amount=20.0, day=date(2024, 1, 15), receipt=False)
        create_transaction(person_id, amount=5.0, day=date(2024, 2, 1), receipt=True)
        create_transaction(person_id, amount=7.0, day=date(2023, 12, 31), receipt=False)

    response = test_client.get(f'/persons/{person_id}/receipt/2024')
    assert response.status_code == 200
    assert b'Tax year:</strong> 2024' in response.data
    assert b'Eligible Amount: 20.00' in response.data
    assert b'Member, Receipt' in response.data


def test_transaction_receipt_route_renders_receipt_content(test_client, app):
    with app.app_context():
        person = create_person(first_name='Txn', last_name='Receipt')
        person_id = person.id
        transaction = create_transaction(person_id, amount=42.5, day=date(2024, 5, 1), receipt=False)
        transaction_id = transaction.id

    response = test_client.get(f'/transactions/{transaction_id}/receipt')
    assert response.status_code == 200
    assert b'Tax year:</strong> 2024' in response.data
    assert b'Eligible Amount: 42.50' in response.data
    assert f'Receipt #</strong> {person_id}-{transaction_id}'.encode() in response.data


def test_person_receipt_pdf_route_returns_pdf_response(test_client, app, monkeypatch):
    with app.app_context():
        person = create_person(first_name='Pdf', last_name='Donor')
        person_id = person.id
        create_transaction(person_id, amount=35.0, day=date(2024, 6, 1), receipt=False)

    called = {}

    def fake_render_pdf(url):
        called['url'] = url
        return app.response_class(b'%PDF-test', mimetype='application/pdf')

    monkeypatch.setattr('app.blueprints.persons.render_pdf', fake_render_pdf)

    response = test_client.get(f'/persons/{person_id}/receipt/2024/pdf')
    assert response.status_code == 200
    assert response.mimetype == 'application/pdf'
    assert b'%PDF-test' in response.data
    assert '/persons/receipts/' in called['url']

    with app.app_context():
        receipt_rows = db.session.execute(select(TaxReceipt)).scalars().all()
        assert len(receipt_rows) == 1
        assert receipt_rows[0].receipt_type == 'annual_person'
        assert receipt_rows[0].tax_year == 2024
        assert receipt_rows[0].person_id == person_id

        txns = db.session.execute(select(Transaction)).scalars().all()
        assert txns[0].receipt is True

        receipt_items = db.session.execute(select(TaxReceiptItem)).scalars().all()
        assert len(receipt_items) == 1


def test_transaction_receipt_pdf_marks_transaction_as_receipted(test_client, app, monkeypatch):
    with app.app_context():
        person = create_person(first_name='Single', last_name='Receipt')
        transaction = create_transaction(person.id, amount=11.0, day=date(2024, 7, 4), receipt=False)
        transaction_id = transaction.id

    called = {}

    def fake_render_pdf(url):
        called['url'] = url
        return app.response_class(b'%PDF-test', mimetype='application/pdf')

    monkeypatch.setattr('app.blueprints.transactions.render_pdf', fake_render_pdf)

    response = test_client.get(f'/transactions/{transaction_id}/receipt/pdf')
    assert response.status_code == 200
    assert response.mimetype == 'application/pdf'
    assert b'%PDF-test' in response.data
    assert '/persons/receipts/' in called['url']

    with app.app_context():
        updated = db.session.get(Transaction, transaction_id)
        assert updated.receipt is True
        receipt_item = db.session.execute(
            select(TaxReceiptItem).where(TaxReceiptItem.transaction_id == transaction_id)
        ).scalar_one()
        assert receipt_item.amount == 11.0


def test_receipt_history_route_lists_issued_receipts(test_client, app, monkeypatch):
    with app.app_context():
        person = create_person(first_name='History', last_name='Donor')
        person_id = person.id
        create_transaction(person_id, amount=19.0, day=date(2024, 1, 10), receipt=False)

    monkeypatch.setattr(
        'app.blueprints.persons.render_pdf',
        lambda _url: app.response_class(b'%PDF-test', mimetype='application/pdf'),
    )
    test_client.get(f'/persons/{person_id}/receipt/2024/pdf')

    response = test_client.get(f'/persons/{person_id}/receipts')
    assert response.status_code == 200
    assert b'Receipt history for Donor, History' in response.data
    assert b'annual_person' in response.data
    assert b'Download PDF' in response.data


def test_person_receipt_routes_return_404_when_person_missing(test_client):
    assert test_client.get('/persons/999999/receipt/2024').status_code == 404
    assert test_client.get('/persons/999999/receipt/2024/pdf').status_code == 404
    assert test_client.get('/persons/999999/receipts').status_code == 404


def test_person_receipt_pdf_with_no_eligible_transactions_redirects(test_client, app):
    with app.app_context():
        person = create_person(first_name='No', last_name='Transactions')
        person_id = person.id

    response = test_client.get(f'/persons/{person_id}/receipt/2024/pdf', follow_redirects=True)
    assert response.status_code == 200
    assert b'No eligible transactions found for this person and tax year.' in response.data


def test_transaction_receipt_pdf_returns_404_when_transaction_missing(test_client):
    response = test_client.get('/transactions/999999/receipt/pdf')
    assert response.status_code == 404


def test_receipt_template_uses_configurable_signature_url(test_client, app):
    with app.app_context():
        app.config['SIGNATURE_IMAGE_URL'] = '/static/custom-signature.png'
        person = create_person(first_name='Sign', last_name='Config')
        person_id = person.id
        create_transaction(person_id, amount=17.0, day=date(2024, 10, 10), receipt=False)

    response = test_client.get(f'/persons/{person_id}/receipt/2024')
    assert response.status_code == 200
    assert b'/static/custom-signature.png' in response.data
