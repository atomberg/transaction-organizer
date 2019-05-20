from models.db_session import engine, Base

from models.person import Person
from models.transaction import Transaction

[Person, Transaction]

Base.metadata.create_all(engine)
