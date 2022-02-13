from datetime import date, datetime
from fastapi import APIRouter, Request, Depends, Form, Body
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from app.schemas import TransactionCreate, TransactionUpdate
from app.crud.transactions import (
    create_transaction,
    remove_transaction,
    update_transaction,
)
from app.dependencies import get_db, get_settings, Settings
from app.templates.transactions import (
    fill_transaction_add_template,
    fill_transaction_data_template,
    fill_transaction_edit_template,
    fill_transaction_table_template,
    fill_transaction_export_template,
    fill_transaction_tax_receipt_template,
)
from typing import Optional

router = APIRouter()


@router.get('/', response_class=HTMLResponse)
async def transactions_table_view(
    request: Request,
    begin: Optional[date] = Body(None),
    end: Optional[date] = Body(None),
    db: Session = Depends(get_db),
):
    """Display all transactions in a table."""
    return fill_transaction_table_template(request, db, begin=begin, end=end)


@router.get('/latest', response_class=HTMLResponse)
async def transactions_input_form_view(request: Request, limit: int = 5, db: Session = Depends(get_db)):
    """Get the latest transactions and render a transaction input form."""
    return fill_transaction_add_template(request, db, limit)


@router.post('/', response_class=HTMLResponse)
async def create_transaction_view(
    request: Request,
    person_id: int = Form('person_id'),
    day: date = Form('day'),
    method: date = Form('method'),
    amount: float = Form('amount'),
    accepted_by: Optional[str] = Form('accepted_by'),
    memo: Optional[str] = Form('memo'),
    db: Session = Depends(get_db),
):
    """Add a new transaction."""
    t = TransactionCreate(person_id, day, method, amount, accepted_by, memo)
    create_transaction(db, t)
    return fill_transaction_add_template(request, db)


@router.get('/{transaction_id}', response_class=HTMLResponse)
async def transaction_view(request: Request, transaction_id: int, db: Session = Depends(get_db)):
    """Get a transation by id."""
    return fill_transaction_edit_template(request, db, transaction_id)


@router.post('/{transaction_id}', response_class=HTMLResponse)
def update_transaction_view(
    request: Request,
    transaction_id: int,
    person_id: int = Form('person_id'),
    day: date = Form('day'),
    method: date = Form('method'),
    amount: float = Form('amount'),
    accepted_by: Optional[str] = Form('accepted_by'),
    memo: Optional[str] = Form('memo'),
    receipt_issued: bool = Form('receipt_issued'),
    db: Session = Depends(get_db),
):
    """Update a transaction by id."""
    new_values = TransactionUpdate(
        person_id, day, method, amount, accepted_by, memo, updated_at=datetime.now(), receipt=receipt_issued
    )
    t = update_transaction(db, transaction_id, new_values)
    return fill_transaction_edit_template(request, db, transaction=t)


@router.delete('/{transaction_id}', response_class=HTMLResponse)
@router.post('/{transaction_id}/delete', response_class=HTMLResponse)
async def remove_transaction_view(request: Request, transaction_id: int, db: Session = Depends(get_db)):
    """Delete a transaction by id."""
    remove_transaction(db, transaction_id)
    return fill_transaction_add_template(request, db)


@router.get('/data', response_class=HTMLResponse)
async def transaction_data_view(request: Request, db: Session = Depends(get_db)):
    """Get all of transactions data."""
    return fill_transaction_data_template(request, db)


@router.get('/export', response_class=HTMLResponse)
async def show_export_info(request: Request):
    """Show the export info."""
    return fill_transaction_export_template(request)


@router.get('/{transaction_id}/receipt', response_class=HTMLResponse)
async def transaction_receipt_view(
    request: Request,
    transaction_id: int,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    """Generate a tax receipt for a single transaction."""
    return fill_transaction_tax_receipt_template(
        request, transaction_id, settings.organisation_name, settings.treasurer_name, db
    )
