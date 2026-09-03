# CLAUDE.md

Guidance for Claude Code (claude.ai/code) when working in this repository.

**WatchList is a learning project.** The `Learning mode` rules below **override the global
`~/.claude/CLAUDE.md`** wherever the two disagree. This file is English because every file in
this repository is English — the rules it sets are about how the work is conducted, not about
the language of the file that states them.

---

## Learning mode

### Language

- **Chat replies are Russian prose.** This overrides the global "chat is English" rule.
- **Programming terms stay English, inline, never translated**: `dependency injection`,
  `fixture`, `migration`, `foreign key`, `race condition`, `dependency`, `router`.
- **Everything written to a file is English**: code, comments, docstrings, docs, commit
  messages, branch names, PR titles and bodies.
- The global "correct Alex's English" rule stays, but fires only when the prompt itself was
  written in English.

### Pace

- **One step per turn, then stop and hand the prompt back.** "Давай", "да", "дальше"
  authorise **one** step, never the rest of the plan.
- A step is atomic: one idea, one file (two at most), a diff readable whole in the approval
  window.
- Never chain the verification, the commit, or the next step into the same turn.

### Explanation comes before the edit

Before every `Write` / `Edit`, the reply must already contain, in this order:

1. **Что делаем** — the change, one or two lines.
2. **Почему так** — the reason behind each decision: the type chosen, the default, the
   pattern, the trap avoided.
3. **Что отвергли** — the alternative considered, and why it lost.
4. **Как проверим** — the exact command that will prove it works.

Code goes straight into the file, **never** pasted as a fenced block in the reply — code is
read in the IDE, not in the chat. An edit announced by one line of preamble is a rejected
edit.

### Who writes the code

Claude writes, Alex reviews the diff in the approval prompt. **Rejecting that prompt is how
Alex asks a question about the diff** — it is expected, not a refusal. Answer the question,
then re-offer the **same** edit unchanged, unless the answer itself calls for a change.

### Comprehension check

Every step ends with exactly one question testing understanding of what was just done, as a
blockquote opened by `> ❓`. "Продолжаем?" is not a comprehension check.

### Verification is part of the step

A step is not done until a command proves it: `pytest`, a `curl`, a `psql` query, a
red test turning green. Show the real output. If it failed, say it failed.

### Errors are teaching material

When a command fails, read the error first — which line, which exception, what it actually
means — then fix it. Never retry silently with different flags.

### No silent scope creep

Touch only what the step names. Anything else noticed — dead code, a bug, a bad name — goes to
the Backlog section of `project-plan.md`, not into the diff.

### No unexplained dependency

A new package requires three things stated **before** it is added: what it does, which stdlib
or already-installed alternative was rejected, and why.

### Commands are broken down before they run

Markdown table, one row per part, the command written one part per line (global rule, kept).

---

## Learning artefacts

All three are English.

| File | Content | Written when |
| --- | --- | --- |
| `project-plan.md` | Numbered roadmap with checkboxes, plus a `Backlog` section | the checkbox is ticked when the step is verified |
| `docs/JOURNAL.md` | One entry per session: what was done, and the concept it taught | end of session, drafted in chat first |
| `docs/GLOSSARY.md` | Each new term once: English term, two-line explanation, where it appears in the code | the first time the term is used |

**Session start**: read `project-plan.md` and give a 2–3 line recap — where we stopped, what
comes next.

---

## Git

- **Conventional Commits**: `<type>(<scope>): <description>` — imperative, lowercase, no
  trailing dot. Types: `feat` `fix` `docs` `test` `refactor` `chore` `ci` `perf` `style`.
- **Atomic**: a commit whose message needs an "and" is two commits.
- **One branch per unit of work**: `<type>/<subject>` — `feat/delete-endpoint`,
  `fix/redis-host`, `docs/glossary`.
- **`main` is stable**: never commit on it directly — branch, then PR.
- Nothing is committed or pushed without asking. The PR title and body are pasted in chat for
  review before the PR is created.

---

## Documentation legacy

The repository comes from a previous life as technical-interview material, so some docs are in
French: `backend/postman/README.md` and `backend/tests/test_watched.py`.

**Rule: touching a French file means translating it fully to English in that same change.**
There is no separate translation phase.

---

## What this is

WatchList is a **FastAPI + PostgreSQL** REST API tracking watched movies and a "to watch"
list, enriched with TMDB/OMDB data and cached in Redis. Auth is JWT.

## Commands

The wrapper scripts went with the old `scripts/` folder and come back at the end of the roadmap
(step 33), as do the compose file (step 3), the seed data (step 15) and the TMDB/OMDB stand-in
server (step 18). Until each lands, the command is written out in full next to the step that
needs it in `project-plan.md`.

Python runs **from `backend/`**, against `backend/.venv` (Python 3.14, Poetry-managed). On
Linux and macOS the executables sit in `.venv/bin`, not `.venv/Scripts`.

```bash
cd backend
poetry install                                    # create .venv, install both groups
.venv/Scripts/alembic upgrade head                # apply the migrations
.venv/Scripts/uvicorn app.main:my_app --reload    # API -> http://localhost:8000/docs
.venv/Scripts/pytest -v                           # whole suite
.venv/Scripts/pytest -k delete                    # keyword filter
```

The front-end runs from `frontend/`: `npm install`, then `npm run dev` (Vite, port 5173).

Both need PostgreSQL and Redis up, and the tests additionally need a `watchlist_test`
database - `backend/tests/conftest.py` appends `_test` to `DATABASE_NAME`.

## Architecture

Request flow for an authenticated call:
`client → router → Depends(get_current_user) + Depends(get_db) → models / external API → response (Pydantic schema)`

- `backend/app/main.py` — builds `my_app` and mounts the routers.
- `backend/app/config.py` — pydantic-settings `Settings` read from `.env`, exported as `settings`.
- `backend/app/database.py` — engine, `session_local`, and the `get_db()` dependency (yields a
  session, closes it in `finally`).
- `backend/app/models.py` — SQLAlchemy 2.0 declarative models (`User`, `WatchedMovies`,
  `ToBeWatched`), each with a `user_id` FK (`ondelete="CASCADE"`).
- `backend/app/schemas.py` — Pydantic request/response models: the API contract, not the DB shape.
- `backend/app/auth.py` — JWT via PyJWT: `create_access_token`, `verify_token`, `get_current_user`
  (an `OAuth2PasswordBearer(tokenUrl="login")` dependency).
- `backend/app/utils.py` — password hashing / strength, and the async TMDB/OMDB calls (`aiohttp`).
- `backend/app/routers/` — `user` (`/users`), `login` (`/login`), `movie_list` (`/movies`),
  `watched_list` (`/watched`), `to_be_watched` (`/to-watch`), `smth` (`/smth`, a leftover
  stub).

`GET /movies/` is the heavy endpoint: TMDB `discover` → cached raw in Redis (10h TTL) → per
film, TMDB `external_ids` + OMDB rating fanned out with `asyncio.gather` → cross-referenced
against the user's watched / to-watch tables.

**Tests**: `backend/tests/conftest.py` points at a separate `<DB>_test` database and the `session`
fixture does `drop_all` + `create_all` on every test — a fresh schema each time, Alembic not
involved. Fixtures: `client` (overrides `get_db`), `test_user`, `access_token`,
`authorized_client` (sets the Bearer header).

**Migrations**: after changing `backend/app/models.py`, run
from `backend/`, `.venv/Scripts/alembic revision --autogenerate -m "..."`, then
`.venv/Scripts/alembic upgrade head`.

## Gotchas

| Gotcha | Where |
| --- | --- |
| **`.env` is mandatory at import time** — `Settings()` runs at module load, so *any* import of `app.*` (app, tests, Alembic) crashes without a filled `.env`. | `backend/app/config.py` |
| **Postgres is on host port 5442**, not 5432 — `.env_example` is wrong on this line, the real `.env` must say 5442. | `compose.yml`, step 3 |
| **The ASGI target is `app.main:my_app`**, not the conventional `app`. | `backend/app/main.py:11` |
| **Redis is hard-coded** to `localhost:6379`, not read from `settings`. | `backend/app/routers/movie_list.py:13` |
| **Table names contain spaces**: `users`, `"watched movies"`, `"movies to be watched"` — quote them in raw SQL. | `backend/app/models.py:26,43` |
| **Alembic gets its URL from code, not the ini** — `backend/alembic.ini`'s `sqlalchemy.url` is empty, `backend/alembic/env.py` overrides it with `app.database.SQLALCHEMY_DATABASE_URL`. | `backend/alembic/env.py` |
| **The token carries the user under the key `user_email`** — fixtures and hand-built tokens must match. | `backend/app/auth.py` |
| **Dependencies are Poetry-managed** — `pyproject.toml` plus a committed `poetry.lock`, `package-mode = false`, and `poetry.toml` pinning the venv in-project. bcrypt is held at exactly 4.0.1: passlib 1.7.4 breaks on bcrypt ≥ 4.1. | `backend/` |
| **`VIRTUAL_ENV` overrides `in-project = true`** — a venv activated from another project silently receives every `poetry add`. Prefix Poetry commands with `env -u VIRTUAL_ENV` whenever the terminal has one active. | `backend/poetry.toml` |