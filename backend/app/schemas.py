from datetime import date
from typing import Annotated

from pydantic import BaseModel, EmailStr, Field


class TokenResponse(BaseModel):
    access_token: str
    token_type: str


class UserCredentials(BaseModel):
    email: EmailStr
    password: str


class CreateUser(BaseModel):
    email: EmailStr
    password: str
    first_name: str
    last_name: str


class UserResponse(BaseModel):
    user_id: int
    email: EmailStr
    first_name: str
    last_name: str
    user_created_at: date


class MovieSearch(BaseModel):
    # Absent means "popular" and keeps the discover call. The constraint sits on str
    # rather than on the Optional, so None skips it: the client omits the parameter.
    query: Annotated[str, Field(min_length=3)] | None = None
    page: Annotated[int, Field(ge=1, le=500)] = 1


class MovieResponse(BaseModel):
    # No favorite flag: the endpoint is public and reads no user data at all, so the
    # front-end marks its own cards from GET /favorites/.
    tmdb_id: int
    title: str
    release_date: date
    # TMDB leaves this null for plenty of titles; the card falls back to a placeholder.
    poster_path: str | None = None
    # Echoed back on add: it is what links the row to OMDB.
    imdb_id: str | None
    imdb_rating: float | None


class WatchedMovie(BaseModel):
    tmdb_id: int
    title: str
    release_date: date
    imdb_id: str | None
    imdb_rating: float | None
    personal_rating: float

    class Config:
        from_attributes = True


class Favorite(BaseModel):
    tmdb_id: int
    title: str
    release_date: date
    # A film absent from OMDB has neither, and requiring them turned adding it into
    # a 422. The columns are nullable now, so the insert goes through.
    imdb_id: str | None = None
    imdb_rating: float | None = None

    class Config:
        from_attributes = True
