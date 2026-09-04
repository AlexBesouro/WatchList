from datetime import date, datetime
from enum import Enum as PyEnum
from typing import Optional
from sqlalchemy import Enum, TIMESTAMP, UniqueConstraint, text, DATE, ForeignKey
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"
    user_id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(nullable=False, unique=True)
    password: Mapped[str] = mapped_column(nullable=False)
    first_name: Mapped[str] = mapped_column(nullable=False)
    last_name: Mapped[str] = mapped_column(nullable=False)
    user_created_at: Mapped[datetime] = mapped_column(
        DATE, nullable=False, server_default=text("NOW()")
    )


# CORRECTIONS AFTER INTERVIEW
# composite unique index (UniqueConstraint).
class WatchedMovies(Base):
    __tablename__ = "watched movies"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False
    )
    tmdb_id: Mapped[int] = mapped_column(nullable=False)
    title: Mapped[str] = mapped_column(nullable=False)
    release_date: Mapped[datetime] = mapped_column(DATE, nullable=False)
    imdb_id: Mapped[str] = mapped_column(nullable=False)
    imdb_rating: Mapped[float] = mapped_column(nullable=False)
    personal_rating: Mapped[float] = mapped_column(nullable=False)
    __table_args__ = (UniqueConstraint("user_id", "tmdb_id", name="uq_watched_movie"),)


class Favorite(Base):
    __tablename__ = "favorites"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False
    )
    tmdb_id: Mapped[int] = mapped_column(nullable=False)
    title: Mapped[str] = mapped_column(nullable=False)
    release_date: Mapped[datetime] = mapped_column(DATE, nullable=False)
    # Null for a film OMDB does not carry; the row is still a valid favorite.
    imdb_id: Mapped[Optional[str]] = mapped_column(nullable=True)
    imdb_rating: Mapped[Optional[float]] = mapped_column(nullable=True)
    # One row per film per user: the pair is unique, neither half on its own.
    __table_args__ = (
        UniqueConstraint("user_id", "tmdb_id", name="uq_favorite_user_movie"),
    )
