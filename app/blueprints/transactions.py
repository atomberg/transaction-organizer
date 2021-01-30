from datetime import date, datetime
from flask import Blueprint, request, render_template, current_app as app

from app import db
from app.models.transaction import Transaction, get_transactions, get_accepted_bys
from app.models.person import Person, get_person_names

bp = Blueprint('transactions', __name__, url_prefix='/transactions')


@bp.add_app_template_filter
def currency_format(value):
    return f'{value:.2f}'


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
        persons=get_person_names(),
        accepted_bys=get_accepted_bys(),
        transactions=get_transactions(lim=limit, reverse=True),
    )


@bp.route('/', methods=['POST'])
def add():
    """Add a new transaction."""
    db.session.add(
        Transaction(
            person_id=request.values['person_id'],
            date=datetime.strptime(request.values['day'], '%Y-%m-%d').date(),
            method=request.values['method'],
            amount=float(request.values['amount']),
            accepted_by=request.values['accepted_by'],
            memo=request.values['memo'],
        )
    )
    db.session.commit()
    return get_latest()


@bp.route('/<int:transaction_id>', methods=['GET'])
def get(transaction_id):
    """Get a transation by id."""
    print(Transaction.get_by_id(transaction_id).to_dict())
    return render_template(
        'transaction_edit.html.j2', transaction=Transaction.get_by_id(transaction_id).to_dict()
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
    t.receipt = request.values['receipt_issued'] == 'True'

    db.session.add(t)
    db.session.commit()

    return get(transaction_id)


@bp.route('/<int:transaction_id>', methods=['DELETE'])
@bp.route('/<int:transaction_id>/delete', methods=['GET'])
def delete(transaction_id):
    """Delete a transaction by id."""
    t = Transaction.get_by_id(transaction_id)
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
    p = Person.get_by_id(t.person_id)
    return render_template(
        'tax_receipt.html.j2',
        org=app.config.get('ORG'),
        treasurer=app.config.get('TREASURER'),
        tax_year=t.year,
        receipt_number=f"{p.id}-{t.id}",
        receipt_date=datetime.now().strftime("%B %e, %Y"),
        name=p.full_name,
        address=p.address,
        amount=t.amount,
    )
