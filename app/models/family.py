"""Family/household models for grouped donor management."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, UniqueConstraint, event, func, select, text
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import relationship

from app import db


class Family(db.Model):
    """Household/family entity that can receive aggregated receipts."""

    __tablename__ = 'families'
    id = Column(Integer, primary_key=True)
    display_name = Column(String, nullable=False)
    address = Column(String)
    notes = Column(String)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    deleted_at = Column(DateTime)

    members = relationship('FamilyMember', backref='family', cascade='all, delete-orphan')

    @hybrid_property
    def member_count(self):
        return len([member for member in self.members if member.deleted_at is None])

    def to_dict(self):
        return {
            'id': self.id,
            'display_name': self.display_name,
            'address': self.address or '',
            'notes': self.notes or '',
            'member_count': self.member_count,
        }

    @classmethod
    def get_by_id(cls, family_id):
        return db.session.get(cls, family_id)


class FamilyMember(db.Model):
    """Membership link between people and family entities."""

    __tablename__ = 'family_members'
    __table_args__ = (
        UniqueConstraint('family_id', 'person_id', name='uq_family_member_family_person'),
        db.Index(
            'uq_family_member_active_person',
            'person_id',
            unique=True,
            sqlite_where=text('deleted_at IS NULL'),
        ),
    )
    id = Column(Integer, primary_key=True)
    family_id = Column(Integer, ForeignKey('families.id'), nullable=False)
    person_id = Column(Integer, ForeignKey('persons.id'), nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    deleted_at = Column(DateTime)

    person = relationship('Person', backref='family_memberships')


def get_families():
    return Family.query.filter(Family.deleted_at.is_(None)).order_by(Family.updated_at.desc()).all()


def _validate_membership_limits(connection, membership, is_update=False):
    if membership.deleted_at is not None:
        return

    family_members = FamilyMember.__table__

    count_stmt = (
        select(func.count())
        .select_from(family_members)
        .where(
            family_members.c.family_id == membership.family_id,
            family_members.c.deleted_at.is_(None),
        )
    )
    if is_update and membership.id is not None:
        count_stmt = count_stmt.where(family_members.c.id != membership.id)

    active_in_family = connection.execute(count_stmt).scalar_one()
    if active_in_family >= 2:
        raise ValueError('Family cannot have more than 2 active members.')

    person_stmt = (
        select(func.count())
        .select_from(family_members)
        .where(
            family_members.c.person_id == membership.person_id,
            family_members.c.deleted_at.is_(None),
        )
    )
    if is_update and membership.id is not None:
        person_stmt = person_stmt.where(family_members.c.id != membership.id)

    active_for_person = connection.execute(person_stmt).scalar_one()
    if active_for_person >= 1:
        raise ValueError('Person can only belong to one active family.')


@event.listens_for(FamilyMember, 'before_insert')
def validate_family_member_before_insert(mapper, connection, target):
    _ = mapper
    _validate_membership_limits(connection, target, is_update=False)


@event.listens_for(FamilyMember, 'before_update')
def validate_family_member_before_update(mapper, connection, target):
    _ = mapper
    _validate_membership_limits(connection, target, is_update=True)
