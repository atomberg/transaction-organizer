# import os
# import tempfile

import pytest

from app import create_app, db
from app.models.person import Person, datetime
from app.models.transaction import Transaction
from pathlib import Path


@pytest.fixture(scope='module')
def test_client():
    backend = create_app()
    backend.secret_key = 'test key'
    backend.config['SQLALCHEMY_DATABASE_PATH'] = Path(__file__).parent / 'data' / 'test.db'
    backend.config[
        'SQLALCHEMY_DATABASE_URI'
    ] = f"sqlite:///{backend.config['SQLALCHEMY_DATABASE_PATH'].absolute()}"
    backend.config['TESTING'] = True

    breakpoint()

    with backend.test_client() as client:
        yield client

    # backend.config['SQLALCHEMY_DATABASE_PATH'].unlink()


@pytest.fixture(scope='module')
def init_database(test_client):
    breakpoint()
    # Create the database and the database table
    db.create_all()

    # Insert user data
    alice = Person(
        first_name='Alice',
        last_name='Wu',
        phone='(123) 456-7890',
        email='awu@email.com',
        address='123 Alice Ave. <br> Alice City, TT, A1B 2C3',
    )
    bob = Person(
        first_name='Bob',
        last_name='Xi',
        phone='(567) 890-1234',
        email='bxi@email.ca',
        address='456 Bob St. <br> Bob City, TT, B2C 3D4',
    )
    charlie = Person(
        first_name='Charlie',
        last_name='Yu',
        phone='(123) 456-7897',
        email='cyu@email.com',
        address='789 Charlie Blvd. <br> Charlie City, TT, C3D 4E5',
    )
    db.session.add_all([alice, bob, charlie])
    db.session.add_all(
        [
            Transaction(
                person_id=alice.id,
                date=datetime.date(2019, 4, 27),
                method='Cash',
                amount=125,
                accepted_by='Me',
            ),
            Transaction(
                person_id=alice.id,
                date=datetime.date(2019, 4, 27),
                method='Credit',
                amount=23,
                accepted_by='You',
            ),
            Transaction(
                person_id=bob.id,
                date=datetime.date(2019, 4, 27),
                method='Credit',
                amount=36,
                accepted_by='Me',
            ),
            Transaction(
                person_id=bob.id,
                date=datetime.date(2019, 4, 27),
                method='Cash',
                amount=40,
                accepted_by='You',
            ),
            Transaction(
                person_id=charlie.id,
                date=datetime.date(2019, 4, 27),
                method='Cash',
                amount=59,
                accepted_by='Me',
            ),
            Transaction(
                person_id=charlie.id,
                date=datetime.date(2019, 4, 27),
                method='Credit',
                amount=6,
                accepted_by='You',
            ),
            Transaction(
                person_id=charlie.id,
                date=datetime.date(2019, 4, 27),
                method='Credit',
                amount=72,
                accepted_by='Me',
            ),
        ]
    )

    # Commit the changes for the users
    db.session.commit()

    yield

    db.drop_all()
