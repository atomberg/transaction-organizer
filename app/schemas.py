from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel


class TransactionBase(BaseModel):
    date: date
    supplier: str
    amount: float
    category: Optional[str]


class TransactionCreate(TransactionBase):
    pass


class TransactionUpdate(TransactionBase):
    notes: Optional[str]


class Transaction(TransactionBase):
    id: int
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime
