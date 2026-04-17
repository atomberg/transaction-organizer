"""Integration tests for transaction routes and receipt issuance."""

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
        memo='Membership',
    )
    transaction.receipt = receipt
    db.session.add(transaction)
    db.session.commit()
    return transaction


def test_person_routes_removed(test_client):
    assert test_client.get('/persons/').status_code == 404
    assert test_client.get('/persons/1').status_code == 404


def test_transaction_add_requires_donor_id(test_client):
    response = test_client.post(
        '/transactions/',
        data={
            'day': '2024-02-15',
            'method': 'Credit',
            'amount': '55.25',
            'memo': 'AGM membership',
        },
    )
    assert response.status_code == 400
    assert b'donor_id is required' in response.data


def test_transaction_add_route(test_client, app):
    with app.app_context():
        person = create_person(first_name='Donor', last_name='One')
        person_id = person.id

    response = test_client.post(
        '/transactions/',
        data={
            'donor_id': str(person_id),
            'day': '2024-02-15',
            'method': 'Credit',
            'amount': '55.25',
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
            'donor_id': str(person_id),
            'day': '2024-03-01',
            'method': 'Cheque',
            'amount': '40.00',
            'memo': 'Updated memo',
        },
        follow_redirects=True,
    )
    assert update_response.status_code == 200
    assert b'40.0' in update_response.data or b'40.00' in update_response.data

    with app.app_context():
        updated = db.session.get(Transaction, transaction_id)
        assert updated is not None
        assert updated.method == 'Cheque'
        assert updated.receipt_issued is False

    delete_response = test_client.get(f'/transactions/{transaction_id}/delete', follow_redirects=True)
    assert delete_response.status_code == 200

    with app.app_context():
        assert db.session.get(Transaction, transaction_id) is None


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
    assert f'Receipt #</strong> {person_id}-{transaction_id}-1'.encode() in response.data


def test_transaction_receipt_pdf_marks_transaction_as_receipted(test_client, app, monkeypatch):
    with app.app_context():
        person = create_person(first_name='Single', last_name='Receipt')
        transaction = create_transaction(person.id, amount=11.0, day=date(2024, 7, 4), receipt=False)
        transaction_id = transaction.id
        person_id = person.id

    called = {}

    def fake_render_pdf(url):
        called['url'] = url
        return app.response_class(b'%PDF-test', mimetype='application/pdf')

    monkeypatch.setattr('app.blueprints.transactions.render_pdf', fake_render_pdf)

    response = test_client.get(f'/transactions/{transaction_id}/receipt/pdf')
    assert response.status_code == 200
    assert response.mimetype == 'application/pdf'
    assert b'%PDF-test' in response.data
    assert '/donors/receipts/' in called['url']

    with app.app_context():
        updated = db.session.get(Transaction, transaction_id)
        assert updated.receipt is True

        receipt_row = db.session.execute(select(TaxReceipt)).scalar_one()
        assert receipt_row.person_id == person_id
        assert receipt_row.donor_id == person_id

        receipt_item = db.session.execute(
            select(TaxReceiptItem).where(TaxReceiptItem.transaction_id == transaction_id)
        ).scalar_one()
        assert receipt_item.amount == 11.0


def test_transaction_receipt_pdf_returns_404_when_transaction_missing(test_client):
    response = test_client.get('/transactions/999999/receipt/pdf')
    assert response.status_code == 404
