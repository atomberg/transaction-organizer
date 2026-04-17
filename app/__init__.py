"""."""
import datetime
import os
import shutil

from flask import Flask
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


def _format_phone(value):
    if value is None:
        return ''
    as_text = str(value)
    digits = ''.join(ch for ch in as_text if ch.isdigit())
    if len(digits) == 10:
        return f'({digits[0:3]}) {digits[3:6]}-{digits[6:10]}'
    return as_text


def create_app(config_filename='config.py'):
    app = Flask(__name__)
    app.config.from_pyfile(config_filename)
    app.config['SECRET_KEY'] = (
        os.environ.get('SECRET_KEY')
        or app.config.get('SECRET_KEY')
        or 'dev-secret-key'
    )
    app.secret_key = app.config['SECRET_KEY']
    app.add_template_filter(_format_phone, 'phone_format')

    # Backup the database file
    backup_path = app.config['SQLALCHEMY_DATABASE_BACKUP_PATH']
    backup_path.mkdir(exist_ok=True, parents=True)
    backup_path /= (datetime.date.today().replace(day=1) - datetime.timedelta(days=1)).strftime("%Y_%B.bak")
    if app.config['SQLALCHEMY_DATABASE_PATH'].exists() and not backup_path.exists():
        shutil.copyfile(app.config['SQLALCHEMY_DATABASE_PATH'], backup_path)

    db.init_app(app)

    # Ensure schema exists for fresh/empty SQLite files.
    with app.app_context():
        from app.models.family import Family, FamilyMember
        from app.models.person import Person
        from app.models.tax_receipt import TaxReceipt, TaxReceiptItem
        from app.models.transaction import Transaction

        _ = (Person, Transaction, TaxReceipt, TaxReceiptItem, Family, FamilyMember)
        db.create_all()

    # Import and register blueprints
    from .blueprints import donor_family_bp, persons_bp, reports_bp, transactions_bp

    app.register_blueprint(donor_family_bp)
    app.register_blueprint(persons_bp)
    app.register_blueprint(transactions_bp)
    app.register_blueprint(reports_bp)
    return app
