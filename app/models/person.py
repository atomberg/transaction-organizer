from models.db_session import Session, Base
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime  # , func as sqlfunc, desc
from sqlalchemy.orm import relationship
from sqlalchemy.ext.hybrid import hybrid_property


class Person(Base):
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

    def to_table_row(self):
        return self.id, self.last_name, self.first_name, self.phone, self.email, bool(self.notes)

    @classmethod
    def get_by_id(cls, id):
        return Session.query(Person).get(id)

    def __str__(self):
        return (f"#{self.id:d} {self.last_name}, {self.first_name} | {self.phone} | {self.email}")


def get_persons():
    return [(r.id, r.full_name) for r in Session.query(Person).filter(Person.deleted_at.is_(None)).all()]


# def get_suppliers():
#     return [r.supplier for r in Session.query(Transaction.supplier).distinct().all()]


# def get_transactions(lim=None, reverse=False, begin=None, end=None, month=None):
#     q = Session.query(Transaction)
#     if month:
#         q = q.filter(Transaction.month == month).filter(Transaction.year == datetime.now().year)
#     else:
#         if begin and end:
#             q = q.filter(Transaction.date.between(begin, end))
#         elif begin:
#             q = q.filter(Transaction.date >= begin)
#         elif end:
#             q = q.filter(Transaction.date <= end)
#     q = q.order_by(Transaction.updated_at.desc()).limit(lim).all()
#     if reverse:
#         q = q[::-1]
#     return [t.to_table_row() for t in q]


# def get_years():
#     q = Session.query(Transaction.year).distinct().order_by(Transaction.year.desc())
#     return [r.year for r in q.all()]


# def pivot_transactions(year):
#     q = Session.query(Transaction.month, Transaction.category, sqlfunc.sum(Transaction.amount))
#     q = q.filter(Transaction.year == year)
#     q = q.group_by(Transaction.month, Transaction.category)
#     return dict([((m, c), a) for m, c, a in q.all()])


# def guess_category(supplier):
#     q = Session.query(Transaction.category, sqlfunc.count().label('count'))
#     q = q.filter(Transaction.supplier == supplier)
#     q = q.group_by(Transaction.category).order_by(desc('count')).limit(1)
#     return q.scalar() or ''
