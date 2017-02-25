from db_session import engine, Session
from datetime import datetime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Float, Date, DateTime, func as sqlfunc, case
from sqlalchemy.ext.hybrid import hybrid_property


Base = declarative_base()
num_to_month_dict = {
    '01': 'Jan', '02': 'Feb', '03': 'Mar', '04': 'Apr', '05': 'May', '06': 'Jun',
    '07': 'Jul', '08': 'Aug', '09': 'Sep', '10': 'Oct', '11': 'Nov', '12': 'Dec'
}


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

    @hybrid_property
    def month(self):
        return self.date.strftime('%b')

    @month.expression
    def month(cls):
        return case(
            num_to_month_dict,
            value=sqlfunc.extract('month', cls.date),
            else_=None)

    def to_dict(self):
        return {
            'id': self.id,
            'date': self.date.strftime('%Y-%m-%d'),
            'supplier': self.supplier,
            'amount': '%.2f' % self.amount,
            'category': self.category,
            'last_modified': self.updated_at.strftime('%c'),
            'created_at': self.created_at.strftime('%c'),
            'notes': self.notes or ''
        }

    def to_table_row(self):
        return (self.id, self.date, self.supplier, self.amount, self.category)

    @classmethod
    def get_by_id(cls, id):
        return Session.query(Transaction).get(id)

    def __str__(self):
        return ' | '.join(
            ('#%d' % self.id, self.date.strftime('%d %b %Y'), self.supplier, '%.2f' % self.amount, self.category))


def get_categories():
    return [r[0] for r in Session.query(Transaction.category).distinct().all()]


def get_suppliers():
    return [r[0] for r in Session.query(Transaction.supplier).distinct().all()]


def get_transactions(lim=None, reverse=False):
    q = Session.query(Transaction).order_by(Transaction.updated_at.desc()).limit(lim)
    q = q.all()
    if reverse:
        q = q[::-1]
    return [t.to_table_row() for t in q]


def pivot_transactions():
    q = Session.query(Transaction.month, Transaction.category, sqlfunc.sum(Transaction.amount))
    q = q.group_by(Transaction.month, Transaction.category)
    return dict([((m, c), a) for m, c, a in q.all()])


Base.metadata.create_all(engine)
