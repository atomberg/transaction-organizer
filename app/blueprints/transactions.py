from datetime import date, datetime
from flask import Blueprint, request, render_template
from models.db_session import Session
from models.transaction import Transaction, get_categories, get_suppliers, get_transactions


bp = Blueprint('transactions', __name__, url_prefix='/transactions')


@bp.app_template_filter()
def currency_format(value):
    return f'{value:.2f}'


@bp.route('/', methods=['GET'])
def get_latest():
    """Get 3 latest transactions."""
    return render_template(
        'input.html.j2',
        today=date.today().strftime('%Y-%m-%d'),
        suppliers=get_suppliers(),
        categories=get_categories(),
        transactions=get_transactions(3, True)
    )


@bp.route('/input', methods=['POST'])
@bp.route('/', methods=['POST'])
def add():
    """Input transaction."""
    t = Transaction(
        datetime.strptime(request.values['day'], '%Y-%m-%d').date(),
        request.values['supplier'],
        float(request.values['amount']),
        request.values['category'])
    Session.add(t)
    Session.commit()
    return get_latest()


@bp.route('/<int:transaction_id>', methods=['GET'])
def get(transaction_id):
    """Get a transation by id."""
    return render_template(
        'edit.html.j2',
        suppliers=get_suppliers(),
        categories=get_categories(),
        transaction=Transaction.get_by_id(transaction_id)
    )


@bp.route('/<int:transaction_id>', methods=['POST'])
def update(transaction_id):
    """Update transaction by id."""
    t = Transaction.get_by_id(transaction_id)
    t.date = datetime.strptime(request.values['day'], '%Y-%m-%d').date()
    t.supplier = request.values['supplier']
    t.amount = float(request.values['amount'])
    t.category = request.values['category']
    t.notes = request.values['notes']
    t.updated_at = datetime.now()

    Session.add(t)
    Session.commit()

    return get(transaction_id)


@bp.route('/<int:transaction_id>', methods=['DELETE'])
@bp.route('/<int:transaction_id>/delete', methods=['POST'])
def delete(transaction_id):
    """Delete transactio by id."""
    t = Transaction.get_by_id(transaction_id)
    Session.delete(t)
    Session.commit()
    return get_latest()


@bp.route('/data', methods=['GET'])
def get_data():
    """Get all of transactions data."""
    return render_template('data.html.j2', transactions=get_transactions())
