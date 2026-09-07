import asyncio
from aiohttp import ClientError
import json
from urllib.parse import quote_plus
from typing import List
from fastapi import APIRouter, Depends
from app import schemas
from app.config import settings
import redis
from app import utils

red = redis.Redis(host="localhost", port=6379, decode_responses=True)

router = APIRouter(prefix="/movies", tags=["All movies list"])


# Public and stateless: no database session is opened, so the list answers before
# Postgres exists and has no user rows it could leak.
@router.get("/", response_model=List[schemas.MovieResponse])
async def get_movies(params: schemas.MovieSearch = Depends()):
    headers = {
        "accept": "application/json",
        "Authorization": f"Bearer {settings.AUTHORIZATION}",
    }

    # The query belongs in the key: otherwise a search reads back the popular list.
    cache_key = f"TMDB_result:{params.query}:{params.page}"
    cached_result = red.get(cache_key)
    if cached_result:
        result = json.loads(cached_result)
        print("Returning cached data")
    else:
        # No query means the home page, and discover answers "what is popular now".
        if params.query:
            url = (
                f"{settings.TMDB_URL}search/movie?"
                f"query={quote_plus(params.query)}&page={params.page}"
            )
        else:
            url = f"{settings.TMDB_URL}discover/movie?page={params.page}"
        try:
            result = await utils.fetch_data(url, headers=headers)

            red.set(cache_key, json.dumps(result), ex=36000)
            print("Fetching new data from TMDB API")
        except ClientError as e:
            print(f"Error fetching TMDB data: {e}")
            return []  # Return an empty list instead of failing completely
        except ValueError:
            print("Invalid JSON response from TMDB API")
            return []

    res = result["results"]
    film_list = []
    tasks = []

    for movie in res:
        tmdb_id = movie["id"]
        task = utils.get_movie_details(tmdb_id, headers)
        tasks.append(task)
        film_list.append(
            {
                "tmdb_id": tmdb_id,
                "title": movie["original_title"],
                "release_date": movie["release_date"],
                # TMDB sends the key with a null value when a title has no poster.
                "poster_path": movie.get("poster_path"),
            }
        )

    movie_details = await asyncio.gather(*tasks)
    for i, (imdb_id, imdb_rating) in enumerate(movie_details):
        film_list[i]["imdb_id"] = imdb_id
        film_list[i]["imdb_rating"] = imdb_rating

    return film_list
