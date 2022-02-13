import csv
import io
from datetime import date, datetime
from sqlalchemy.orm import Session
from typing import Optional, List

from ..models.transaction import Transaction
from ..schemas import TransactionCreate


def create_transaction(db: Session, transaction: TransactionCreate) -> Transaction:
    """Create a new transaction."""
    t = Transaction(
        person_id=transaction.person_id,
        date=transaction.date,
        method=transaction.method,
        amount=transaction.amount,
        accepted_by=transaction.accepted_by,
        memo=transaction.memo,
    )
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


def get_accepted_bys(db: Session):
    return [
        r.accepted_by for r in db.query(Transaction).with_entities(Transaction.accepted_by).distinct().all()
    ]


def get_as_csv():
    with io.StringIO() as buffer:
        fieldnames = [
            'id',
            'person_id',
            'date',
            'method',
            'amount',
            'accepted_by',
            'memo',
            'created_at',
            'updated_at',
        ]
        writer = csv.DictWriter(buffer, fieldnames=fieldnames, extrasaction='ignore')

        writer.writeheader()
        for t in get_transactions(reverse=True):
            writer.writerow(t.__dict__)
        return buffer.getvalue()


def to_dict(t: Transaction):
    return {
        'id': t.id,
        'person_id': t.person_id,
        'person': t.person.full_name,
        'date': t.date.strftime('%Y-%m-%d'),
        'method': t.method,
        'amount': t.amount,
        'accepted_by': t.accepted_by,
        'last_modified': t.updated_at.strftime('%c'),
        'created_at': t.created_at.strftime('%c'),
        'memo': t.memo or '',
        'receipt': t.receipt,
    }
