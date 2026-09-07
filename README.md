# WatchList

Browse films, keep a **favorites** list and a **watch later** list.

A FastAPI + PostgreSQL API enriched with TMDB and OMDB data and cached in Redis, with a React
front-end. Authentication is a JWT bearer token.

The structure is two zones, and only two:

1. **Browsing is public** — the home page and the search need no account, and the endpoint
   behind them reads no user data at all.
2. **Saving needs an account** — the two lists are the only thing the app asks you to sign in
   for.

---

## Requirements

| | Version | Note |
| --- | --- | --- |
| Python | 3.13+ | managed by Poetry, virtualenv in `backend/.venv` |
| Node | 20+ | Vite 8 |
| Docker | any recent | only for PostgreSQL and Redis |

On Linux and macOS the virtualenv executables live in `.venv/bin`, not `.venv/Scripts`.

## Install

```bash
git clone <this repository>
cd watchlist

cp backend/.env_example backend/.env      # then fill it in, see the table below

cd backend && poetry install              # creates .venv with both dependency groups
cd ../frontend && npm install
```

## Run

Three terminals, or three commands and two of them backgrounded.

```bash
# 1. infrastructure — the --env-file makes the container use the password the app reads
docker compose --env-file backend/.env up -d

# 2. the API, from backend/
.venv/Scripts/alembic upgrade head
# --reload-dir app: without it the reloader watches backend/ whole and restarts
# the server every time a test file is saved, which changes nothing it serves.
.venv/Scripts/uvicorn app.main:my_app --reload --reload-dir app

# 3. the front-end, from frontend/
npm run dev
```

- API and interactive docs: <http://localhost:8000/docs>
- Application: <http://localhost:5173>

**Neither Postgres nor Redis is needed to browse.** `GET /movies` opens no database session,
and a Redis that is down is read as a cache miss, so the home page and the search work with
nothing but the API running. `GET /health` says which of the two is actually up:

```bash
curl http://localhost:8000/health
# {"status":"degraded","database":"down","cache":"down"}   <- API alone
# {"status":"ok","database":"up","cache":"up"}             <- compose running
```

## Test

```bash
cd backend  && .venv/Scripts/pytest -q     # 56 tests, SQLite in memory, no Docker needed
cd frontend && npm test                    # 19 tests, Vitest + jsdom
```

Quality:

```bash
cd backend  && .venv/Scripts/ruff check app tests && .venv/Scripts/ruff format --check app tests
cd frontend && npm run lint
```

## Environment

`backend/.env` is read **once, at import time**, so a missing line stops the application from
starting rather than failing on the first request. `backend/.env_example` is the template.

| Variable | What it is |
| --- | --- |
| `TMDB_URL` | `https://api.themoviedb.org/3/` |
| `AUTHORIZATION` | TMDB **v4 read access token** — the long `eyJ…` string, not the 32-character v3 key |
| `OMDB_URL` | `http://www.omdbapi.com/` |
| `OMDB_API_KEY` | OMDB key, used for the IMDb rating |
| `DATABASE_HOSTNAME` | `localhost` |
| `DATABASE_PORT` | **5555** — the port `compose.yml` publishes, not the default 5432 |
| `DATABASE_PASSWORD` | also what the container is created with |
| `DATABASE_NAME` | `watchlist` |
| `DATABASE_USERNAME` | `postgres` |
| `REDIS_URL` | optional, defaults to `redis://localhost:6379` |
| `SECRET_KEY` | signs every token — generate one, never reuse the example |
| `ALGORITHM` | `HS256` |
| `EXPIRE_TIME` | token lifetime, in minutes |

The front-end reads one optional variable, `VITE_API_URL`; without it it calls
`http://localhost:8000`.

## The API

| Method | Path | Auth | What it does |
| --- | --- | --- | --- |
| `GET` | `/health` | — | what the service can reach: `{status, database, cache}` |
| `GET` | `/movies` | — | popular films, or the results of `?query=` |
| `POST` | `/users` | — | create an account |
| `POST` | `/login` | — | exchange email + password for a token |
| `GET` | `/users/me` | token | who the token belongs to |
| `GET` | `/favorites` | token | this user's favorites |
| `POST` | `/favorites` | token | add a film |
| `DELETE` | `/favorites/{tmdb_id}` | token | remove a film |
| `GET` `POST` `DELETE` | `/watch-later`, `/watch-later/{tmdb_id}` | token | the same three, on the other list |

**No path ends in a trailing slash.** One rule, so `/docs` can be read rather than memorised.

## How a request flows

```
public   client → router → TMDB (+ Redis cache) → response schema
private  client → router → CurrentUser (JWT) + DbSession → movie_lists → PostgreSQL → response schema
```

- `app/main.py` — builds `my_app`, mounts the six routers, sets CORS.
- `app/config.py` — `Settings` read from `.env`, exported as `settings`.
- `app/database.py` — engine, session factory, and `DbSession`, the annotated dependency every
  handler that touches Postgres takes.
- `app/auth.py` — token creation and verification, and `CurrentUser`, the single gate in front
  of the private routes.
- `app/models.py` — three tables: `users`, `favorites`, `watch_later`.
- `app/schemas.py` — the request and response shapes: the API contract, not the database shape.
- `app/movie_lists.py` — the three functions behind both saved lists, each taking the table as a
  parameter, so `user_id` is filtered in exactly one place.
- `app/cache.py` — Redis, guarded: unreachable means a miss, never an error.
- `app/routers/health.py` — what the service can reach, component by component.
- `app/utils.py` — password hashing and policy, and the TMDB/OMDB calls.
- `frontend/src/api/client.js` — the only file in the front-end that touches the network.
- `frontend/src/context/` — `AuthContext` (token, user, modal) and `SavedContext` (both lists).

## Where the rest is written down

| File | What is in it |
| --- | --- |
| `project-plan.md` | the numbered roadmap, and a Backlog with the reasons things were left |
| `docs/JOURNAL.md` | one entry per session: what was done, and what it taught |
| `docs/GLOSSARY.md` | each term used in the code, explained once |
| `CLAUDE.md` | how the work is conducted (untracked, local) |
