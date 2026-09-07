from fastapi import APIRouter, status

from app import movie_lists, schemas
from app.auth import CurrentUser
from app.database import DbSession
from app.models import Favorite

router = APIRouter(prefix="/favorites", tags=["Favorites"])


@router.get("")
def list_favorites(db: DbSession, user: CurrentUser) -> list[schemas.SavedMovie]:
    """The films this user marked as favorites."""
    return movie_lists.list_movies(db, user, Favorite)


@router.post("", status_code=status.HTTP_201_CREATED)
def add_favorite(
    movie: schemas.SavedMovie, db: DbSession, user: CurrentUser
) -> schemas.SavedMovie:
    """Add a film to this user's favorites."""
    return movie_lists.add_movie(db, user, Favorite, movie)


@router.delete("/{tmdb_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_favorite(tmdb_id: int, db: DbSession, user: CurrentUser) -> None:
    """Remove a film from this user's favorites."""
    # tmdb_id and not id: the path carries the film's TMDB identifier, which is
    # what the front-end knows, never the primary key of our own row.
    movie_lists.remove_movie(db, user, Favorite, tmdb_id)
