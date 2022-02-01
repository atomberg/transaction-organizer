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

num_to_month_dict = {
    1: 'Jan',
    2: 'Feb',
    3: 'Mar',
    4: 'Apr',
    5: 'May',
    6: 'Jun',
    7: 'Jul',
    8: 'Aug',
    9: 'Sep',
    10: 'Oct',
    11: 'Nov',
    12: 'Dec',
}


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


def transpose(M, nrows, ncols):
    T = []
    for i in range(ncols):
        T.append([])
        for j in range(nrows):
            T[-1].append(M[j][i])
    return T


def make_pivot_table(db: Session, year: int, vertical: bool = True):
    p = pivot_transactions(db, year)
    cols = list(set([c for m, c in p]))
    pivot_table = [[''] + cols + ['Total']]
    grand_total = 0
    for n, m in sorted(num_to_month_dict.items()):
        s = sum([p.get((n, c), 0.0) for c in cols], 0)
        pivot_table.append(
            [m] + ['{:,.2f}'.format(p.get((n, c), 0.0)) for c in cols] + ['{:,.2f}'.format(s)]
        )
        grand_total += s
    pivot_table.append(
        ['Total']
        + ['{:,.2f}'.format(sum([p.get((n, c), 0.0) for n in num_to_month_dict.keys()], 0.0)) for c in cols]
        + ['{:,.2f}'.format(grand_total)]
    )
    return transpose(pivot_table, len(pivot_table), len(pivot_table[0])) if vertical else pivot_table


def fill_pivot_template(request: Request, db: Session) -> HTMLResponse:
    years = get_years(db)
    template_data = dict(
        request=request,
        data=[
            {'year': year, 'table_rows': make_pivot_table(db, year), 'active': year == max(years)}
            for year in years
        ],
    )
    return templates.TemplateResponse('pivot.html.j2', template_data)


def fill_data_template(request: Request, db: Session) -> HTMLResponse:
    """Fill the data template."""
    template_data = dict(request=request, transactions=get_transactions(db))
    return templates.TemplateResponse('data.html.j2', template_data)


def fill_export_template(request: Request) -> HTMLResponse:
    """Fill the export template."""
    return templates.TemplateResponse('export.html.j2', {'request': request})
