from datetime import date, datetime
from typing import Optional
from xmlrpc.client import Boolean

from pydantic import BaseModel


class TransactionBase(BaseModel):
    date: date
    method: str
    amount: float
    accepted_by: str


class PersonBase(BaseModel):
    first_name: str
    last_name: str
    phone: Optional[str]
    email: Optional[str]
    address: Optional[str]
    notes: Optional[str]


class TransactionCreate(TransactionBase):
    pass


class TransactionUpdate(TransactionBase):
    memo: Optional[str]
    receipt: Optional[Boolean]


class Transaction(TransactionBase):
    id: int
    memo: Optional[str]
    receipt: Optional[Boolean]
    created_at: datetime
    updated_at: datetime
    person: PersonBase


class PersonCreate(PersonBase):
    pass


class PersonUpdate(PersonBase):
    notes: Optional[str]


class Person(PersonBase):
    id: int
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime
