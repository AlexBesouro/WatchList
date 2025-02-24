from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.config import settings

SQLALCHEMY_DATABASE_URL = (f"postgresql://{settings.DATABASE_USERNAME}:{settings.DATABASE_PASSWORD}@"
                           f"{settings.DATABASE_HOSTNAME}:{settings.DATABASE_PORT}/{settings.DATABASE_NAME}")

engine = create_engine(SQLALCHEMY_DATABASE_URL)

session_local = sessionmaker(autoflush=False, autocommit=False, bind=engine)


def get_db():
    db = session_local()
    try:
        yield db
    finally:
        db.close()