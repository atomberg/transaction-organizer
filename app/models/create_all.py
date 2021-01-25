from models.db_session import engine, Base

from app.models.person import Person
from app.models.transaction import Transaction

[Person, Transaction]

Base.metadata.create_all(engine)
