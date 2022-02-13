from functools import lru_cache
from .database import SessionLocal
from .config import Settings


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@lru_cache()
def get_settings():
    return Settings()
