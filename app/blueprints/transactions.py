from datetime import date, datetime
from flask import Blueprint, request, render_template
from models.db_session import Session
from models.transaction import Transaction, get_categories, get_suppliers, get_transactions


bp = Blueprint('transactions', __name__, url_prefix='/transactions')


@bp.route('/', methods=['GET'])
def get_latest_transactions():
    """Get 3 latest transactions."""
    return render_template(
        'input.html.j2',
        today=date.today().strftime('%Y-%m-%d'),
        suppliers=get_suppliers(),
        categories=get_categories(),
        table_rows=get_transactions(3, True)
    )


@bp.route('/input', methods=['POST'])
@bp.route('/', methods=['POST'])
def input_transaction():
    """Input transaction."""
    print(request.values)
    t = Transaction(
        datetime.strptime(request.values['day'], '%Y-%m-%d').date(),
        request.values['supplier'],
        float(request.values['amount']),
        request.values['category'])
    Session.add(t)
    Session.commit()
    return get_latest_transactions()


@bp.route('/<int:transaction_id>', methods=['GET'])
def get_transaction(transaction_id):
    """Get a transation by id."""
    return render_template(
        'edit.html.j2',
        suppliers=get_suppliers(),
        categories=get_categories(),
        transaction=Transaction.get_by_id(transaction_id).to_dict()
    )


@bp.route('/<int:transaction_id>', methods=['POST'])
def update_transaction(transaction_id):
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

    return get_transaction(transaction_id)


@bp.route('/<int:transaction_id>', methods=['DELETE'])
@bp.route('/<int:transaction_id>/delete', methods=['POST'])
def delete_transaction(transaction_id):
    """."""
    t = Transaction.get_by_id(transaction_id)
    Session.delete(t)
    Session.commit()
    return get_latest_transactions()
