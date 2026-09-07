from datetime import date

from sqlalchemy import ForeignKey, MetaData, UniqueConstraint, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

# Without this, Postgres invents its own names for constraints and Alembic cannot
# drop what it did not name. The pattern makes every migration reproducible.
NAMING_CONVENTION = {
    "ix": "ix_%(table_name)s_%(column_0_name)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=NAMING_CONVENTION)


class User(Base):
    """A registered account: the owner of every saved film."""

    __tablename__ = "users"

    user_id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(unique=True)
    password: Mapped[str]
    first_name: Mapped[str]
    last_name: Mapped[str]
    # current_date and not now(): the column is a DATE, and a timestamp default
    # is what SQLite hands back as an unparsable string in the tests.
    user_created_at: Mapped[date] = mapped_column(server_default=func.current_date())


class Favorite(Base):
    """A film the user liked."""

    __tablename__ = "favorites"

    id: Mapped[int] = mapped_column(primary_key=True)
    # CASCADE: deleting the account takes its lists with it, in one statement.
    user_id: Mapped[int] = mapped_column(ForeignKey("users.user_id", ondelete="CASCADE"))
    tmdb_id: Mapped[int]
    title: Mapped[str]
    # TMDB leaves it empty for a film with no announced date yet.
    release_date: Mapped[date | None]
    # Stored, not looked up again: the saved pages draw the same poster
    # without a second trip to TMDB for a film the user already picked.
    poster_path: Mapped[str | None]
    # Null for a film OMDB does not carry; the row is still a valid entry.
    imdb_id: Mapped[str | None]
    imdb_rating: Mapped[float | None]

    # One row per film per user: the pair is unique, neither half on its own.
    __table_args__ = (
        UniqueConstraint("user_id", "tmdb_id", name="uq_favorites_user_movie"),
    )


class WatchLater(Base):
    """A film the user plans to watch."""

    __tablename__ = "watch_later"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.user_id", ondelete="CASCADE"))
    tmdb_id: Mapped[int]
    title: Mapped[str]
    # TMDB leaves it empty for a film with no announced date yet.
    release_date: Mapped[date | None]
    # Stored, not looked up again: the saved pages draw the same poster
    # without a second trip to TMDB for a film the user already picked.
    poster_path: Mapped[str | None]
    imdb_id: Mapped[str | None]
    imdb_rating: Mapped[float | None]

    __table_args__ = (
        UniqueConstraint("user_id", "tmdb_id", name="uq_watch_later_user_movie"),
    )
