from db_session import engine, Session
from datetime import datetime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Float, Date, DateTime

Base = declarative_base()


class Transaction(Base):
    __tablename__ = 'transactions'
    id = Column(Integer, primary_key=True)
    date = Column(Date, nullable=False)
    supplier = Column(String, nullable=False)
    amount = Column(Float, nullable=False)
    category = Column(String)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)
    notes = Column(String)

    def __init__(self, date, supplier, amount, category=None, notes=None):
        self.date = date
        self.supplier = supplier
        self.amount = amount
        self.category = category
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
        self.notes = notes

    @classmethod
    def get_by_id(cls, id):
        return Session.query(Transaction).filter_by(id=id).one_or_none()

    def __str__(self):
        return '%s | %s | %2.2f | %s' % (self.date.strftime('%Y-%m-%d'), self.supplier, self.amount, self.category)


def get_categories():
    return [r[0] for r in Session.query(Transaction.category).distinct().all()]


def get_suppliers():
    return [r[0] for r in Session.query(Transaction.supplier).distinct().all()]


def get_transactions(limit=None):
    if not limit:
        return Session.query(Transaction.date, Transaction.supplier, Transaction.amount, Transaction.category).all()
    else:
        return (Session.query(
            Transaction.date, Transaction.supplier, Transaction.amount, Transaction.category)
            .order_by(Transaction.updated_at.desc()).limit(limit).all())[::-1]


Base.metadata.create_all(engine)
