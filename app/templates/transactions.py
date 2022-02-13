from datetime import date, datetime
from fastapi import Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from typing import Optional
from ..models.transaction import Transaction

from ..crud.persons import get_person_by_id, get_person_names
from ..crud.transactions import (
    get_transactions,
    get_accepted_bys,
    get_transactions_between_dates,
    get_transaction_by_id,
)


def currency_format(value):
    return f'{value:.2f}'


templates = Jinja2Templates(directory="app/templates")
templates.env.filters['currency_format'] = currency_format


def fill_transaction_add_template(request: Request, db: Session, limit: int = 5) -> HTMLResponse:
    """Fill the input template with latest transactions."""
    template_data = dict(
        request=request,
        today=date.today().strftime('%Y-%m-%d'),
        persons=get_person_names(db),
        accepted_bys=get_accepted_bys(db),
        transactions=get_transactions(db, limit=limit),
    )
    return templates.TemplateResponse('transaction_add.html.j2', template_data)


def fill_transaction_edit_template(request: Request, db: Session, transaction_id: int) -> HTMLResponse:
    """Fill the edit template with data from given transaction."""
    template_data = dict(request=request, transaction=get_transaction_by_id(db, transaction_id))
    return templates.TemplateResponse('transaction_edit.html.j2', template_data)


def fill_transaction_table_template(
    request: Request, db: Session, begin: Optional[date], end: Optional[date]
) -> HTMLResponse:
    transactions = get_transactions_between_dates(db, begin, end)
    template_data = dict(request=request, begin=begin, end=end, transactions=transactions)
    return templates.TemplateResponse('transaction_table.html.j2', template_data)


def fill_transaction_data_template(request: Request, db: Session) -> HTMLResponse:
    """Fill the data template."""
    template_data = dict(request=request, transactions=get_transactions(db))
    return templates.TemplateResponse('data.html.j2', template_data)


def fill_transaction_export_template(request: Request) -> HTMLResponse:
    return templates.TemplateResponse('transaction_export.html.j2', dict(request=request))


def fill_transaction_tax_receipt_template(
    request: Request, transaction_id: int, organisation_name: str, treasurer_name: str, db: Session
) -> HTMLResponse:
    t = get_transaction_by_id(db, transaction_id)
    p = get_person_by_id(db, t.person_id)
    template_data = dict(
        request=request,
        org=organisation_name,
        treasurer=treasurer_name,
        tax_year=t.year,
        receipt_number=f"{p.id}-{t.id}",
        receipt_date=datetime.now().strftime("%B %e, %Y"),
        name=p.full_name,
        address=p.address,
        amount=t.amount,
    )
    return templates.TemplateResponse('tax_receipt.html.j2', template_data)
