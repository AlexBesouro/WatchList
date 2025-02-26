import json
from typing import List
from fastapi import APIRouter, Depends
import requests
from sqlalchemy.orm import Session

from app import schemas, models
from app.config import settings
import redis

from app.database import get_db

red = redis.Redis(host='localhost', port=6379, decode_responses=True)

router = APIRouter(prefix="/movies", tags=["All movies list"])

@router.get("/", response_model= List[schemas.MovieResponse])
def get_movies(params: schemas.MovieSearch, db: Session = Depends(get_db)):
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
        response = requests.get(f"{settings.TMDB_URL}discover/movie?"
                                f"primary_release_year={params.primary_release_year}&"
                                f"with_original_language={params.original_language}&"
                                f"page={params.page}",
                                headers=headers)
        result = response.json()
        red.set(cache_key, json.dumps(result), ex=36000)
        print("Fetching new data from TMDB API")
    total_pages = result.get("total_pages", 1)
    print(total_pages)
    res = result["results"]
    film_list = []
    for i in range(len(res)):
        is_watched = db.query(models.WatchedMovies).filter(models.WatchedMovies.tmdb_id == res[i]['id']).first()
        in_list_to_be_seen = db.query(models.UnWatched).filter(models.UnWatched.tmdb_id == res[i]['id']).first()
        if is_watched:
            watched_status = True
            personal_rating = is_watched.personal_rating
        else:
            personal_rating = 0
            watched_status = False
        if in_list_to_be_seen:
            watch_later = True
        else:
            watch_later = False

        imdb_id_response = requests.get(f"{settings.TMDB_URL}movie/{res[i]["id"]}/external_ids", headers=headers)
        try:
            imdb_id_data = imdb_id_response.json()
        except ValueError:
            imdb_id_data = {}
        imdb_id = imdb_id_data.get("imdb_id", None)
        if imdb_id == "N/A":
            imdb_id = None

        imdb_rating_response = requests.get(f"{settings.OMDB_URL}?i={imdb_id}&apikey={settings.OMDB_API_KEY}")
        try:
            imdb_rating_data = imdb_rating_response.json()
        except ValueError:
            imdb_rating_data = {}
        imdb_rating = imdb_rating_data.get("imdbRating", None)
        if imdb_rating == "N/A":
            imdb_rating = None
        film_list.append({"tmdb_id": res[i]["id"],
                          "title" : res[i]["original_title"],
                          "release_date": res[i]["release_date"],
                          "imdb_id" : imdb_id,
                          "imdb_rating": imdb_rating,
                          "already_seen": watched_status,
                          "personal_rating": personal_rating,
                          "watch_later": watch_later})


    return film_list