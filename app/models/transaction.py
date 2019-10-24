from models.db_session import engine, Session
from datetime import datetime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Float, Date, DateTime, func as sqlfunc, desc
from sqlalchemy.ext.hybrid import hybrid_property


Base = declarative_base()


class Transaction(Base):
    """Model of a transaction from the transactions table in database."""

    __tablename__ = 'transactions'
    id = Column(Integer, primary_key=True)
    date = Column(Date, nullable=False)
    supplier = Column(String, nullable=False)
    amount = Column(Float, nullable=False)
    category = Column(String)
    notes = Column(String)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)

    def __init__(self, date, supplier, amount, category=None, notes=''):
        """Create a new transaction."""
        self.date = date
        self.supplier = supplier
        self.amount = amount
        self.category = category
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
        self.notes = notes

    @hybrid_property
    def month(self):
        return self.date.strftime('%m')

    @month.expression
    def month(self):
        return sqlfunc.extract('month', self.date)

    @hybrid_property
    def year(self):
        return self.date.strftime('%Y')

    @year.expression
    def year(self):
        return sqlfunc.extract('year', self.date)

    @classmethod
    def get_by_id(cls, id):
        return Session.query(cls).get(id)

    def __str__(self):
        return ' | '.join(
            ('#%d' % self.id, self.date.strftime('%d %b %Y'), self.supplier, '%.2f' % self.amount, self.category))


def get_categories():
    return [r.category for r in Session.query(Transaction.category).distinct().all()]


def get_suppliers():
    return [r.supplier for r in Session.query(Transaction.supplier).distinct().all()]


def get_transactions(lim=None, reverse=False, begin=None, end=None, month=None):
    q = Session.query(Transaction)
    if month:
        q = q.filter(Transaction.month == month).filter(Transaction.year == datetime.now().year)
    else:
        if begin and end:
            q = q.filter(Transaction.date.between(begin, end))
        elif begin:
            q = q.filter(Transaction.date >= begin)
        elif end:
            q = q.filter(Transaction.date <= end)
    rows = q.order_by(Transaction.updated_at.desc()).limit(lim).all()
    if reverse:
        return rows[::-1]
    return rows


def get_years():
    q = Session.query(Transaction.year).distinct().order_by(Transaction.year.desc())
    return [r.year for r in q.all()]


def pivot_transactions(year):
    q = Session.query(Transaction.month, Transaction.category, sqlfunc.sum(Transaction.amount))
    q = q.filter(Transaction.year == year)
    q = q.group_by(Transaction.month, Transaction.category)
    return dict([((m, c), a) for m, c, a in q.all()])


def guess_category(supplier):
    q = Session.query(Transaction.category, sqlfunc.count().label('count'))
    q = q.filter(Transaction.supplier == supplier)
    q = q.group_by(Transaction.category).order_by(desc('count')).limit(1)
    return q.scalar() or ''


Base.metadata.create_all(engine)
