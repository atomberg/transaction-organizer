from datetime import date, datetime
from sqlalchemy.orm import Session
from sqlalchemy import func as sqlfunc, desc
from typing import Optional, List, Dict, Tuple

from .models import Transaction
from .schemas import TransactionCreate


def create_transaction(db: Session, transaction: TransactionCreate) -> Transaction:
    """Create a new transaction."""
    t = Transaction(transaction.date, transaction.supplier, transaction.amount, transaction.category)
    db.add(t)
    db.commit()
    db.refresh(t)
    return t


def get_transactions(db: Session, skip: int = 0, limit: Optional[int] = None) -> List[Transaction]:
    """Get latest transactions."""
    q = db.query(Transaction)
    return q.order_by(Transaction.updated_at.desc()).offset(skip).limit(limit).all()


def get_transaction_by_id(db: Session, transaction_id: int) -> Transaction:
    """Get a transation by id."""
    return db.query(Transaction).filter(Transaction.id == transaction_id).first()


def get_transactions_between_dates(
    db: Session,
    begin: Optional[date] = None,
    end: Optional[date] = None,
    skip: int = 0,
    limit: Optional[int] = None,
) -> List[Transaction]:
    """Get all transations between two dates."""
    q = db.query(Transaction)
    if begin and end:
        q = q.filter(Transaction.date.between(begin, end))
    elif begin:
        q = q.filter(Transaction.date >= begin)
    elif end:
        q = q.filter(Transaction.date <= end)
    return q.order_by(Transaction.updated_at.desc()).offset(skip).limit(limit).all()


def get_transactions_by_month(
    db: Session, month: int, skip: int = 0, limit: Optional[int] = None
) -> List[Transaction]:
    """Get all transations in a specific month of the current year."""
    q = db.query(Transaction)
    q = q.filter(Transaction.month == month)
    q = q.filter(Transaction.year == datetime.now().year)
    return q.order_by(Transaction.updated_at.desc()).offset(skip).limit(limit).all()


def update_transaction(db: Session, transaction_id: int, new_values: TransactionCreate) -> Transaction:
    """Update transaction by id."""
    t = get_transaction_by_id(db, transaction_id)
    t.date = new_values.date
    t.supplier = new_values.supplier
    t.amount = new_values.amount
    t.category = new_values.category
    t.notes = new_values.notes
    t.updated_at = datetime.now()

    db.add(t)
    db.commit()
    db.refresh(t)
    return t


def remove_transaction(db: Session, transaction_id: int) -> Transaction:
    """Delete transaction by id."""
    t = get_transaction_by_id(db, transaction_id)
    db.delete(t)
    db.commit()
    return t


def get_categories(db: Session) -> List[str]:
    return [r.category for r in db.query(Transaction.category).distinct().all()]


def get_suppliers(db: Session) -> List[str]:
    return [r.supplier for r in db.query(Transaction.supplier).distinct().all()]


def get_years(db: Session) -> List[int]:
    q = db.query(Transaction.year).distinct().order_by(Transaction.year.desc())
    return [r.year for r in q.all()]


def pivot_transactions(db: Session, year: int) -> Dict[Tuple[int, str], float]:
    q = db.query(Transaction.month, Transaction.category, sqlfunc.sum(Transaction.amount))
    q = q.filter(Transaction.year == year)
    q = q.group_by(Transaction.month, Transaction.category)
    return dict([((m, c), a) for m, c, a in q.all()])


def guess_category(db: Session, supplier: str) -> str:
    q = db.query(Transaction.category, sqlfunc.count().label('count'))
    q = q.filter(Transaction.supplier == supplier)
    q = q.group_by(Transaction.category).order_by(desc('count')).limit(1)
    return q.scalar() or ''
