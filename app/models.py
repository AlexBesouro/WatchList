from datetime import date, datetime
from enum import Enum as PyEnum
from sqlalchemy import Enum, TIMESTAMP, text, DATE, ForeignKey
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = "users"
    user_id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(nullable=False, unique=True)
    password: Mapped[str] = mapped_column(nullable=False)
    first_name: Mapped[str] = mapped_column( nullable=False)
    last_name: Mapped[str] = mapped_column(nullable=False)
    user_created_at: Mapped[datetime] = mapped_column(DATE, nullable=False, server_default=text("NOW()"))

class WatchedMovies(Base):
    __tablename__ = "watched movies"
    id: Mapped[int] = mapped_column(primary_key=True)
    tmdb_id: Mapped[int] = mapped_column(ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)