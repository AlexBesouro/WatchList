#!/usr/bin/env python
"""
Mock local des APIs TMDB & OMDB — outillage d'entretien (aucune clé requise).

Sert des réponses « canned », à la même FORME que TMDB/OMDB, pour que
`GET /movies/` fonctionne sans clé API et renvoie des films réalistes.

Ne modifie PAS le code de l'app : on redirige juste TMDB_URL / OMDB_URL vers ce
serveur (mode mock de scripts/run.sh). L'app fait de vrais appels HTTP async,
ils atterrissent simplement en local — le chemin `asyncio.gather` reste intact
(pratique pour le bonus « robustesse »).

Routes servies (mêmes formes que les vraies APIs) :
  GET /discover/movie               → catalogue (forme TMDB "discover")
  GET /movie/{tmdb_id}/external_ids → {"imdb_id": "..."} (forme TMDB)
  GET /                             → note OMDB {"imdbRating": "..."} (via ?i=imdb_id)
  GET /health                       → sonde de disponibilité

Lancer :  ./scripts/mock.sh start   (ou dev)
"""

from fastapi import FastAPI

mock_app = FastAPI(title="WatchList — mock TMDB/OMDB")

# Catalogue : films avec tmdb_id / imdb_id / note réels. Inclut les films seedés
# (pour voir `already_seen` / `watch_later` s'activer dans /movies/) + des extras.
# « Schindler's List » a une note OMDB "N/A" → illustre l'affichage d'une note
# manquante (imdb_rating: null), sujet du bonus robustesse.
CATALOG = [
    {"id": 550,    "original_title": "Fight Club",               "release_date": "1999-10-15", "imdb_id": "tt0137523", "imdbRating": "8.8"},
    {"id": 603,    "original_title": "The Matrix",               "release_date": "1999-03-31", "imdb_id": "tt0133093", "imdbRating": "8.7"},
    {"id": 680,    "original_title": "Pulp Fiction",             "release_date": "1994-09-10", "imdb_id": "tt0110912", "imdbRating": "8.9"},
    {"id": 13,     "original_title": "Forrest Gump",             "release_date": "1994-06-23", "imdb_id": "tt0109830", "imdbRating": "8.8"},
    {"id": 155,    "original_title": "The Dark Knight",          "release_date": "2008-07-16", "imdb_id": "tt0468569", "imdbRating": "9.0"},
    {"id": 27205,  "original_title": "Inception",                "release_date": "2010-07-15", "imdb_id": "tt1375666", "imdbRating": "8.8"},
    {"id": 238,    "original_title": "The Godfather",            "release_date": "1972-03-14", "imdb_id": "tt0068646", "imdbRating": "9.2"},
    {"id": 157336, "original_title": "Interstellar",             "release_date": "2014-11-05", "imdb_id": "tt0816692", "imdbRating": "8.7"},
    {"id": 496243, "original_title": "Parasite",                 "release_date": "2019-05-30", "imdb_id": "tt6751668", "imdbRating": "8.5"},
    {"id": 278,    "original_title": "The Shawshank Redemption", "release_date": "1994-09-23", "imdb_id": "tt0111161", "imdbRating": "9.3"},
    {"id": 244786, "original_title": "Whiplash",                 "release_date": "2014-10-10", "imdb_id": "tt2582802", "imdbRating": "8.5"},
    {"id": 129,    "original_title": "Spirited Away",            "release_date": "2001-07-20", "imdb_id": "tt0245429", "imdbRating": "8.6"},
    {"id": 438631, "original_title": "Dune",                     "release_date": "2021-09-15", "imdb_id": "tt1160419", "imdbRating": "8.0"},
    {"id": 424,    "original_title": "Schindler's List",         "release_date": "1993-11-30", "imdb_id": "tt0108052", "imdbRating": "N/A"},
]

BY_TMDB = {m["id"]: m for m in CATALOG}
BY_IMDB = {m["imdb_id"]: m for m in CATALOG}


@mock_app.get("/health")
def health():
    return {"status": "ok", "service": "watchlist-mock", "movies": len(CATALOG)}


@mock_app.get("/discover/movie")
def discover_movie(primary_release_year: int | None = None,
                   with_original_language: str | None = None,
                   page: int = 1):
    """Forme TMDB `discover`. Mock : filtres ignorés, catalogue complet en page 1."""
    if page == 1:
        results = [
            {"id": m["id"], "original_title": m["original_title"], "release_date": m["release_date"]}
            for m in CATALOG
        ]
    else:
        results = []
    return {"page": page, "results": results, "total_pages": 1, "total_results": len(CATALOG)}


@mock_app.get("/movie/{tmdb_id}/external_ids")
def external_ids(tmdb_id: int):
    """Forme TMDB `external_ids` : renvoie l'imdb_id du film."""
    movie = BY_TMDB.get(tmdb_id)
    return {"id": tmdb_id, "imdb_id": movie["imdb_id"] if movie else None}


@mock_app.get("/")
def omdb(i: str | None = None, apikey: str | None = None):
    """Forme OMDB : appelée en `?i=<imdb_id>&apikey=...`. Renvoie la note imdb."""
    movie = BY_IMDB.get(i)
    if not movie:
        return {"Response": "False", "Error": "Movie not found!"}
    return {"Response": "True", "imdbID": i, "imdbRating": movie["imdbRating"]}
