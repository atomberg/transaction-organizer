"""Shared pytest fixtures for application tests."""

from pathlib import Path

import pytest

from app import create_app, db
from app.models.person import Person
from app.models.tax_receipt import TaxReceipt, TaxReceiptItem
from app.models.transaction import Transaction


@pytest.fixture(scope='session')
def app():
    backend = create_app(Path(__file__).parent / 'data' / 'test_config.py')
    backend.secret_key = 'test key'
    backend.config['SQLALCHEMY_DATABASE_PATH'] = Path(__file__).parent / 'data' / 'test.db'
    backend.config[
        'SQLALCHEMY_DATABASE_URI'
    ] = f'sqlite:///{backend.config["SQLALCHEMY_DATABASE_PATH"].absolute()}'
    backend.config['TESTING'] = True

    with backend.app_context():
        db.drop_all()
        db.create_all()

    yield backend

    with backend.app_context():
        db.session.remove()
        db.drop_all()


@pytest.fixture()
def test_client(app):
    with app.test_client() as client:
        yield client


@pytest.fixture(autouse=True)
def clean_database(app):
    with app.app_context():
        db.session.query(TaxReceiptItem).delete()
        db.session.query(TaxReceipt).delete()
        db.session.query(Transaction).delete()
        db.session.query(Person).delete()
        db.session.commit()
    yield
