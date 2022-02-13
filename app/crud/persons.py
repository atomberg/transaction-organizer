from datetime import datetime
from sqlalchemy.orm import Session
from typing import Optional, List

from ..models.person import Person
from ..schemas import PersonCreate, PersonUpdate


def create_person(db: Session, person: PersonCreate) -> Person:
    """Create a new transaction."""
    t = Person(
        first_name=person.first_name,
        last_name=person.last_name,
        phone=person.phone,
        email=person.email,
        address=person.address,
        notes=person.notes,
    )
    db.add(t)
    db.commit()
    db.refresh(t)
    return t


def get_persons(db: Session, skip: int = 0, limit: Optional[int] = None) -> List[Person]:
    """Get persons."""
    q = db.query(Person).filter(Person.deleted_at.is_(None))
    return q.order_by(Person.updated_at.desc()).offset(skip).limit(limit).all()


def get_person_by_id(db: Session, person_id: int) -> Person:
    """Get a person by id."""
    return db.query(Person).filter(Person.id == person_id).first()


def update_person(db: Session, person_id: int, new_values: PersonUpdate) -> Person:
    """Update person by id."""
    p = get_person_by_id(db, person_id)
    p.date = new_values.date
    p.supplier = new_values.supplier
    p.amount = new_values.amount
    p.category = new_values.category
    p.notes = new_values.notes
    p.updated_at = datetime.now()

    db.add(p)
    db.commit()
    db.refresh(p)
    return p


def remove_person(db: Session, person_id: int) -> Person:
    """Delete person by id."""
    p = get_person_by_id(db, person_id)
    db.delete(p)
    db.commit()
    return p


def get_person_names(db):
    """Get a list of person (id, full_name) tuples."""
    return [(r.id, r.full_name) for r in db.query(Person).filter(Person.deleted_at.is_(None)).all()]
