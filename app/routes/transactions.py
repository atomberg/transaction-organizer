from datetime import date, datetime
from fastapi import APIRouter, Request, Depends, Form
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from app.schemas import TransactionCreate, TransactionUpdate
from app.crud.transactions import (
    get_transaction_by_id,
    create_transaction,
    remove_transaction,
    update_transaction,
)
from app.crud.persons import get_person_by_id
from app.dependencies import get_db
from app.templates.transactions import (
    fill_transaction_add_template,
    fill_transaction_data_template,
    fill_transaction_edit_template,
    fill_transaction_table_template,
)
from typing import Optional

# bp = Blueprint('transactions', __name__, url_prefix='/transactions')
router = APIRouter()


@router.get('/', response_class=HTMLResponse)
def transactions_table_view(
    request: Request, begin: Optional[date] = None, end: Optional[date] = None, db: Session = Depends(get_db)
):
    """Display all transactions in a table."""
    # begin = datetime.strptime(begin, '%Y-%m-%d').date() or None
    # end = datetime.strptime(end, '%Y-%m-%d').date() or None
    return fill_transaction_table_template(request, db, begin=begin, end=end)


@router.get('/latest', response_class=HTMLResponse)
def transactions_input_form_view(request: Request, limit: int = 5, db: Session = Depends(get_db)):
    """Get the latest transactions and render a transaction input form."""
    return fill_transaction_add_template(request, db, limit)


@router.post('/', response_class=HTMLResponse)
def create_transaction_view(request: Request, db: Session = Depends(get_db)):
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
    return fill_transaction_add_template(request, db)


@router.get('/{transaction_id}', response_class=HTMLResponse)
def transaction_view(request: Request, transaction_id: int, db: Session = Depends(get_db)):
    """Get a transation by id."""
    t = get_transaction_by_id(db, transaction_id)
    return fill_transaction_edit_template(request, transaction=t)


@router.post('/{transaction_id}', response_class=HTMLResponse)
def update_transaction_view(request: Request, transaction_id: int, db: Session = Depends(get_db)):
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
    t = update_transaction(db, transaction_id, new_values)
    return fill_transaction_edit_template(request, transaction=t)


@router.delete('/{transaction_id}', response_class=HTMLResponse)
@router.post('/{transaction_id}/delete', response_class=HTMLResponse)
def remove_transaction_view(request: Request, transaction_id: int, db: Session = Depends(get_db)):
    """Delete a transaction by id."""
    remove_transaction(db, transaction_id)
    return fill_transaction_add_template(request, db)


@router.get('/data', response_class=HTMLResponse)
def transaction_data_view(request: Request, db: Session = Depends(get_db)):
    """Get all of transactions data."""
    return fill_transaction_data_template(request, db)


@router.get('/export', response_class=HTMLResponse)
def show_export_info(request: Request):
    """Show the export info."""
    return render_template('export.html.j2')


@router.get('/{transaction_id}/receipt', response_class=HTMLResponse)
def transaction_receipt_view(request: Request, transaction_id: int, db: Session = Depends(get_db)):
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
