from datetime import date, datetime
from pydantic import BaseModel, EmailStr, Field
from typing_extensions import Optional
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
    primary_release_year: int
    original_language: str
    page: Annotated[int, Field(ge=1, le=500)]


class MovieResponse(BaseModel):
    tmdb_id: int
    title: str
    release_date: date
    imdb_id: Optional[str]
    imdb_rating: Optional[float]
    already_seen: Optional[bool] = False
    personal_rating: Optional[float] = 0
    watch_later: Optional[bool] = False


class WatchedMovie(BaseModel):
    tmdb_id: int
    title: str
    release_date: date
    imdb_id: Optional[str]
    imdb_rating: Optional[float]
    personal_rating: float

    class Config:
        from_attributes = True


# CORRECTIONS AFTER INTERVIEW
# IN MODEL FIELDS imdb_id AND imdb_rating ARE NOT NULLUBLE, SO OPTIONAL FIELD CAN'T BE USED
class ToBeWatched(BaseModel):
    tmdb_id: int
    title: str
    release_date: date
    # imdb_id: Optional[str]
    # imdb_rating: Optional[float]
    imdb_id: str
    imdb_rating: float
