from datetime import date
from fastapi import Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from .crud import get_transactions, get_transaction_by_id, get_categories, get_suppliers


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


def fill_data_template(request: Request, db: Session) -> HTMLResponse:
    """Fill the data template."""
    template_data = dict(request=request, transactions=get_transactions(db))
    return templates.TemplateResponse('data.html.j2', template_data)
