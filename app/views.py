from datetime import date, datetime
from models.db_session import Session
from models.transaction import Transaction, get_categories, get_suppliers, get_transactions

from flask import Flask, render_template, request
backend = Flask(__name__)


@backend.route('/')
@backend.route('/transactions', methods=['GET', 'POST'])
def add_transaction():
    if request.method == 'POST':
        print request.values
        t = Transaction(
            datetime.strptime(request.values['day'], '%Y-%m-%d').date(),
            request.values['supplier'],
            float(request.values['amount']),
            request.values['category'])
        Session.add(t)
        Session.commit()
    return render_template(
        'index.html',
        today=date.today().strftime('%Y-%m-%d'),
        suppliers=get_suppliers(),
        categories=get_categories(),
        table_rows=get_transactions(3))


@backend.route('/view', methods=['GET'])
def view_transaction():
    return render_template(
        'table.html',
        table_rows=get_transactions())


if __name__ == "__main__":
    backend.run(host='localhost', port=5555, debug=True)
