"""."""
import datetime
import shutil

from flask import Flask
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


def create_app(config_filename='config.py'):
    app = Flask(__name__)
    app.config.from_pyfile(config_filename)

    # Backup the database file
    backup_path = app.config['SQLALCHEMY_DATABASE_BACKUP_PATH']
    backup_path.mkdir(exist_ok=True, parents=True)
    backup_path /= (datetime.date.today().replace(day=1) - datetime.timedelta(days=1)).strftime("%Y_%B.bak")
    if app.config['SQLALCHEMY_DATABASE_PATH'].exists() and not backup_path.exists():
        shutil.copyfile(app.config['SQLALCHEMY_DATABASE_PATH'], backup_path)

    db.init_app(app)

    # Ensure schema exists for fresh/empty SQLite files.
    with app.app_context():
        from app.models.person import Person
        from app.models.tax_receipt import TaxReceipt, TaxReceiptItem
        from app.models.transaction import Transaction

        _ = (Person, Transaction, TaxReceipt, TaxReceiptItem)
        db.create_all()

    # Import and register blueprints
    from .blueprints import persons_bp, reports_bp, transactions_bp

    app.register_blueprint(persons_bp)
    app.register_blueprint(transactions_bp)
    app.register_blueprint(reports_bp)
    return app
