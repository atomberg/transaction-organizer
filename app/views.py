from flask import Flask, render_template
backend = Flask(__name__)


@backend.route('/')
def home():
    return render_template('index.html')


@backend.route('/hello')
def hello_world():
    return 'Hello World!'


if __name__ == "__main__":
    backend.run(host='localhost', port=5555, debug=True)
