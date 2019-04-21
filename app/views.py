from blueprints import autocomplete_bp, transaction_bp, view_bp
from flask import Flask


backend = Flask(__name__)

backend.register_blueprint(autocomplete_bp)
backend.register_blueprint(transaction_bp)
backend.register_blueprint(view_bp)


if __name__ == "__main__":
    backend.run(host='localhost', port=5555, debug=True)
