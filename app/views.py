from datetime import date, datetime
# import StringIO
# import csv
from models.db_session import Session
from models.transaction import Transaction, get_categories, get_suppliers, get_transactions, pivot_transactions

from flask import Flask, render_template, request, make_response
import flask_excel
backend = Flask(__name__)

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


@backend.route('/')
@backend.route('/input', methods=['GET', 'POST'])
def input_transactions():
    if request.method == 'POST':
        print(request.values)
        t = Transaction(
            datetime.strptime(request.values['day'], '%Y-%m-%d').date(),
            request.values['supplier'],
            float(request.values['amount']),
            request.values['category'])
        Session.add(t)
        Session.commit()
    return render_template(
        'input.html',
        today=date.today().strftime('%Y-%m-%d'), suppliers=get_suppliers(), categories=get_categories(),
        table_rows=get_transactions(5, True))


@backend.route('/transaction/<int:transaction_id>', methods=['GET', 'POST', 'DELETE'])
def transaction(transaction_id):
    if request.method == 'POST':
        t = Transaction.get_by_id(transaction_id)
        t.date = datetime.strptime(request.values['day'], '%Y-%m-%d').date()
        t.supplier = request.values['supplier']
        t.amount = float(request.values['amount'])
        t.category = request.values['category']
        t.notes = request.values['notes']
        t.updated_at = datetime.now()

        Session.add(t)
        Session.commit()

    return render_template(
        'edit.html',
        suppliers=get_suppliers(), categories=get_categories(),
        transaction=Transaction.get_by_id(transaction_id).to_dict()
    )


@backend.route('/transaction/<int:transaction_id>/delete', methods=['POST'])
def del_transaction(transaction_id):
    t = Transaction.get_by_id(transaction_id)
    Session.delete(t)
    Session.commit()
    return render_template(
        'input.html',
        today=date.today().strftime('%Y-%m-%d'), suppliers=get_suppliers(), categories=get_categories(),
        table_rows=get_transactions(3))


@backend.route('/view', methods=['GET'])
def view_transactions():
    month = month_to_num_dict.get(request.values.get('month', '').lower())
    begin = datetime.strptime(request.values['begin'], '%Y-%m-%d').date() if request.values.get('begin') else None
    end = datetime.strptime(request.values['end'], '%Y-%m-%d').date() if request.values.get('end') else None
    return render_template(
        'table.html',
        begin=begin, end=end, month=request.values.get('month', 'Filter by month'),
        table_rows=get_transactions(begin=begin, end=end, month=month))


@backend.route('/pivot', methods=['GET'])
def pivot():
    year = int(request.values.get('year', datetime.now().year))
    return render_template(
        'pivot.html',
        year=year,
        table_rows=make_pivot_table(year))


@backend.route('/download/<string:filename>', methods=['GET'])
def download(filename):
    # Prepare data for download
    if filename == 'pivot':
        data = make_pivot_table()
        print(data)
    elif filename == 'transactions':
        month = month_to_num_dict.get(request.values.get('month', '').lower())
        begin = datetime.strptime(request.values['begin'], '%Y-%m-%d').date() if request.values.get('begin') else None
        end = datetime.strptime(request.values['end'], '%Y-%m-%d').date() if request.values.get('end') else None
        data = get_transactions(begin=begin, end=end, month=month)
    else:
        return make_response()

    # Prepare response
    if request.values.get('format') == 'xlsx':
        output = flask_excel.make_response_from_array(data, 'xlsx')
        output.headers["Content-Disposition"] = "attachment; filename=%s.xlsx" % filename
        # output.headers["Content-type"] = "text/csv"
    else:
        output = flask_excel.make_response_from_array(data, 'csv')
        output.headers["Content-Disposition"] = "attachment; filename=%s.csv" % filename
        output.headers["Content-type"] = "text/csv"
    return output


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
            ['Total'] +
            ['{:,.2f}'.format(sum([p.get((n, c), 0.0) for n in num_to_month_dict.keys()], 0.0)) for c in cols] +
            ['{:,.2f}'.format(grand_total)]
        )
        return transpose(pivot_table, len(pivot_table), len(pivot_table[0])) if vertical else pivot_table


def transpose(M, nrows, ncols):
    T = []
    for i in range(ncols):
        T.append([])
        for j in range(nrows):
            T[-1].append(M[j][i])
    return T


if __name__ == "__main__":
    backend.run(host='localhost', port=5555, debug=True)
