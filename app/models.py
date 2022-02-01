from .database import Base

from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Date, DateTime, func as sqlfunc
from sqlalchemy.ext.hybrid import hybrid_property


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

    def __str__(self):
        return ' | '.join(
            (
                '#%d' % self.id,
                self.date.strftime('%d %b %Y'),
                self.supplier,
                '%.2f' % self.amount,
                self.category,
            )
        )
