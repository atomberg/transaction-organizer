from datetime import datetime
from sqlalchemy import Column, ForeignKey, Integer, String, Float, Date, DateTime, Boolean, func as sqlfunc
from sqlalchemy.ext.hybrid import hybrid_property

from ..database import Base


class Transaction(Base):
    """Model of a transaction from the transactions table in database."""

    __tablename__ = 'transactions'
    id = Column(Integer, primary_key=True)
    person_id = Column(Integer, ForeignKey('persons.id'), nullable=False)
    date = Column(Date, nullable=False)
    method = Column(String, nullable=False)
    amount = Column(Float, nullable=False)
    accepted_by = Column(String, nullable=False)
    receipt = Column(Boolean)
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
        self.memo = memo
        self.created_at = datetime.now()
        self.updated_at = datetime.now()

    @hybrid_property
    def year(self) -> str:
        return self.date.strftime('%Y')

    @year.expression
    def year(self) -> int:
        return sqlfunc.extract('year', self.date)

    def __str__(self) -> str:
        """Human readable representation."""
        return (
            f"#{self.id:d} | {self.date.strftime('%d %b %Y')} | "
            f"{self.method} | {self.amount:.2f} | {self.accepted_by}"
        )
