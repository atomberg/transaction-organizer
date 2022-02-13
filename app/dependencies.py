# from functools import lru_cache
from .database import SessionLocal
from .config import settings, Settings


def get_settings() -> Settings:
    return settings


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
