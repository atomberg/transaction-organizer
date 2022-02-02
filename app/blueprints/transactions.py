from datetime import date
from typing import Optional

from ..schemas import TransactionCreate, TransactionUpdate
from fastapi import APIRouter, Request, Depends, Form
from fastapi.responses import HTMLResponse
from ..dependencies import get_db
from sqlalchemy.orm import Session

from ..crud import update_transaction, remove_transaction, create_transaction
from ..templates import fill_input_template, fill_edit_template, fill_data_template

router = APIRouter()


@router.get('/', response_class=HTMLResponse)
async def input_new_transaction_view(request: Request, db: Session = Depends(get_db)):
    """Get 3 latest transactions."""
    return fill_input_template(request, db)


@router.post('/input', response_class=HTMLResponse)
@router.post('/', response_class=HTMLResponse)
async def create_transaction_view(
    request: Request,
    day: str = Form('day'),
    supplier: str = Form('supplier'),
    amount: float = Form('amount'),
    category: str = Form('category'),
    db: Session = Depends(get_db),
):
    """Input transaction."""
    day = date.today()
    transaction = TransactionCreate(date=day, supplier=supplier, amount=amount, category=category)
    create_transaction(db, transaction)
    return fill_input_template(request, db)


@router.get('/{transaction_id}', response_class=HTMLResponse)
async def edit_transaction_view(request: Request, transaction_id: int, db: Session = Depends(get_db)):
    """Get a transation by id."""
    return fill_edit_template(request, transaction_id, db)


@router.post('/{transaction_id}', response_class=HTMLResponse)
async def update_transaction_view(
    request: Request,
    transaction_id: int,
    day: str = Form('day'),
    supplier: str = Form('supplier'),
    amount: float = Form('amount'),
    category: str = Form('category'),
    notes: Optional[str] = Form('notes'),
    db: Session = Depends(get_db),
):
    """Update transaction by id."""
    new_values = TransactionUpdate(
        date=day, supplier=supplier, amount=amount, category=category, notes=notes
    )
    t = update_transaction(db, transaction_id, new_values)
    return fill_edit_template(request, t.id, db)


@router.delete('/{transaction_id}', response_class=HTMLResponse)
@router.post('/{transaction_id}/delete', response_class=HTMLResponse)
async def delete_transaction_view(request: Request, transaction_id: int, db: Session = Depends(get_db)):
    """Delete transaction by id."""
    remove_transaction(db, transaction_id)
    return fill_input_template(request, db)


@router.get('/data', response_class=HTMLResponse)
async def transaction_data_view(request: Request, db: Session = Depends(get_db)):
    """Get all of transactions data."""
    return fill_data_template(request, db)
