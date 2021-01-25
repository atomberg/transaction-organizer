"""."""
from .blueprints import transactions_bp, persons_bp, reports_bp
from flask import Flask


def create_app(config_filename='config.py'):
    app = Flask(__name__)
    app.config.from_pyfile(config_filename)

    app.register_blueprint(persons_bp)
    app.register_blueprint(transactions_bp)
    app.register_blueprint(reports_bp)
    return app
