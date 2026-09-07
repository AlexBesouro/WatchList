from datetime import date
from typing import Annotated

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class Health(BaseModel):
    """What GET /health answers: the process, and what it can reach."""

    status: str
    database: str
    cache: str


class TokenResponse(BaseModel):
    """What POST /login/ hands back: the bearer token and its type."""

    access_token: str
    token_type: str


class UserCredentials(BaseModel):
    """The sign-in body."""

    email: EmailStr
    password: str


class CreateUser(BaseModel):
    """The sign-up body. The password policy is checked in the router, not here."""

    email: EmailStr
    password: str
    first_name: str
    last_name: str


class UserResponse(BaseModel):
    """A user as the API shows it — note that `password` is absent by design."""

    model_config = ConfigDict(from_attributes=True)

    user_id: int
    email: EmailStr
    first_name: str
    last_name: str
    user_created_at: date


class MovieSearch(BaseModel):
    """The query string of GET /movies/, validated before TMDB is called."""

    # Absent means "popular" and keeps the discover call. The constraint sits on
    # str rather than on the union, so None skips it: the client omits it.
    query: Annotated[str, Field(min_length=3)] | None = None
    page: Annotated[int, Field(ge=1, le=500)] = 1


class MovieResponse(BaseModel):
    """One film in the public list."""

    # No "saved" flag: the endpoint is public and reads no user data at all, so
    # the front-end marks its own cards from the two private lists.
    tmdb_id: int
    title: str
    # Empty at TMDB for an unreleased film, so the card prints a dash.
    release_date: date | None = None
    # TMDB leaves this null for plenty of titles; the card falls back to a placeholder.
    poster_path: str | None = None
    imdb_id: str | None = None
    imdb_rating: float | None = None


class SavedMovie(BaseModel):
    """One film in a saved list: the body when adding, the item when reading."""

    # Both lists hold the same shape, so both routers answer with this schema.
    model_config = ConfigDict(from_attributes=True)

    tmdb_id: int
    title: str
    release_date: date | None = None
    poster_path: str | None = None
    # A film absent from OMDB has neither, and requiring them turned adding it
    # into a 422. The columns are nullable, so the insert goes through.
    imdb_id: str | None = None
    imdb_rating: float | None = None
