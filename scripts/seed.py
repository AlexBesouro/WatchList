#!/usr/bin/env python
"""
WatchList — seed / reset des données de démo pour l'entretien.

Remet la base applicative (`watchlist`) dans un état initial connu :
  - vide les trois tables (`users`, "watched movies", "movies to be watched"),
  - recrée deux utilisateurs partageant le même mot de passe simple,
  - leur attribue des films « vus » et « à voir ».

Idempotent : relancer le script redonne EXACTEMENT le même état
(TRUNCATE ... RESTART IDENTITY, puis ré-insertion).

Lancer via le wrapper :   ./scripts/seed.sh
(ou directement :          PYTHONPATH=. .venv/bin/python scripts/seed.py)

⚠️  Écrit dans la base RÉELLE de l'app (celle de Swagger / Postman / run.sh),
    PAS dans la base de test `watchlist_test`.

Note unicité : `tmdb_id` et `imdb_id` portent un `unique=True` GLOBAL dans
models.py (c'est le bonus « unicité » du cahier). Les films des deux users sont
donc volontairement tous distincts, sinon l'insertion violerait la contrainte.
"""

from datetime import date

from sqlalchemy import text

from app import models
from app.database import SQLALCHEMY_DATABASE_URL, session_local
from app.utils import hash_password

# Mot de passe commun aux deux comptes de démo. Conforme à is_strong_password
# (8+ car., maj/min/chiffre/spécial) et identique aux fixtures de test.
PASSWORD = "Password_1"

# Tables applicatives, dans l'ordre — noms avec espaces à quoter en SQL brut.
TABLES = ["users", "watched movies", "movies to be watched"]

# --- Données de démo ---------------------------------------------------------
# Chaque user a des films « vus » (avec note perso) et « à voir ».
# Les tmdb_id / imdb_id sont réels et TOUS distincts entre les deux users
# (cf. note unicité en tête de fichier).

USERS = [
    {
        "email": "alice@watchlist.dev",
        "first_name": "Alice",
        "last_name": "Martin",
        "watched": [
            {"tmdb_id": 550, "title": "Fight Club", "release_date": "1999-10-15", "imdb_id": "tt0137523", "imdb_rating": 8.8, "personal_rating": 9.0},
            {"tmdb_id": 603, "title": "The Matrix", "release_date": "1999-03-31", "imdb_id": "tt0133093", "imdb_rating": 8.7, "personal_rating": 9.5},
            {"tmdb_id": 680, "title": "Pulp Fiction", "release_date": "1994-09-10", "imdb_id": "tt0110912", "imdb_rating": 8.9, "personal_rating": 8.5},
            {"tmdb_id": 13, "title": "Forrest Gump", "release_date": "1994-06-23", "imdb_id": "tt0109830", "imdb_rating": 8.8, "personal_rating": 8.0},
        ],
        "to_watch": [
            {"tmdb_id": 157336, "title": "Interstellar", "release_date": "2014-11-05", "imdb_id": "tt0816692", "imdb_rating": 8.7},
            {"tmdb_id": 496243, "title": "Parasite", "release_date": "2019-05-30", "imdb_id": "tt6751668", "imdb_rating": 8.5},
        ],
    },
    {
        "email": "bob@watchlist.dev",
        "first_name": "Bob",
        "last_name": "Durand",
        "watched": [
            {"tmdb_id": 155, "title": "The Dark Knight", "release_date": "2008-07-16", "imdb_id": "tt0468569", "imdb_rating": 9.0, "personal_rating": 9.0},
            {"tmdb_id": 27205, "title": "Inception", "release_date": "2010-07-15", "imdb_id": "tt1375666", "imdb_rating": 8.8, "personal_rating": 8.0},
            {"tmdb_id": 238, "title": "The Godfather", "release_date": "1972-03-14", "imdb_id": "tt0068646", "imdb_rating": 9.2, "personal_rating": 10.0},
        ],
        "to_watch": [
            {"tmdb_id": 278, "title": "The Shawshank Redemption", "release_date": "1994-09-23", "imdb_id": "tt0111161", "imdb_rating": 9.3},
            {"tmdb_id": 244786, "title": "Whiplash", "release_date": "2014-10-10", "imdb_id": "tt2582802", "imdb_rating": 8.5},
        ],
    },
]


def _movie_kwargs(movie: dict) -> dict:
    """Copie du film avec `release_date` converti en objet `date`."""
    kwargs = dict(movie)
    kwargs["release_date"] = date.fromisoformat(kwargs["release_date"])
    return kwargs


def reset(db) -> None:
    """Vide les trois tables et remet les séquences d'id à zéro."""
    quoted = ", ".join(f'"{t}"' for t in TABLES)
    db.execute(text(f"TRUNCATE TABLE {quoted} RESTART IDENTITY CASCADE"))
    db.commit()


def seed(db) -> tuple[int, int]:
    """Insère les users et leurs films. Retourne (nb_vus, nb_à_voir)."""
    watched_count = 0
    to_watch_count = 0
    for entry in USERS:
        user = models.User(
            email=entry["email"],
            password=hash_password(PASSWORD),
            first_name=entry["first_name"],
            last_name=entry["last_name"],
        )
        db.add(user)
        db.flush()  # attribue user.user_id sans commit

        for movie in entry["watched"]:
            db.add(models.WatchedMovies(user_id=user.user_id, **_movie_kwargs(movie)))
            watched_count += 1
        for movie in entry["to_watch"]:
            db.add(models.ToBeWatched(user_id=user.user_id, **_movie_kwargs(movie)))
            to_watch_count += 1

    db.commit()
    return watched_count, to_watch_count


def main() -> None:
    db = session_local()
    try:
        reset(db)
        watched_count, to_watch_count = seed(db)
    finally:
        db.close()

    print("── WatchList · seed terminé ──────────────────────────────────────────")
    print(f"  Base       : {SQLALCHEMY_DATABASE_URL}")
    print(f"  Users      : {len(USERS)}   |   films vus : {watched_count}   |   à voir : {to_watch_count}")
    print("  Comptes de démo (même mot de passe) :")
    for entry in USERS:
        print(f"    • {entry['email']:<22} / {PASSWORD}"
              f"   ({len(entry['watched'])} vus, {len(entry['to_watch'])} à voir)")
    print("──────────────────────────────────────────────────────────────────────")
    print("  Prochaine étape :  ./scripts/run.sh dev   → http://localhost:8000/docs")
    print("  Ou importe la collection Postman : postman/WatchList.postman_collection.json")


if __name__ == "__main__":
    main()
