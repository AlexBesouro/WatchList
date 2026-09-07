from fastapi import APIRouter, status

from app import movie_lists, schemas
from app.auth import CurrentUser
from app.database import DbSession
from app.models import WatchLater

router = APIRouter(prefix="/watch-later", tags=["Watch later"])


@router.get("")
def list_watch_later(db: DbSession, user: CurrentUser) -> list[schemas.SavedMovie]:
    """The films this user plans to watch."""
    return movie_lists.list_movies(db, user, WatchLater)


@router.post("", status_code=status.HTTP_201_CREATED)
def add_watch_later(
    movie: schemas.SavedMovie, db: DbSession, user: CurrentUser
) -> schemas.SavedMovie:
    """Add a film to this user's watch-later list."""
    return movie_lists.add_movie(db, user, WatchLater, movie)


@router.delete("/{tmdb_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_watch_later(tmdb_id: int, db: DbSession, user: CurrentUser) -> None:
    """Remove a film from this user's watch-later list."""
    movie_lists.remove_movie(db, user, WatchLater, tmdb_id)
