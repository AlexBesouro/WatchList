import asyncio
import json
from typing import List
import aiohttp
from fastapi import APIRouter, Depends
from requests import RequestException
from sqlalchemy.orm import Session
from app import schemas, models
from app.config import settings
import redis
from app import utils
from app.database import get_db

red = redis.Redis(host='localhost', port=6379, decode_responses=True)

router = APIRouter(prefix="/movies", tags=["All movies list"])


@router.get("/", response_model= List[schemas.MovieResponse])
async def get_movies(params: schemas.MovieSearch, db: Session = Depends(get_db)):

    headers = {
        "accept": "application/json",
        "Authorization": f"Bearer {settings.AUTHORIZATION}"
    }

    cache_key = f"TMDB_result:{params.primary_release_year}:{params.original_language}:{params.page}"
    cached_result = red.get(cache_key)
    if cached_result:
        result = json.loads(cached_result)
        print("Returning cached data")
    else:
        try:
            result = await utils.fetch_data(f"{settings.TMDB_URL}discover/movie?"
                                    f"primary_release_year={params.primary_release_year}&"
                                    f"with_original_language={params.original_language}&"
                                    f"page={params.page}",
                                    headers=headers)

            red.set(cache_key, json.dumps(result), ex=36000)
            print("Fetching new data from TMDB API")
        except RequestException as e:
            print(f"Error fetching TMDB data: {e}")
            return []  # Return an empty list instead of failing completely
        except ValueError:
            print("Invalid JSON response from TMDB API")
            return []

    res = result["results"]
    film_list = []
    tasks = []
    watched_movies = db.query(models.WatchedMovies).all()
    watched_movies_dict = {movie.tmdb_id: movie for movie in watched_movies}
    to_be_watched_movies = db.query(models.ToBeWatched).all()
    to_be_watched_movies_set = {movie.tmdb_id for movie in to_be_watched_movies}


    for movie in res:
        tmdb_id = movie["id"]
        is_watched = watched_movies_dict.get(tmdb_id)
        watched_status = bool(is_watched)
        personal_rating = is_watched.personal_rating if is_watched else 0
        watch_later = tmdb_id in to_be_watched_movies_set

        task = utils.get_movie_details(tmdb_id, headers)
        tasks.append(task)
        film_list.append({"tmdb_id": tmdb_id,
                          "title" : movie["original_title"],
                          "release_date": movie["release_date"],
                          "already_seen": watched_status,
                          "personal_rating": personal_rating,
                          "watch_later": watch_later})

    movie_details = await asyncio.gather(*tasks)
    for i, (imdb_id, imdb_rating) in enumerate(movie_details):
        film_list[i]["imdb_id"] = imdb_id
        film_list[i]["imdb_rating"] = imdb_rating

    return film_list