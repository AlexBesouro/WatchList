from datetime import date, datetime

from pydantic import BaseModel, EmailStr
from typing_extensions import Optional


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
    page: int

class MovieResponse(BaseModel):
    tmdb_id: int
    title: str
    release_date: date
    imdb_id: str
    imdb_rating: str
    already_seen: Optional[bool] = False
    personal_rating: Optional[float] = 0
    watch_later: Optional[bool] = False
