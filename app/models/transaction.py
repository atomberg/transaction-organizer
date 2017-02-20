from app.models.db_session import engine, Session
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Float, Date

Base = declarative_base()


class Transaction(Base):
    __tablename__ = 'transactions'
    id = Column(Integer, primary_key=True)
    date = Column(Date, nullable=False)
    supplier = Column(String, nullable=False)
    amount = Column(Float, nullable=False)
    category = Column(String(250))

    def __init__(self, date, supplier, amount, category=None):
        self.date = date
        self.supplier = supplier
        self.amount = amount
        self.category = category

    @classmethod
    def get_by_id(cls, id):
        return Session.query(Transaction).filter_by(id=id).one_or_none()


def get_categories():
    return Session.query(Transaction.category).distinct().all()


def get_suppliers():
    return Session.query(Transaction.supplier).distinct().all()


Base.metadata.create_all(engine)
