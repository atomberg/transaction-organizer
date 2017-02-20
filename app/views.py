import datetime
from flask import Flask, render_template
backend = Flask(__name__)


@backend.route('/')
def home():
    return render_template(
        'index.html',
        today=datetime.date.today().strftime('%Y-%m-%d'),
        suppliers=['Cdef', 'Cefd'],
        categories=['Abcdef', 'Acbdef', 'Bacdef'])


@backend.route('/add_transaction')
def add_transaction():
    return render_template(
        'index.html',
        today=datetime.date.today().strftime('%Y-%m-%d'),
        suppliers=['Cdef', 'Cefd'],
        categories=['Abcdef', 'Acbdef', 'Bacdef'])


@backend.route('/hello')
def hello_world():
    return 'Hello World!'


if __name__ == "__main__":
    backend.run(host='localhost', port=5555, debug=True)
