from datetime import datetime
from flask import Blueprint
from models.transaction import get_transactions, pivot_transactions, get_years
from flask import render_template, request

bp = Blueprint('tables', __name__, url_prefix='/table')

num_to_month_dict = {
    1: 'Jan', 2: 'Feb', 3: 'Mar', 4: 'Apr', 5: 'May', 6: 'Jun',
    7: 'Jul', 8: 'Aug', 9: 'Sep', 10: 'Oct', 11: 'Nov', 12: 'Dec'
}

month_to_num_dict = {
    'jan': 1, 'january': 1,
    'feb': 2, 'february': 2,
    'mar': 3, 'march': 3,
    'apr': 4, 'april': 4,
    'may': 5,
    'jun': 6, 'june': 6,
    'jul': 7, 'july': 7,
    'aug': 8, 'august': 8,
    'sep': 9, 'september': 9,
    'oct': 10, 'october': 10,
    'nov': 11, 'november': 11,
    'dec': 12, 'december': 12
}


@bp.route('/', methods=['GET'])
def get_table():
    month = month_to_num_dict.get(request.values.get('month', '').lower())
    begin = datetime.strptime(request.values['begin'], '%Y-%m-%d').date() if request.values.get('begin') else None
    end = datetime.strptime(request.values['end'], '%Y-%m-%d').date() if request.values.get('end') else None
    return render_template(
        'table.html.j2',
        begin=begin, end=end, month=request.values.get('month', 'Filter by month'),
        transactions=get_transactions(begin=begin, end=end, month=month))


@bp.route('/pivot', methods=['GET'])
def get_pivot():
    years = get_years()
    return render_template(
        'pivot.html.j2',
        data=[{
            'year': year,
            'table_rows': make_pivot_table(year),
            'active': year == max(years)
        } for year in years]
    )


@bp.route('/export', methods=['GET'])
def export():
    return render_template('export.html.j2')


def make_pivot_table(year, vertical=True):
    p = pivot_transactions(year)
    cols = list(set([c for m, c in p]))
    pivot_table = [[''] + cols + ['Total']]
    grand_total = 0
    for n, m in sorted(num_to_month_dict.items()):
        s = sum([p.get((n, c), 0.0) for c in cols], 0)
        pivot_table.append([m] + ['{:,.2f}'.format(p.get((n, c), 0.0)) for c in cols] + ['{:,.2f}'.format(s)])
        grand_total += s
    pivot_table.append(
        ['Total']
        + ['{:,.2f}'.format(sum([p.get((n, c), 0.0) for n in num_to_month_dict.keys()], 0.0)) for c in cols]
        + ['{:,.2f}'.format(grand_total)]
    )
    return transpose(pivot_table, len(pivot_table), len(pivot_table[0])) if vertical else pivot_table


def transpose(M, nrows, ncols):
    T = []
    for i in range(ncols):
        T.append([])
        for j in range(nrows):
            T[-1].append(M[j][i])
    return T
