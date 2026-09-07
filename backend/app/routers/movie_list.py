import asyncio
import logging
from urllib.parse import quote_plus

from aiohttp import ClientError
from fastapi import APIRouter, Depends

from app import schemas, utils
from app.cache import cache_get, cache_set
from app.config import settings

log = logging.getLogger(__name__)

# TMDB refreshes its popular list slowly, so ten hours of cache costs nothing and
# saves forty-one upstream calls per page view.
CACHE_TTL = 36000

router = APIRouter(prefix="/movies", tags=["Movies"])


@router.get("")
async def get_movies(
    params: schemas.MovieSearch = Depends(),
) -> list[schemas.MovieResponse]:
    """The public film list: popular titles, or the results of a search."""
    # Public and stateless: no database session is opened, so the list answers
    # before Postgres exists and has no user rows it could leak.

    # The query belongs in the key: otherwise a search reads back the popular list.
    # `or ""` and not the raw value: an absent query renders as "None", and a
    # search for the word None would then build the very same key.
    cache_key = f"movies:{params.query or ''}:{params.page}"

    # What is cached is the finished list, not the TMDB page it was built from.
    # Enriching costs two upstream calls per film, so caching the page instead
    # would save one request out of forty-one.
    cached = cache_get(cache_key)
    if cached is not None:
        return cached

    headers = {
        "accept": "application/json",
        "Authorization": f"Bearer {settings.AUTHORIZATION}",
    }

    # No query means the home page, and discover answers "what is popular now".
    if params.query:
        url = (
            f"{settings.TMDB_URL}search/movie?"
            f"query={quote_plus(params.query)}&page={params.page}"
        )
    else:
        url = f"{settings.TMDB_URL}discover/movie?page={params.page}"

    try:
        page = await utils.fetch_data(url, headers=headers)
    except (ClientError, ValueError):
        # An empty list and not a 500: TMDB being down is not a bug in this
        # service, and the page renders its "nothing found" state. Nothing is
        # cached here, or one bad minute would blank the home page for ten hours.
        log.warning("TMDB did not answer for %r", url)
        return []

    films = [
        {
            "tmdb_id": movie["id"],
            "title": movie["original_title"],
            # TMDB sends "" rather than null for an unannounced date.
            "release_date": movie.get("release_date") or None,
            # TMDB sends the key with a null value when a title has no poster.
            "poster_path": movie.get("poster_path"),
        }
        for movie in page["results"]
    ]

    # One round trip per film would be forty in a row; gather runs them at once.
    details = await asyncio.gather(
        *(utils.get_movie_details(film["tmdb_id"], headers) for film in films)
    )
    for film, (imdb_id, imdb_rating) in zip(films, details, strict=True):
        film["imdb_id"] = imdb_id
        film["imdb_rating"] = imdb_rating

    cache_set(cache_key, films, CACHE_TTL)
    return films
