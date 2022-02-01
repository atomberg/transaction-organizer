from datetime import date
from ..templates import fill_pivot_template, fill_export_template, fill_table_template
from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from ..dependencies import get_db
from sqlalchemy.orm import Session
from typing import Optional
from ..crud import get_transactions_by_month, get_transactions_between_dates

router = APIRouter()

month_to_num_dict = {
    'jan': 1,
    'january': 1,
    'feb': 2,
    'february': 2,
    'mar': 3,
    'march': 3,
    'apr': 4,
    'april': 4,
    'may': 5,
    'jun': 6,
    'june': 6,
    'jul': 7,
    'july': 7,
    'aug': 8,
    'august': 8,
    'sep': 9,
    'september': 9,
    'oct': 10,
    'october': 10,
    'nov': 11,
    'november': 11,
    'dec': 12,
    'december': 12,
}


@router.get('/', response_class=HTMLResponse)
def get_table(
    request: Request,
    begin: Optional[date] = None,
    end: Optional[date] = None,
    month: Optional[str] = None,
    db: Session = Depends(get_db),
):
    if month:
        transactions = get_transactions_by_month(db, month_to_num_dict.get(month.lower()))
    else:
        transactions = get_transactions_between_dates(db, begin, end)
    return fill_table_template(request, db, transactions, begin, end, month)


@router.get('/pivot', response_class=HTMLResponse)
def pivot_view(request: Request, db: Session = Depends(get_db)):
    return fill_pivot_template(request, db)


@router.get('/export', response_class=HTMLResponse)
async def export_view(request: Request):
    return fill_export_template(request)
