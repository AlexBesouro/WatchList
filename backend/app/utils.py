import re

import aiohttp
from passlib.context import CryptContext

from app.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# The same five rules the sign-up form shows live. The server stays the
# authority: a client can be bypassed, this cannot.
PASSWORD_RULES = [
    (r".{8,}", "Password must be at least 8 characters long."),
    (r"[A-Z]", "Password must contain at least one uppercase letter."),
    (r"[a-z]", "Password must contain at least one lowercase letter."),
    (r"\d", "Password must contain at least one digit."),
    (
        r'[!@#$%^&*(),.?":{}|<>_-]',
        "Password must contain at least one special character.",
    ),
]


def is_strong_password(password: str) -> tuple[bool, str]:
    """(False, what is missing) on the first rule broken, (True, "") otherwise."""
    for pattern, message in PASSWORD_RULES:
        if not re.search(pattern, password):
            return False, message
    return True, ""


def hash_password(password: str) -> str:
    """The bcrypt hash to store. The plain password is never written anywhere."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Whether the password typed matches the stored hash."""
    return pwd_context.verify(plain_password, hashed_password)


async def fetch_data(url: str, headers: dict | None = None) -> dict:
    """GET `url` and return the decoded JSON, raising on any non-2xx answer."""
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            response.raise_for_status()
            return await response.json()


async def get_movie_details(
    tmdb_id: int, headers: dict
) -> tuple[str | None, float | None]:
    """The film's IMDb id from TMDB and its IMDb rating from OMDB, or (None, None)."""
    async with aiohttp.ClientSession() as session:
        imdb_id = await _read_json(
            session,
            f"{settings.TMDB_URL}movie/{tmdb_id}/external_ids",
            headers,
            "imdb_id",
        )
        if not imdb_id:
            # OMDB is looked up *by* the IMDb id, so without one there is nothing
            # to ask: the second call would return an error page we would ignore.
            return None, None

        rating = await _read_json(
            session,
            f"{settings.OMDB_URL}?i={imdb_id}&apikey={settings.OMDB_API_KEY}",
            None,
            "imdbRating",
        )
        return imdb_id, float(rating) if rating else None


async def _read_json(session, url: str, headers: dict | None, key: str) -> str | None:
    """One field out of a JSON answer, treating "N/A" and any failure as absent."""
    try:
        async with session.get(url, headers=headers) as response:
            data = await response.json()
    except (aiohttp.ClientError, ValueError):
        return None
    value = data.get(key)
    return None if value in (None, "N/A") else value
