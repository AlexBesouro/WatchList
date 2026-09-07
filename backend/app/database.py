from typing import Annotated

from fastapi import Depends
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.config import settings

SQLALCHEMY_DATABASE_URL = (
    f"postgresql://{settings.DATABASE_USERNAME}:{settings.DATABASE_PASSWORD}"
    f"@{settings.DATABASE_HOSTNAME}:{settings.DATABASE_PORT}/{settings.DATABASE_NAME}"
)

engine = create_engine(SQLALCHEMY_DATABASE_URL)

session_local = sessionmaker(autoflush=False, autocommit=False, bind=engine)


def get_db():
    """Open one session per request and close it whatever the handler does."""
    db = session_local()
    try:
        yield db
    finally:
        db.close()


DbSession = Annotated[Session, Depends(get_db)]
# Named once here so a handler writes `db: DbSession` instead of repeating the
# Depends() call, which ruff flags as a mutable default in every signature.
