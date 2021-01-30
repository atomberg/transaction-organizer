from datetime import datetime
from app import db
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.ext.hybrid import hybrid_property


class Person(db.Model):
    """Model of a person from the persons table in database."""

    __tablename__ = 'persons'
    id = Column(Integer, primary_key=True)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    phone = Column(String)
    email = Column(String)
    address = Column(String)
    transactions = relationship('Transaction', backref='person')
    notes = Column(String)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)
    deleted_at = Column(DateTime)

    def __init__(self, first_name, last_name, phone=None, email=None, address=None, notes=None):
        """Create a new person."""
        self.first_name = first_name
        self.last_name = last_name
        self.phone = phone
        self.email = email
        self.address = address
        self.notes = notes
        self.created_at = datetime.now()
        self.updated_at = datetime.now()

    @hybrid_property
    def full_name(self):
        return f'{self.last_name}, {self.first_name}'

    @hybrid_property
    def total(self):
        return sum([t.amount for t in self.transactions])

    def to_dict(self):
        return {
            'id': self.id,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'full_name': self.full_name,
            'phone': self.phone,
            'email': self.email,
            'address': self.address,
            'transactions': [t.to_dict() for t in self.transactions],
            'notes': self.notes or '',
            'last_modified': self.updated_at.strftime('%c'),
            'created_at': self.created_at.strftime('%c'),
        }

    @classmethod
    def get_by_id(cls, id):
        return cls.query.get(id)

    def __str__(self):
        """Human readable representation."""
        return f"#{self.id:d} {self.full_name} | {self.phone} | {self.email}"


def get_person_names():
    return [(r.id, r.full_name) for r in Person.query.filter(Person.deleted_at.is_(None)).all()]


def get_persons(lim=None, reverse=False):
    q = Person.query.filter(Person.deleted_at.is_(None))
    rows = q.order_by(Person.updated_at.desc()).limit(lim).all()
    if reverse:
        return rows[::-1]
    return rows
