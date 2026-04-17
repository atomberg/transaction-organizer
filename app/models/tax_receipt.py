"""Tax receipt models and issuance helpers."""

from __future__ import annotations

from datetime import datetime
from typing import Iterable

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, UniqueConstraint, and_, or_
from sqlalchemy.orm import backref, relationship

from app import db


class TaxReceipt(db.Model):
    """Model for issued tax receipts."""

    __tablename__ = 'tax_receipts'
    id = Column(Integer, primary_key=True)
    receipt_number = Column(String, nullable=False, unique=True)
    receipt_type = Column(String, nullable=False)
    donor_id = Column(Integer, ForeignKey('persons.id'))
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
    __table_args__ = (
        UniqueConstraint('tax_receipt_id', 'transaction_id', name='uq_tax_receipt_item_receipt_txn'),
    )
    id = Column(Integer, primary_key=True)
    tax_receipt_id = Column(Integer, ForeignKey('tax_receipts.id'), nullable=False)
    transaction_id = Column(Integer, ForeignKey('transactions.id'), nullable=False)
    amount = Column(Float, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    transaction = relationship(
        'Transaction',
        backref=backref('tax_receipt_items'),
    )


def _next_receipt_number(base_prefix):
    """Return next sequential receipt number for a given base prefix."""
    existing_numbers = (
        db.session.query(TaxReceipt.receipt_number)
        .filter(TaxReceipt.receipt_number.like(f'{base_prefix}%'))
        .all()
    )

    used_sequences = []
    for (value,) in existing_numbers:
        if value == base_prefix:
            used_sequences.append(1)
            continue
        suffix_prefix = f'{base_prefix}-'
        if not value.startswith(suffix_prefix):
            continue
        suffix = value[len(suffix_prefix) :]
        if suffix.isdigit():
            used_sequences.append(int(suffix))

    next_sequence = (max(used_sequences) if used_sequences else 0) + 1
    return f'{base_prefix}-{next_sequence}'


def next_single_transaction_receipt_number(transaction):
    """Preview the next receipt number for a single transaction receipt."""
    return _next_receipt_number(f'{transaction.person_id}-{transaction.id}')


def next_annual_person_receipt_number(person_id, tax_year):
    """Preview the next receipt number for a person annual receipt."""
    return _next_receipt_number(f'{person_id}-Y{tax_year}')


def _active_receipt_item(transaction):
    for item in transaction.tax_receipt_items:
        if item.tax_receipt.voided_at is None:
            return item
    return None


def is_receipt_eligible(transaction):
    """Eligibility for new receipt issuance under active receipt model."""
    return _active_receipt_item(transaction) is None and not bool(transaction.receipt)


def sync_receipt_flag(transaction):
    """Sync transaction.receipt from active receipt records."""
    has_active = (
        db.session.query(TaxReceipt.id)
        .join(TaxReceiptItem)
        .filter(
            TaxReceiptItem.transaction_id == transaction.id,
            TaxReceipt.voided_at.is_(None),
        )
        .first()
        is not None
    )
    transaction.receipt = has_active
    db.session.add(transaction)


def _base_prefix_from_receipt_number(receipt_number):
    prefix, sep, suffix = receipt_number.rpartition('-')
    if sep and suffix.isdigit():
        return prefix
    return receipt_number


def _active_receipt_for_transaction(transaction_id):
    return (
        TaxReceipt.query.join(TaxReceiptItem)
        .filter(TaxReceiptItem.transaction_id == transaction_id, TaxReceipt.voided_at.is_(None))
        .order_by(TaxReceipt.issued_at.desc())
        .first()
    )


def get_receipts_for_person_ids(person_ids: Iterable[int], tax_year=None, include_voided=True):
    """Fetch issued receipts for multiple people, optionally filtered by year."""
    ids = [person_id for person_id in set(person_ids) if person_id is not None]
    if not ids:
        return []
    query = TaxReceipt.query.filter(
        or_(
            TaxReceipt.donor_id.in_(ids),
            and_(TaxReceipt.donor_id.is_(None), TaxReceipt.person_id.in_(ids)),
        )
    )
    if not include_voided:
        query = query.filter(TaxReceipt.voided_at.is_(None))
    if tax_year is not None:
        query = query.filter(TaxReceipt.tax_year == tax_year)
    return query.order_by(TaxReceipt.issued_at.desc()).all()


def issue_single_transaction_receipt(transaction, org, treasurer):
    """Issue or reuse a receipt for a single transaction."""
    org = org or 'Unknown organisation'
    treasurer = treasurer or 'Unknown treasurer'

    existing = _active_receipt_for_transaction(transaction.id)
    if existing is not None:
        return existing

    person = transaction.person
    receipt = TaxReceipt(
        receipt_number=next_single_transaction_receipt_number(transaction),
        receipt_type='single_transaction',
        donor_id=person.id,
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
    db.session.flush()
    sync_receipt_flag(transaction)
    db.session.commit()
    return receipt


def issue_annual_donor_receipt(
    recipient_person,
    contributor_people,
    tax_year,
    org,
    treasurer,
    recipient_name=None,
    recipient_address=None,
):
    """Issue or reuse an annual donor-family receipt for one tax year."""
    org = org or 'Unknown organisation'
    treasurer = treasurer or 'Unknown treasurer'

    existing = (
        TaxReceipt.query.filter_by(
            person_id=recipient_person.id,
            tax_year=tax_year,
            receipt_type='annual_donor',
        )
        .filter(TaxReceipt.voided_at.is_(None))
        .order_by(TaxReceipt.issued_at.desc())
        .first()
    )
    if existing is not None:
        return existing

    eligible = []
    for contributor in contributor_people:
        eligible.extend(
            [
                transaction
                for transaction in contributor.transactions
                if transaction.date.year == tax_year and is_receipt_eligible(transaction)
            ]
        )
    if not eligible:
        raise ValueError('No eligible transactions found for this donor family and tax year.')

    receipt = TaxReceipt(
        receipt_number=next_annual_person_receipt_number(recipient_person.id, tax_year),
        receipt_type='annual_donor',
        donor_id=recipient_person.id,
        person_id=recipient_person.id,
        tax_year=tax_year,
        name_snapshot=recipient_name or recipient_person.full_name,
        address_snapshot=recipient_address or recipient_person.address,
        org_snapshot=org,
        treasurer_snapshot=treasurer,
        total_amount=sum(transaction.amount for transaction in eligible),
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
    db.session.flush()
    for transaction in eligible:
        sync_receipt_flag(transaction)

    db.session.commit()
    return receipt


def void_receipt(receipt):
    """Void an active receipt and update transaction receipt flags."""
    if receipt.voided_at is not None:
        return receipt
    receipt.voided_at = datetime.utcnow()
    receipt.updated_at = datetime.utcnow()
    db.session.add(receipt)

    for item in receipt.items:
        sync_receipt_flag(item.transaction)

    db.session.commit()
    return receipt


def reissue_receipt(receipt, org=None, treasurer=None):
    """Void a receipt and create a new active replacement with same transactions."""
    if receipt.voided_at is None:
        void_receipt(receipt)

    org_value = org or receipt.org_snapshot or 'Unknown organisation'
    treasurer_value = treasurer or receipt.treasurer_snapshot or 'Unknown treasurer'

    transactions = [item.transaction for item in receipt.items]
    ineligible = [txn.id for txn in transactions if not is_receipt_eligible(txn)]
    if ineligible:
        raise ValueError(f'Transactions already receipted elsewhere: {ineligible}')

    replacement = TaxReceipt(
        receipt_number=_next_receipt_number(_base_prefix_from_receipt_number(receipt.receipt_number)),
        receipt_type=receipt.receipt_type,
        donor_id=receipt.donor_id,
        person_id=receipt.person_id,
        tax_year=receipt.tax_year,
        name_snapshot=receipt.name_snapshot,
        address_snapshot=receipt.address_snapshot,
        org_snapshot=org_value,
        treasurer_snapshot=treasurer_value,
        total_amount=receipt.total_amount,
    )
    db.session.add(replacement)
    db.session.flush()

    for item in receipt.items:
        db.session.add(
            TaxReceiptItem(
                tax_receipt_id=replacement.id,
                transaction_id=item.transaction_id,
                amount=item.amount,
            )
        )
    db.session.flush()
    for item in receipt.items:
        sync_receipt_flag(item.transaction)

    db.session.commit()
    return replacement
