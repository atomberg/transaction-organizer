from datetime import date
from fastapi import Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from typing import Optional, List
from .models import Transaction

from .crud import (
    get_transactions,
    get_transaction_by_id,
    get_categories,
    get_suppliers,
    get_years,
    pivot_transactions,
)


def currency_format(value):
    return f'{value:.2f}'


templates = Jinja2Templates(directory="app/templates")
templates.env.filters['currency_format'] = currency_format


def fill_input_template(request: Request, db: Session) -> HTMLResponse:
    """Fill the input template with 3 latest transactions."""
    transactions = get_transactions(db, limit=3)
    template_data = dict(
        request=request,
        today=date.today().strftime('%Y-%m-%d'),
        suppliers=get_suppliers(db),
        categories=get_categories(db),
        transactions=transactions,
    )
    return templates.TemplateResponse('input.html.j2', template_data)


def fill_edit_template(request: Request, transaction_id: int, db: Session) -> HTMLResponse:
    """Fill the edit template with data from given transaction."""
    t = get_transaction_by_id(db, transaction_id)
    template_data = dict(
        request=request, suppliers=get_suppliers(db), categories=get_categories(db), transaction=t,
    )
    return templates.TemplateResponse('edit.html.j2', template_data)


def fill_table_template(
    request: Request,
    db: Session,
    transactions: List[Transaction],
    begin: Optional[date],
    end: Optional[date],
    month: Optional[str],
) -> HTMLResponse:
    if not month:
        month = 'Filter by month'
    template_data = dict(request=request, begin=begin, end=end, month=month, transactions=transactions)
    return templates.TemplateResponse('table.html.j2', template_data)


def fill_data_template(request: Request, db: Session) -> HTMLResponse:
    """Fill the data template."""
    template_data = dict(request=request, transactions=get_transactions(db))
    return templates.TemplateResponse('data.html.j2', template_data)


def fill_export_template(request: Request) -> HTMLResponse:
    """Fill the export template."""
    return templates.TemplateResponse('export.html.j2', {'request': request})


@bp.route('/', methods=['GET'])
def get_all():
    """Display all transactions in a table."""
    begin = datetime.strptime(request.values.get('begin'), '%Y-%m-%d').date() or None
    end = datetime.strptime(request.values.get('end'), '%Y-%m-%d').date() or None
    transactions = get_transactions_between_dates(db, begin, end)
    return render_template('transaction_table.html.j2', begin=begin, end=end, transactions=transactions)


@bp.route('/latest', methods=['GET'])
def get_latest():
    """Get the latest transactions and render a transaction input form."""
    limit = request.values.get('limit', 5)
    return render_template(
        'transaction_add.html.j2',
        today=date.today().strftime('%Y-%m-%d'),
        persons=get_person_names(db),
        accepted_bys=get_accepted_bys(),
        transactions=get_transactions(db, lim=limit),
    )


@bp.route('/', methods=['POST'])
def add():
    """Add a new transaction."""
    t = TransactionCreate(
        person_id=request.values['person_id'],
        date=datetime.strptime(request.values['day'], '%Y-%m-%d').date(),
        method=request.values['method'],
        amount=float(request.values['amount']),
        accepted_by=request.values['accepted_by'],
        memo=request.values['memo'],
    )
    create_transaction(db, t)
    return get_latest()


@bp.route('/<int:transaction_id>', methods=['GET'])
def get(transaction_id):
    """Get a transation by id."""
    t = get_transaction_by_id(db, transaction_id)
    return render_template('transaction_edit.html.j2', transaction=t)


@bp.route('/<int:transaction_id>', methods=['POST'])
def update(transaction_id):
    """Update a transaction by id."""
    new_values = TransactionUpdate(
        person_id=request.values['person_id'],
        date=datetime.strptime(request.values['day'], '%Y-%m-%d').date(),
        method=request.values['method'],
        amount=float(request.values['amount']),
        accepted_by=request.values['accepted_by'],
        memo=request.values['memo'],
        updated_at=datetime.now(),
        receipt=request.values['receipt_issued'] == 'True',
    )
    update_transaction(db, transaction_id, new_values)
    return get(transaction_id)


@bp.route('/<int:transaction_id>', methods=['DELETE'])
@bp.route('/<int:transaction_id>/delete', methods=['GET'])
def delete(transaction_id):
    """Delete a transaction by id."""
    remove_transaction(db, transaction_id)
    return get_latest()


@bp.route('/data', methods=['GET'])
def get_data():
    """Get all of transactions data."""
    return render_template('transaction_data.html.j2', transactions=get_transactions(db))


@bp.route('/export', methods=['GET'])
def show_export_info():
    """Show the export info."""
    return render_template('export.html.j2')


@bp.route('/<int:transaction_id>/receipt')
def receipt(transaction_id):
    """Generate a tax receipt for a single transaction."""
    t = get_transaction_by_id(db, transaction_id)
    p = get_person_by_id(db, t.person_id)
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
