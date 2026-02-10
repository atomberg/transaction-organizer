"""Tax receipt models and issuance helpers."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app import db


class TaxReceipt(db.Model):
    """Model for issued tax receipts."""

    __tablename__ = 'tax_receipts'
    id = Column(Integer, primary_key=True)
    receipt_number = Column(String, nullable=False, unique=True)
    receipt_type = Column(String, nullable=False)
    person_id = Column(Integer, ForeignKey('persons.id'), nullable=False)
    tax_year = Column(Integer, nullable=False)
    issued_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    issued_by_user_id = Column(Integer)
    name_snapshot = Column(String, nullable=False)
    address_snapshot = Column(String)
    org_snapshot = Column(String, nullable=False)
    treasurer_snapshot = Column(String, nullable=False)
    total_amount = Column(Float, nullable=False)
    pdf_path = Column(String)
    voided_at = Column(DateTime)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    items = relationship('TaxReceiptItem', backref='tax_receipt', cascade='all, delete-orphan')

    @classmethod
    def get_by_id(cls, receipt_id):
        return db.session.get(cls, receipt_id)


class TaxReceiptItem(db.Model):
    """Model linking issued receipts to transactions."""

    __tablename__ = 'tax_receipt_items'
    id = Column(Integer, primary_key=True)
    tax_receipt_id = Column(Integer, ForeignKey('tax_receipts.id'), nullable=False)
    transaction_id = Column(Integer, ForeignKey('transactions.id'), nullable=False, unique=True)
    amount = Column(Float, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)


def get_receipts_for_person(person_id, tax_year=None):
    """Fetch issued receipts for one person, optionally filtered by year."""
    query = TaxReceipt.query.filter_by(person_id=person_id).filter(TaxReceipt.voided_at.is_(None))
    if tax_year is not None:
        query = query.filter(TaxReceipt.tax_year == tax_year)
    return query.order_by(TaxReceipt.issued_at.desc()).all()


def issue_single_transaction_receipt(transaction, org, treasurer):
    """Issue or reuse a receipt for a single transaction."""
    org = org or 'Unknown organisation'
    treasurer = treasurer or 'Unknown treasurer'

    existing_item = TaxReceiptItem.query.filter_by(transaction_id=transaction.id).first()
    if existing_item is not None and existing_item.tax_receipt.voided_at is None:
        return existing_item.tax_receipt

    person = transaction.person
    receipt = TaxReceipt(
        receipt_number=f'{person.id}-{transaction.id}',
        receipt_type='single_transaction',
        person_id=person.id,
        tax_year=transaction.date.year,
        name_snapshot=person.full_name,
        address_snapshot=person.address,
        org_snapshot=org,
        treasurer_snapshot=treasurer,
        total_amount=transaction.amount,
    )
    db.session.add(receipt)
    db.session.flush()

    db.session.add(
        TaxReceiptItem(
            tax_receipt_id=receipt.id,
            transaction_id=transaction.id,
            amount=transaction.amount,
        )
    )
    transaction.receipt = True
    db.session.add(transaction)
    db.session.commit()
    return receipt


def issue_annual_person_receipt(person, tax_year, org, treasurer):
    """Issue or reuse an annual receipt for one person and year."""
    org = org or 'Unknown organisation'
    treasurer = treasurer or 'Unknown treasurer'

    existing = (
        TaxReceipt.query.filter_by(
            person_id=person.id,
            tax_year=tax_year,
            receipt_type='annual_person',
        )
        .filter(TaxReceipt.voided_at.is_(None))
        .order_by(TaxReceipt.issued_at.desc())
        .first()
    )
    if existing is not None:
        return existing

    eligible = [t for t in person.transactions if t.date.year == tax_year and not t.receipt]
    if not eligible:
        raise ValueError('No eligible transactions found for this person and tax year.')

    receipt = TaxReceipt(
        receipt_number=f'{person.id}-Y{tax_year}',
        receipt_type='annual_person',
        person_id=person.id,
        tax_year=tax_year,
        name_snapshot=person.full_name,
        address_snapshot=person.address,
        org_snapshot=org,
        treasurer_snapshot=treasurer,
        total_amount=sum(t.amount for t in eligible),
    )
    db.session.add(receipt)
    db.session.flush()

    for transaction in eligible:
        db.session.add(
            TaxReceiptItem(
                tax_receipt_id=receipt.id,
                transaction_id=transaction.id,
                amount=transaction.amount,
            )
        )
        transaction.receipt = True
        db.session.add(transaction)

    db.session.commit()
    return receipt
