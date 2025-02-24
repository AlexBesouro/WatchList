import json
from typing import List
from fastapi import APIRouter
import requests
from app import schemas
from app.config import settings
import redis

red = redis.Redis(host='localhost', port=6379, decode_responses=True)

router = APIRouter(prefix="/movies", tags=["All movies list"])

@router.get("/", response_model= List[schemas.MovieResponse])
def get_movies(params: schemas.MovieSearch):
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
        red.set(cache_key, 36000, json.dumps(result))
        print("Fetching new data from TMDB API")

    res = result["results"]
    film_list = []
    for i in range(len(res)):
        imdb_id = requests.get(f"{settings.TMDB_URL}movie/{res[i]["id"]}/external_ids", headers=headers).json()["imdb_id"]
        imdb_rating = requests.get(f"{settings.OMDB_URL}?i={imdb_id}&apikey={settings.OMDB_API_KEY}").json()["imdbRating"]
        film_list.append({"tmdb_id": res[i]["id"],
                          "title" : res[i]["original_title"],
                          "release_date": res[i]["release_date"],
                          "imdb_id" : imdb_id,
                          "imdb_rating": imdb_rating})


    return film_list