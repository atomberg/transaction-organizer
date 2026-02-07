"""Helper script to create database tables."""

from models.db_session import Base, engine

from app.models.person import Person
from app.models.transaction import Transaction

_ = (Person, Transaction)

Base.metadata.create_all(engine)
