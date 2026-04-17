"""Routes for managing donations and transaction records."""

from datetime import date, datetime
from pathlib import Path

from flask import Blueprint, render_template, request, url_for
from flask import current_app as app
from flask_weasyprint import render_pdf

from app import db
from app.models.person import Person, get_donor_names
from app.models.tax_receipt import (
    issue_single_transaction_receipt,
    next_single_transaction_receipt_number,
)
from app.models.transaction import Transaction, get_transactions

bp = Blueprint('transactions', __name__, url_prefix='/transactions')


@bp.add_app_template_filter
def currency_format(value):
    return f'{value:.2f}'


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


@bp.route('/', methods=['GET'])
def get_all():
    """Display all transactions in a table."""
    begin = request.values.get('begin')
    end = request.values.get('end')
    return render_template(
        'transaction_table.html.j2',
        begin=begin,
        end=end,
        transactions=get_transactions(
            begin=datetime.strptime(begin, '%Y-%m-%d').date() if begin else None,
            end=datetime.strptime(end, '%Y-%m-%d').date() if end else None,
        ),
    )


@bp.route('/latest', methods=['GET'])
def get_latest():
    """Get the latest transactions and render a transaction input form."""
    limit = request.values.get('limit', 5)
    return render_template(
        'transaction_add.html.j2',
        today=date.today().strftime('%Y-%m-%d'),
        donors=get_donor_names(),
        transactions=get_transactions(lim=limit, reverse=True),
    )


@bp.route('/', methods=['POST'])
def add():
    """Add a new transaction."""
    donor_id = request.values.get('donor_id') or request.values.get('person_id')
    db.session.add(
        Transaction(
            person_id=donor_id,
            date=datetime.strptime(request.values['day'], '%Y-%m-%d').date(),
            method=request.values['method'],
            amount=float(request.values['amount']),
            memo=request.values['memo'],
        )
    )
    db.session.commit()
    return get_latest()


@bp.route('/<int:transaction_id>', methods=['GET'])
def get(transaction_id):
    """Get a transation by id."""
    transaction = Transaction.get_by_id(transaction_id)
    if transaction is None:
        return ('Transaction not found', 404)
    return render_template(
        'transaction_edit.html.j2', transaction=transaction.to_dict()
    )


@bp.route('/<int:transaction_id>', methods=['POST'])
def update(transaction_id):
    """Update a transaction by id."""
    t = Transaction.get_by_id(transaction_id)
    if t is None:
        return ('Transaction not found', 404)
    t.person_id = request.values.get('donor_id') or request.values.get('person_id')
    t.date = datetime.strptime(request.values['day'], '%Y-%m-%d').date()
    t.method = request.values['method']
    t.amount = float(request.values['amount'])
    t.memo = request.values['memo']
    t.updated_at = datetime.now()

    db.session.add(t)
    db.session.commit()

    return get(transaction_id)


@bp.route('/<int:transaction_id>', methods=['DELETE'])
@bp.route('/<int:transaction_id>/delete', methods=['GET'])
def delete(transaction_id):
    """Delete a transaction by id."""
    t = Transaction.get_by_id(transaction_id)
    if t is None:
        return ('Transaction not found', 404)
    db.session.delete(t)
    db.session.commit()

    return get_latest()


@bp.route('/data', methods=['GET'])
def get_data():
    """Get all of transactions data."""
    return render_template('transaction_data.html.j2', transactions=get_transactions())


@bp.route('/export', methods=['GET'])
def show_export_info():
    """Show the export info."""
    return render_template('export.html.j2')


@bp.route('/<int:transaction_id>/receipt')
def receipt(transaction_id):
    """Generate a tax receipt for a single transaction."""
    t = Transaction.get_by_id(transaction_id)
    if t is None:
        return ('Transaction not found', 404)
    donor = Person.get_by_id(t.person_id)
    if donor is None:
        return ('Donor not found', 404)
    return render_template(
        'tax_receipt.html.j2',
        org=_org_value(),
        treasurer=_treasurer_value(),
        tax_year=t.year,
        receipt_number=next_single_transaction_receipt_number(t),
        receipt_date=datetime.now().strftime("%B %e, %Y"),
        name=donor.full_name,
        address=donor.address,
        amount=t.amount,
        signature_url=_signature_url(),
    )


@bp.route('/<int:transaction_id>/receipt/pdf', methods=['GET'])
def receipt_pdf(transaction_id):
    """Generate a PDF for a single transaction and mark it receipted."""
    transaction = Transaction.get_by_id(transaction_id)
    if transaction is None:
        return ('Transaction not found', 404)
    receipt_record = issue_single_transaction_receipt(
        transaction,
        _org_value(),
        _treasurer_value(),
    )
    return render_pdf(url_for('donor_family.receipt_by_id', receipt_id=receipt_record.id))
