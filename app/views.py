from datetime import date, datetime
from models.db_session import Session
from models.transaction import Transaction

from flask import Flask, render_template, request
backend = Flask(__name__)


@backend.route('/')
def home():
    return render_template(
        'index.html',
        today=date.today().strftime('%Y-%m-%d'),
        suppliers=['Cdef', 'Cefd'],
        categories=['Abcdef', 'Acbdef', 'Bacdef'])


@backend.route('/transaction', methods=['POST'])
def add_transaction():
    s = Session()
    t = Transaction(
        datetime.strptime(request.values['day'], '%Y-%m-%d').date(),
        request.values['supplier'],
        float(request.values['amount']),
        request.values['category'])
    s.add(t)
    s.commit()
    Session.remove()
    return render_template(
        'index.html',
        today=date.today().strftime('%Y-%m-%d'),
        suppliers=['Cdef', 'Cefd'],
        categories=['Abcdef', 'Acbdef', 'Bacdef'])


@backend.route('/hello')
def hello_world():
    return 'Hello World!'


if __name__ == "__main__":
    backend.run(host='localhost', port=5555, debug=True)
