from datetime import date, datetime
from flask import Blueprint, request, render_template
from models.db_session import Session
from models.transaction import Transaction, get_categories, get_suppliers, get_transactions


bp = Blueprint('transaction', __name__)


@bp.route('/')
@bp.route('/input', methods=['GET', 'POST'])
def input_transactions():
    if request.method == 'POST':
        print(request.values)
        t = Transaction(
            datetime.strptime(request.values['day'], '%Y-%m-%d').date(),
            request.values['supplier'],
            float(request.values['amount']),
            request.values['category'])
        Session.add(t)
        Session.commit()
    return render_template(
        'input.html',
        today=date.today().strftime('%Y-%m-%d'), suppliers=get_suppliers(), categories=get_categories(),
        table_rows=get_transactions(3, True))


@bp.route('/transaction/<int:transaction_id>', methods=['GET', 'POST', 'DELETE'])
def transaction(transaction_id):
    if request.method == 'POST':
        t = Transaction.get_by_id(transaction_id)
        t.date = datetime.strptime(request.values['day'], '%Y-%m-%d').date()
        t.supplier = request.values['supplier']
        t.amount = float(request.values['amount'])
        t.category = request.values['category']
        t.notes = request.values['notes']
        t.updated_at = datetime.now()

        Session.add(t)
        Session.commit()

    return render_template(
        'edit.html',
        suppliers=get_suppliers(), categories=get_categories(),
        transaction=Transaction.get_by_id(transaction_id).to_dict()
    )


@bp.route('/transaction/<int:transaction_id>/delete', methods=['POST'])
def del_transaction(transaction_id):
    t = Transaction.get_by_id(transaction_id)
    Session.delete(t)
    Session.commit()
    return render_template(
        'input.html',
        today=date.today().strftime('%Y-%m-%d'), suppliers=get_suppliers(), categories=get_categories(),
        table_rows=get_transactions(3))
