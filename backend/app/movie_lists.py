"""The logic behind the two saved lists: one table each, one code path for both."""

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app import models, schemas

# Favorites and watch-later hold the same columns and the same rules, so the
# table is a parameter here instead of a second copy of these three functions.
SavedTable = type[models.Favorite] | type[models.WatchLater]


def list_movies(db: Session, user: models.User, table: SavedTable) -> list:
    """Every film this user saved in `table`, oldest first."""
    return db.query(table).filter(table.user_id == user.user_id).order_by(table.id).all()


def add_movie(
    db: Session, user: models.User, table: SavedTable, movie: schemas.SavedMovie
):
    """Save a film for this user, or 409 when the list already holds it."""
    row = table(**movie.model_dump(), user_id=user.user_id)
    db.add(row)
    try:
        db.commit()
    except IntegrityError:
        # The unique constraint is what decides, not a SELECT first: two parallel
        # requests would both pass the check and only the constraint stops them.
        db.rollback()
        raise HTTPException(
            status.HTTP_409_CONFLICT, "This film is already in the list."
        ) from None
    db.refresh(row)
    return row


def remove_movie(db: Session, user: models.User, table: SavedTable, tmdb_id: int) -> None:
    """Drop a film from this user's list, or 404 when they never saved it."""
    row = (
        db.query(table)
        .filter(table.user_id == user.user_id, table.tmdb_id == tmdb_id)
        .first()
    )
    if row is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "This film is not in the list.")
    db.delete(row)
    db.commit()


# Every query above filters on user_id. Written once, it cannot be forgotten in
# one of the six handlers that call it.
