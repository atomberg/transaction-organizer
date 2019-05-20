from models.db_session import Session, Base
from datetime import datetime
from sqlalchemy import Column, ForeignKey, Integer, String, Float, Date, DateTime, func as sqlfunc, desc
from sqlalchemy.ext.hybrid import hybrid_property


class Transaction(Base):
    """Model of a transaction from the transactions table in database."""

    __tablename__ = 'transactions'
    id = Column(Integer, primary_key=True)
    person_id = Column(Integer, ForeignKey('persons.id'), nullable=False)
    date = Column(Date, nullable=False)
    method = Column(String, nullable=False)
    amount = Column(Float, nullable=False)
    accepted_by = Column(String, nullable=False)
    memo = Column(String)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)
    deleted_at = Column(DateTime)

    def __init__(self, person_id, date, method, amount, accepted_by, memo=None):
        """Create a new transaction."""
        self.person_id = person_id
        self.date = date
        self.method = method
        self.amount = amount
        self.accepted_by = accepted_by
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
        self.memo = memo

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

    def to_dict(self):
        return {
            'id': self.id,
            'person_id': self.person_id,
            'person': self.person.full_name,
            'date': self.date.strftime('%Y-%m-%d'),
            'method': self.method,
            'amount': self.amount,
            'accepted_by': self.accepted_by,
            'last_modified': self.updated_at.strftime('%c'),
            'created_at': self.created_at.strftime('%c'),
            'memo': self.memo or ''
        }

    def to_table_row(self):
        return self.id, self.person.full_name, self.date, self.method, self.amount, self.accepted_by, bool(self.memo)

    @classmethod
    def get_by_id(cls, id):
        return Session.query(Transaction).get(id)

    def __str__(self):
        return (
            f"#{self.id:d} | {self.date.strftime('%d %b %Y')} | {self.method} | {self.amount:.2f} | {self.accepted_by}"
        )


def get_methods():
    return [r.method for r in Session.query(Transaction.method).distinct().all()]


def get_accepted_bys():
    return [r.accepted_by for r in Session.query(Transaction.accepted_by).distinct().all()]


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
    q = q.order_by(Transaction.updated_at.desc()).limit(lim).all()
    if reverse:
        q = q[::-1]
    return [t.to_table_row() for t in q]


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
