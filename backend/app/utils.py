import aiohttp
from passlib.context import CryptContext
from app.config import settings
import re
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")



def is_strong_password(password):
    if len(password) < 8:
        return False, "Password must be at least 8 characters long."
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter."
    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter."
    if not re.search(r'\d', password):
        return False, "Password must contain at least one digit."
    if not re.search(r'[!@#$%^&*(),.?":{}|<>_-]', password):
        return False, "Password must contain at least one special character."

    return True, "Password is strong."


def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


async def fetch_data(url: str, headers=None):
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers= headers) as response:
            response.raise_for_status()
            return await response.json()

async def get_movie_details(tmdb_id, headers):
    async with aiohttp.ClientSession() as session:
        imdb_id_response = await session.get(f"{settings.TMDB_URL}movie/{tmdb_id}/external_ids", headers=headers)
        try:
            imdb_id_data = await imdb_id_response.json()
        except ValueError:
            imdb_id_data = {}
        imdb_id = imdb_id_data.get("imdb_id", None)
        if imdb_id == "N/A":
            imdb_id = None

        imdb_rating_response = await session.get(f"{settings.OMDB_URL}?i={imdb_id}&apikey={settings.OMDB_API_KEY}")
        try:
            imdb_rating_data = await imdb_rating_response.json()
        except ValueError:
            imdb_rating_data = {}
        imdb_rating = imdb_rating_data.get("imdbRating", None)
        if imdb_rating == "N/A":
            imdb_rating = None

        return imdb_id, imdb_rating