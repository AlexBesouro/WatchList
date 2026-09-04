from datetime import date, datetime
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from typing import Annotated


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
    query: Optional[Annotated[str, Field(min_length=3)]] = None
    page: Annotated[int, Field(ge=1, le=500)] = 1


class MovieResponse(BaseModel):
    tmdb_id: int
    title: str
    release_date: date
    # TMDB leaves this null for plenty of titles; the card falls back to a placeholder.
    poster_path: Optional[str] = None
    # Echoed back on add: it is what links the row to OMDB.
    imdb_id: Optional[str]
    imdb_rating: Optional[float]
    # Computed here, not sent by TMDB: it answers "is it in this user's list".
    is_favorite: Optional[bool] = False


class WatchedMovie(BaseModel):
    tmdb_id: int
    title: str
    release_date: date
    imdb_id: Optional[str]
    imdb_rating: Optional[float]
    personal_rating: float

    class Config:
        from_attributes = True


class Favorite(BaseModel):
    tmdb_id: int
    title: str
    release_date: date
    # A film absent from OMDB has neither, and requiring them turned adding it into
    # a 422. The columns are nullable now, so the insert goes through.
    imdb_id: Optional[str] = None
    imdb_rating: Optional[float] = None

    class Config:
        from_attributes = True
