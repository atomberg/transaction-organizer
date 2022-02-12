from fastapi import APIRouter, Depends
from ..dependencies import get_db
from sqlalchemy.orm import Session

from ..crud import get_categories, get_suppliers, guess_category

router = APIRouter()


@router.get('/supplier')
def supplier(q: str = '', db: Session = Depends(get_db)):
    return [s for s in get_suppliers(db) if q in s]


@router.get('/category')
def category(q: str = '', db: Session = Depends(get_db)):
    return [s for s in get_categories(db) if q in s]


@router.get('/category/guess')
def category_guess(q: str = '', db: Session = Depends(get_db)):
    return {'category': guess_category(db, q)}
