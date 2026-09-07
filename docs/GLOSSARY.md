# Glossary

Each term appears once, with the place in the code where it is used. Added the first time the
term comes up, never rewritten later.

---

## Back-end

**Dependency injection**
A handler declares what it needs and the framework supplies it, instead of the handler building
it. `db: DbSession` is a declaration, not a call.
→ `backend/app/database.py`, every router.

**Annotated dependency**
`Annotated[Session, Depends(get_db)]` names a dependency once and reuses it as a type. It also
removes ruff's `B008`, which sees `Depends()` in a default argument as a mutable default.
→ `backend/app/database.py` (`DbSession`), `backend/app/auth.py` (`CurrentUser`).

**ORM (Object-Relational Mapping)**
A Python class stands for a table and an instance for a row, so a query is written in Python and
SQLAlchemy emits the SQL — parameterised, which is what closes SQL injection.
→ `backend/app/models.py`.

**Migration**
A versioned script that moves the database from one schema to the next. The models say what the
schema *should* be; the migration is how an existing database *gets* there.
→ `backend/alembic/versions/0001_initial_schema.py`.

**Naming convention (metadata)**
A pattern that names every constraint. Without it Postgres invents names and Alembic cannot drop
what it did not name, so a later migration fails on a constraint it cannot find.
→ `backend/app/models.py`, `NAMING_CONVENTION`.

**Foreign key, `ON DELETE CASCADE`**
A column that must match a row in another table. `CASCADE` means deleting the user deletes their
saved films, in one statement, instead of leaving rows pointing at nobody.
→ `backend/app/models.py`.

**Unique constraint**
A rule the database enforces on a pair of columns. `(user_id, tmdb_id)` unique means one row per
film per user — and it is the *database* that refuses a duplicate, which a `SELECT` first cannot
do when two requests arrive at once.
→ `backend/app/models.py`, and the 409 in `backend/app/movie_lists.py`.

**JWT (JSON Web Token), bearer token**
A signed string carrying a payload. The server does not store it: it verifies the signature and
trusts the payload. "Bearer" means whoever holds it is treated as the user, so it travels only
over the `Authorization` header.
→ `backend/app/auth.py`.

**Hashing (vs encryption)**
A one-way transformation. A hash cannot be reversed, only recomputed and compared, which is why a
stolen database of bcrypt hashes is not a list of passwords.
→ `backend/app/utils.py`, `hash_password`.

**Cache, TTL, cache miss**
A copy kept because recomputing it is expensive. TTL is how long the copy is allowed to live. A
miss is "not there" — here it also covers "Redis is unreachable", which is what keeps the cache
optional.
→ `backend/app/cache.py`.

**Logging a transition, not a state**
A condition that lasts logs once when it starts and once when it ends, not on every call that
meets it. Redis being down printed two lines per page view until `/health` took over the
question "is it up right now".
→ `backend/app/cache.py`, `_note_failure` / `_note_recovery`.

**Lazy client**
`redis.Redis.from_url()` opens no connection; the first command does. That is why a Redis that is
down never stops the application from starting.
→ `backend/app/cache.py`.

**`asyncio.gather`**
Runs several awaitables at once and waits for all of them. Twenty OMDB lookups take as long as
the slowest one instead of the sum of twenty.
→ `backend/app/routers/movie_list.py`.

**Fixture (pytest)**
A named piece of setup a test asks for by putting its name in the signature. `authorized_client`
is a client that is already signed in.
→ `backend/tests/conftest.py`.

**`monkeypatch`**
Replaces an attribute for the length of one test and puts it back afterwards. It is how the tests
call TMDB without leaving the machine.
→ `backend/tests/test_movies.py`.

**`parametrize`**
Runs the same test body over several inputs, each reported separately. Both saved lists are
tested by one file this way.
→ `backend/tests/test_saved_lists.py`.

**OWASP A01 — Broken Access Control**
Data reachable by someone who should not reach it. Ours was real: the public film list read the
whole `favorites` table, so every visitor saw every user's rows.
→ fixed at step 13; the regression test lives in `backend/tests/test_saved_lists.py`.

**CORS, preflight**
A browser refuses a cross-origin call unless the server allows the origin. For a call with an
`Authorization` header it first sends an `OPTIONS` request — the preflight — and only sends the
real one if that answer allows it.
→ `backend/app/main.py`, `origins`.

**307 redirect (the trailing slash)**
Starlette answers a path it cannot match with a redirect to that path plus or minus a slash.
307 keeps the method and the body, unlike a 302 — but the `Location` is built from the `Host`
header, and a client following it across origins drops `Authorization`. Avoided rather than
handled: every route here is declared without a trailing slash.
→ `backend/app/routers/`, all six.

---

## Front-end

**Context (React)**
A value published by a provider and read by any component below it, without passing it through
every intermediate component.
→ `frontend/src/context/AuthContext.jsx`, `SavedContext.jsx`.

**Hook**
A function starting with `use` that lets a component hold state or run an effect. `useAuth` is a
custom one: it reads a context and fails loudly if the provider is missing.
→ `frontend/src/context/`, `frontend/src/hooks/useTheme.js`.

**Effect (`useEffect`)**
Code that runs after rendering, to synchronise with something outside React — here, the network.
Its dependency array says when to run it again.
→ `frontend/src/pages/Search.jsx`.

**Cleanup / stale response**
The function an effect returns, run before the next one. It sets `ignore = true`, so an answer to
a request the user has already moved past is dropped instead of overwriting a newer one.
→ `frontend/src/pages/Search.jsx`, `SavedContext.jsx`.

**`useMemo`**
Recomputes a value only when its dependencies change. The two `Set`s of saved ids are built once
per list change, not once per card.
→ `frontend/src/context/SavedContext.jsx`.

**`aria-pressed`**
Marks a button as a toggle and says which way it is set. It reaches a screen reader *and* the
stylesheet, so the state cannot be shown in one and not the other.
→ `frontend/src/components/MovieCard.jsx`.

**Live region (`aria-live`)**
A part of the page a screen reader announces when its content changes. It must already be in the
DOM: announcing the arrival of the node itself is not the same thing.
→ `frontend/src/pages/Search.jsx`, `SavedPage.jsx`.
