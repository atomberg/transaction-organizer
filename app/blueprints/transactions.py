from datetime import date, datetime
from flask import Blueprint, request, render_template
from models.db_session import Session
from models.transaction import Transaction, get_transactions, get_accepted_bys
from models.person import get_person_names

bp = Blueprint('transactions', __name__, url_prefix='/transactions')


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
            end=datetime.strptime(end, '%Y-%m-%d').date() if end else None
        )
    )


@bp.route('/latest', methods=['GET'])
def get_latest():
    """Get the latest transactions and render a transaction input form."""
    limit = request.values.get('limit', 5)
    return render_template(
        'transaction_add.html.j2',
        today=date.today().strftime('%Y-%m-%d'),
        persons=get_person_names(),
        accepted_bys=get_accepted_bys(),
        transactions=get_transactions(lim=limit, reverse=False)
    )


@bp.route('/', methods=['POST'])
def add():
    """Add a new transaction."""
    Session.add(Transaction(
        person_id=request.values['person_id'],
        date=datetime.strptime(request.values['day'], '%Y-%m-%d').date(),
        method=request.values['method'],
        amount=float(request.values['amount']),
        accepted_by=request.values['accepted_by'],
        # memo=request.values['memo']
    ))
    Session.commit()
    return get_latest()


@bp.route('/<int:transaction_id>', methods=['GET'])
def get(transaction_id):
    """Get a transation by id."""
    return render_template(
        'transaction_edit.html.j2',
        transaction=Transaction.get_by_id(transaction_id).to_dict()
    )


@bp.route('/<int:transaction_id>', methods=['POST'])
def update(transaction_id):
    """Update a transaction by id."""
    t = Transaction.get_by_id(transaction_id)
    t.person_id = request.values['person_id']
    t.date = datetime.strptime(request.values['day'], '%Y-%m-%d').date()
    t.method = request.values['method']
    t.amount = float(request.values['amount'])
    t.accepted_by = request.values['accepted_by']
    t.memo = request.values['memo']
    t.updated_at = datetime.now()

    Session.add(t)
    Session.commit()

    return get(transaction_id)


@bp.route('/<int:transaction_id>', methods=['DELETE'])
@bp.route('/<int:transaction_id>/delete', methods=['POST'])
def delete(transaction_id):
    """Delete a transaction by id."""
    t = Transaction.get_by_id(transaction_id)
    t.deleted_at = datetime.now()
    Session.add(t)
    Session.commit()

    return get_latest()
