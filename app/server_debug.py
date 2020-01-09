from blueprints import transactions_bp, persons_bp, reports_bp
from flask import Flask

backend = Flask(__name__)
backend.config.from_pyfile('config.py')

backend.register_blueprint(persons_bp)
backend.register_blueprint(transactions_bp)
backend.register_blueprint(reports_bp)


if __name__ == "__main__":
    backend.secret_key = 'super secret key'
    backend.config['SESSION_TYPE'] = 'filesystem'

    backend.run(host='localhost', port=5555, debug=True)
