# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

WatchList is a FastAPI + PostgreSQL REST API for tracking watched movies and a "to watch" list, enriched with TMDB/OMDB data. It is also **live technical-interview material** — see `CAHIER-EXERCICES.md`. Several things are *intentionally* incomplete or buggy because they are the candidate's exercises; do not "fix" them unprompted:

- `DELETE /watched/{tmdb_id}` does not exist yet — `tests/test_watched.py` is red on purpose (exercise 1).
- `tests/test_login.py` is empty on purpose (bonus exercise).
- `tmdb_id`/`imdb_id` carry a global `unique=True` in `models.py`, so two users can't track the same film — this is the "fix uniqueness" bonus, not an oversight.
- `movie_list.py`'s `asyncio.gather` has no per-film error isolation — that's the "robustness" bonus.

The `app/`, `tests/`, and `alembic/` code is the candidate's. `scripts/`, `requirements.txt`, and `CAHIER-EXERCICES.md` are interviewer tooling (branch `prep-entretien`).

## Commands

Everything runs through the wrapper scripts, which use the project venv (`.venv`, Python 3.14). Run from the repo root.

```bash
./scripts/infra.sh start      # start PostgreSQL + Redis (docker compose, project "watchlist")
./scripts/infra.sh init       # apply Alembic migrations (upgrade head); idempotent
./scripts/infra.sh psql       # open psql in the container   (also: cli → redis-cli, clean, info)
# infra.sh accepts a "<target> <action>" grammar (single entry point):
#   target = all | postgres (pg) | redis | mock   action = start|stop|restart|status|logs
#   e.g. ./scripts/infra.sh all restart · ./scripts/infra.sh redis logs · ./scripts/infra.sh mock start
# Bare "start|stop|restart|status|logs" are legacy aliases for "all <action>".

./scripts/seed.sh             # reset + seed demo data: users alice@ / bob@watchlist.dev (pwd Password_1) + their movies; idempotent
# infra.sh start also starts a local TMDB/OMDB mock (scripts/mock_apis.py) → GET /movies/ works without API keys (run.sh dev auto-uses it)

./scripts/run.sh dev          # run the API in foreground with --reload → http://localhost:8000/docs
./scripts/run.sh start|stop|status|logs   # background instance

./scripts/test.sh                                    # whole suite (always -v)
./scripts/test.sh delete                             # -k "delete" keyword filter
./scripts/test.sh tests/test_watched.py::test_delete_watched_movie   # single test (path/node-id)
./scripts/test.sh -k "delete and not owns" -x        # raw pytest args (first token starts with -)
```

`test.sh` auto-creates the `watchlist_test` database if missing. Both `run.sh` and `test.sh` require Docker infra to be up first.

## Critical gotchas

- **`.env` is mandatory at import time.** `app/config.py` instantiates `Settings()` at module load, so *any* import of `app.*` (app, tests, Alembic) crashes without a populated `.env`. Copy `.env_example` → `.env` and fill it. Note `.env_example` shows `DATABASE_PORT=5432`, but docker-compose maps Postgres to host **5442** — the real `.env` must use 5442.
- **ASGI target is `app.main:my_app`**, not the conventional `app`.
- **Redis host is hard-coded** to `localhost:6379` in `app/routers/movie_list.py` (not read from config).
- **Mock mode for `GET /movies/`** (no API keys needed): `scripts/mock_apis.py` is a standalone FastAPI server mimicking TMDB+OMDB. It's **infra**, started by `./scripts/infra.sh start` (part of `all`; port 9100) — or alone via `./scripts/infra.sh mock start`. `run.sh` never starts it; it only *points* the app at it: when mock mode is on, `run.sh` exports `TMDB_URL`/`OMDB_URL` toward `:9100` (pydantic-settings prioritizes OS env over `.env`, so `app/` is untouched). Mock mode toggle: `WATCHLIST_MOCK=1`/`0`; unset = auto-on while `.env` keys are still `CHANGE_ME` placeholders (so plain `run.sh dev` already uses the mock). `run.sh mock` just forces the mode.
- **Table names contain spaces**: `users`, `"watched movies"`, `"movies to be watched"` (see `models.py`). Quote them in raw SQL.
- **Alembic gets its URL from code, not the ini.** `alembic.ini`'s `sqlalchemy.url` is empty; `alembic/env.py` overrides it with `app.database.SQLALCHEMY_DATABASE_URL` (built from `.env`). So migrations always hit the same DB as the app.
- **bcrypt is pinned to 4.0.1** in `requirements.txt` (passlib 1.7.4 breaks on bcrypt ≥ 4.1). Don't bump it.

## Architecture

Request flow for an authenticated call:
`client → router → Depends(get_current_user) + Depends(get_db) → models / external API → response (Pydantic schema)`

- `app/main.py` — assembles `my_app` and mounts the five routers.
- `app/config.py` — pydantic-settings `Settings` read from `.env`; exported as `settings`.
- `app/database.py` — SQLAlchemy engine, `session_local`, and the `get_db()` dependency (yields a session, closes in `finally`).
- `app/models.py` — SQLAlchemy 2.0 declarative models (`User`, `WatchedMovies`, `ToBeWatched`), all with a `user_id` FK (`ondelete="CASCADE"`).
- `app/schemas.py` — Pydantic request/response models (the API contract; not the DB shape).
- `app/auth.py` — JWT via PyJWT. `create_access_token`, `verify_token`, and `get_current_user` (an `OAuth2PasswordBearer(tokenUrl="login")` dependency). **The token payload carries the user under the key `user_email`** — fixtures and any manual token building must match.
- `app/utils.py` — password hashing/strength (`is_strong_password` enforces the create-user policy) and the async TMDB/OMDB HTTP calls (`aiohttp`).
- `app/routers/` — `user` (`/users`), `login` (`/login`), `movie_list` (`/movies`), `watched_list` (`/watched`), `to_be_watched` (`/to-watch`).

`GET /movies/` is the one heavy endpoint: it hits TMDB `discover`, caches the raw result in Redis (10h TTL), then fans out per-film TMDB `external_ids` + OMDB rating lookups via `asyncio.gather`, and cross-references the user's watched / to-watch tables to annotate each result.

### Tests

`tests/conftest.py` points at a **separate `<DB>_test` database** and the `session` fixture does `drop_all` + `create_all` on every test (fresh schema each time — Alembic is not involved in tests). Key fixtures: `client` (overrides `get_db`), `test_user`, `access_token`, `authorized_client` (sets the Bearer header). Postgres must be running; `test.sh` handles the test-DB creation.

### Migrations

Alembic migrations live in `alembic/versions/`. After changing `app/models.py`, generate with `.venv/bin/alembic revision --autogenerate -m "..."` then `./scripts/infra.sh init` (or `.venv/bin/alembic upgrade head`) to apply.
