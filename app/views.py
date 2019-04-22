from blueprints import autocomplete_bp, tables_bp, transactions_bp
from flask import Flask


backend = Flask(__name__)

backend.register_blueprint(autocomplete_bp)
backend.register_blueprint(tables_bp)
backend.register_blueprint(transactions_bp)


if __name__ == "__main__":
    backend.run(host='localhost', port=5555, debug=True)
