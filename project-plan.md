<!-- markdownlint-disable MD029 -->
<!-- Steps are numbered continuously 1..26 across the day sections so that a step can be
     cited by its number alone. MD029 would demand each list restart at 1. -->

# WatchList — roadmap

`[ ]` open · `[x]` done, and the verification command was run and its output seen · `[-]` dropped,
with the reason recorded in the step itself.

## What this is

WatchList is the second of the two projects defended for the DWWM. `geo-enrich` carries the
back-end story and has no front-end at all, so WatchList exists to carry the front-end.

Six competencies are the target. Their titles are quoted from the REAC because the dossier
reproduces them word for word.

| | Competency (REAC verbatim) | Earned by |
| --- | --- | --- |
| CP2 | *Maquetter des interfaces utilisateur web ou web mobile* | `docs/mockups.md`: style guide, wireframes at two widths, screen-flow diagram |
| CP3 | *Réaliser des interfaces utilisateur statiques web ou web mobile* | React components and hand-written CSS, responsive, accessible |
| CP4 | *Développer la partie dynamique des interfaces utilisateur* | `client.js`, `AuthContext`, form validation, error handling, 3 Vitest tests |
| CP5 | *Mettre en place une base de données relationnelle* | one migration, `schema.sql`, `roles.sql`, seed data, backup and restore |
| CP6 | *Développer des composants d'accès aux données SQL et NoSQL* | SQLAlchemy for SQL, Redis for key/value, both with their failure paths |
| CP7 | *Développer des composants métier côté serveur* | routers, JWT auth, password policy, per-user isolation, pytest |

CP1 and CP8 (environment, deployment) are **out of scope** — they are not among the six, and
four days do not stretch. No Dockerfile for the app, no public deployment.

## Scope ceiling

Three pages and one modal. Every screen exists to exercise a competency; nothing is added
because it would be nice.

The structure is two zones, and only two:

1. **Browsing is public.** The home page and the search are open to everyone, and the endpoint
   behind them reads no user data at all.
2. **Saving needs an account.** That is the single gate, and the only reason the app ever asks
   who you are.

- **Search `/`** — one text field, a grid of film cards, pagination. Each card shows poster,
  title, year, IMDb rating, and two buttons: add to favorites, add to watch later.
- **Favorites `/favorites`** — the same cards, the same two buttons. Logged out, it offers the
  modal instead of rendering an empty list.
- **Watch later `/watch-later`** — the same page over the other list.
- **Auth modal** — a native `<dialog>` over any page, two tabs: sign in (2 fields), sign up
  (4 fields: email, password, first name, last name).

**Two saved lists, two tables** — `favorites` and `watch_later`, identical in shape. They are
not one table with a flag: a film can sit in both, and a flag would make "in both" a state to
encode rather than two rows to read. The old `watched_movies` table is gone; it demanded a
`personal_rating` on insert, which is exactly the extra input the scope removes.

Order of work: the whole front-end first against fixture data, then the back-end, then the
wiring. That is only possible because every network call lives in one file, `client.js`.

## Design tokens

Decided once, transcribed into `frontend/src/index.css` at step 4 and documented in
`docs/mockups.md` at step 23. Contrast ratios are computed, not estimated; WCAG asks 4.5:1 for
body text and 3:1 for the borders of interactive controls.

| Token | Hex | Use | On `#0A0A0A` |
| --- | --- | --- | --- |
| `--bg` | `#0A0A0A` | page background | — |
| `--surface` | `#141414` | cards, modal | — |
| `--text` | `#F5F5F5` | body text | 18.16:1 |
| `--muted` | `#A3A3A3` | secondary text | 7.85:1 |
| `--accent` | `#22C55E` | links, buttons, focus ring | 8.69:1 |
| `--accent-strong` | `#16A34A` | hover, active | 6.01:1 |
| `--error` | `#F87171` | validation messages | 7.16:1 |
| `--border` | `#6B7280` | borders of inputs and buttons | 4.10:1 |
| `--divider` | `#262626` | decorative separators only | 1.31:1, never a control |

Black text `#0A0A0A` on the green button reaches 8.69:1.

A light palette sits on top as `:root[data-theme='light']`, overriding nine of these: `--bg`
`#FFFFFF`, `--text` `#18181B` (17.72:1), `--muted` `#52525B` (7.73:1), `--accent` `#15803D`
(5.02:1 on white, and white on it), `--error` `#B91C1C`. `--border` is not repeated — `#6B7280`
clears its threshold on both grounds, 4.10:1 on black and 4.83:1 on white. The theme is stamped
on `<html>` by an inline script in `index.html` before the first paint, from `localStorage`
first and the system preference second.

---

## Day 2 (Thu 3 Sep) — the front-end, static, no network

1. [x] **Split the repository into `backend/` and `frontend/`** — Poetry adopted, all 37 Python
   files moved with `git mv`, documentation realigned. Merged as PR #2.
2. [x] **Scaffold `frontend/`** — Vite 8, React 19, `react-router-dom` 7, and the
   `src/{api,components,context,pages}` layout. The template ships `oxlint`, not ESLint, which
   covers *la qualité du code est vérifiée* for the front-end the way `ruff` does for the back.
3. [x] **Strip the template and set up routing** — delete the counter demo, `App.css` and
   `src/assets/`. `App.jsx` becomes a `BrowserRouter` with two routes wrapped in one layout.
   Trap: `react-router-dom` 7 moved to `createBrowserRouter`, but the plain `<BrowserRouter>`
   element form still works and is one file shorter.
4. [x] **`index.css`** — the tokens above as custom properties, a mobile-first base, and one
   `@media (min-width: 768px)` breakpoint. Set `:focus-visible` explicitly in the accent green:
   the default outline is nearly invisible on black, and that single omission fails the keyboard
   criterion of CP3.
5. [x] **`components/Header.jsx`** — wordmark, two nav links, the light/dark toggle and the
   sign-in button. Landmarks (`header`, `nav`) rather than `div`s;
   the active link marked with `aria-current="page"`. No hamburger — two links do not justify a
   menu, and the menu would bring its own accessibility work. Swapping the sign-in button for
   the signed-in address is step 19.
6. [x] **`components/MovieCard.jsx` and fixture data** — poster, title, year, IMDb rating, one
   action button. A film with no poster and one with no IMDb rating are both in the fixture,
   because both exist in the real data and both must render without breaking.
7. [x] **`pages/Search.jsx`, static** — the search field, the grid, the pagination, driven by
   the fixture. Four states rendered and reachable by hand: loading, results, empty, error.
   There is no idle state: the home page loads the popular list on mount, so it is never blank.
   Writing the states now costs nothing; retro-fitting them after the wiring is where they get
   skipped.
8. [x] **`pages/Favorites.jsx`, static** — the same cards with a remove button, plus the empty
   state. The duplication between the two pages became visible here and was extracted into
   `hooks/useMovieList.js` (the loading/ready/error triple and the fetch-once-on-mount effect,
   including the guard that drops a stale answer) and `components/MovieGrid.jsx`.
9. [x] **`components/AuthModal.jsx`** — native `<dialog>` opened with `showModal()`, so the focus
   trap, the backdrop, `Escape` and the focus returned to the trigger all come from the browser;
   two modes, sign in and create account; closing on a backdrop click; labels tied to inputs with
   `htmlFor`; errors in an `aria-live="polite"` region. The live password checklist lives in
   `lib/password.js` and mirrors `backend/app/utils.py:9-21` rule for rule — 8 characters, upper,
   lower, digit, and one of `!@#$%^&*(),.?":{}|<>_-` — with the server staying the authority. It
   is tied to the field with `aria-describedby` and deliberately not wrapped in `aria-live`,
   which would announce all five rules on every keystroke. The verdict is carried by a `✓` / `·`
   glyph as well as by colour: WCAG 1.4.1 forbids colour as the only signal.

**Verify:** `npm run dev` · both routes reachable, the browser back button works · the modal
opens, traps focus, closes on `Escape` and returns focus to the button that opened it · the
whole flow is usable with the keyboard alone · at 375 px nothing overflows horizontally.

## Day 3 (Fri 4 Sep) — the back-end, and the wiring

10. [x] **The virtualenv and `.env`, with nothing running** — `poetry install` from `backend/`,
    then copy `backend/.env_example` to `backend/.env`. `Settings()` runs at import time, so
    nothing under `app.` imports without it: not the app, not the tests, not Alembic. Set
    **`DATABASE_PORT=5555`** already, to match the container that arrives at step 15. The
    template keeps the 5432 default on purpose: it documents the shape of the file, not one
    machine's setup. No database runs at this point and none is needed — steps 11 to 14 are read
    from the shape of `/docs`, which touches neither Postgres nor Redis.
11. [x] **Fix the merge wreck** — `movie_list.py` carried a duplicated decorator and signature, so
    `import app.main` raised `IndentationError` and the whole test suite was dead. The `Depends()`
    form was kept; the bare `params: schemas.MovieSearch` form would have demanded a request body
    on a GET.
12. [x] **The contract the scope requires** — `MovieSearch` is now an optional `query` plus
    `page`: absent means the home page and keeps `discover/movie`, three characters or more go to
    `search/movie`, and the title is percent-encoded, or `Fast & Furious` splits into two query
    parameters and the search silently looks for something else. `MovieResponse` gains
    `poster_path` and loses `already_seen` and `personal_rating`, so `/movies/` no longer reads
    the watched table at all. `imdb_id` and `imdb_rating` are `Optional` with nullable columns,
    because a film absent from OMDB used to return 422 on add.
    **Beyond the plan:** the whole to-watch vocabulary became **favorites** — table, model,
    schema, module, route prefix and both handler names. Renaming the GET handler also cleared
    the OpenAPI collision with the identically named one in `watched_list.py`.
13. [x] **Close the cross-user leak** — `get_movies` used to read the `favorites` table with a
    bare `.all()`, so every user's rows were cross-referenced into every visitor's page. This is
    OWASP A01, found in our own code. The fix removed the query instead of filtering it:
    `/movies/` now opens no database session at all, takes no `get_current_user`, and answers
    with Postgres stopped. A filter can be forgotten on the next edit; a missing import cannot.
    The regression test moved to the private lists, where the filter still has to be right:
    `test_saved_lists.py` proves user B never reads and never deletes user A's rows.
14. [x] **Shrink the surface to what the product uses** — the `watched` feature (router, model,
    schema, French test file) and the `smth` stub were deleted: no screen called them, and the
    watched table was the last name containing a space. `PATCH /users/` went with them — the
    front-end never called it, and its `exclude_unset=True` bug had no way to surface. The two
    Redis calls are wrapped in `try/except redis.RedisError`, so a stopped Redis degrades to a
    cache miss instead of a 500 — CP6's exception-handling criterion in four lines.
    **To recover the watched feature**: `git show 6175ec6^:backend/app/routers/watched_list.py`.

**Verify:** `.venv/Scripts/pytest -q` · 46 passed, with neither Postgres nor Redis running.

## Day 4 (Mon 7 Sep) — the second list, the wiring, the evidence

15. [x] **Postgres and Redis, then one migration** — `compose.yml` at the repository root
    declares the two services and a named volume, Postgres published on host port **5555**. It
    reads the back-end's own `.env`, so the password the container is created with is the one
    the application uses: `docker compose --env-file backend/.env up -d`. The eight
    interview-era migrations were deleted and replaced by a single hand-written
    `0001_initial_schema`, and `Base.metadata` gained a naming convention so constraints stop
    getting random names. Verified with no database running: `alembic upgrade head --sql`
    renders the DDL, and it matches what `CreateTable` produces from the models.
16. [ ] **Seed script** — two users with populated lists. The CP5 *jeu d'essai*, and what proves
    the isolation fix by demonstration rather than by assertion. Needs Docker running.
17. [-] **TMDB/OMDB stand-in server** — dropped. Real keys sit in `.env`, which is the exact
    condition this step named for skipping it. Note for the defence: TMDB's v4 header scheme
    wants the *API Read Access Token*, the long `eyJ…` string, not the 32-character v3 key.
18. [x] **`src/api/client.js`** — one `request()` behind seven named functions. Base URL from
    `VITE_API_URL` with a `localhost:8000` fallback, the `Authorization: Bearer` header, 204
    read as `null` rather than parsed, and the single place that turns a non-2xx into a thrown
    `ApiError` carrying `status` and the FastAPI `detail` — including the 422 list, folded into
    one sentence. A `fetch` that rejects outright becomes status `0`, "the server did not
    answer".
19. [x] **The two contexts and the wiring** — `AuthContext` holds the token (in `localStorage`),
    the current user, `signIn`, `signUp`, `signOut` and the modal's open state; a token restored
    from storage is validated by `GET /users/me`, and a rejected one signs the session out.
    `SavedContext` holds both saved lists, loads them together with `Promise.all`, derives a
    `Set` of ids per list with `useMemo`, and owns every add and remove. There is no login route
    to redirect to, so saving a film while logged out opens the modal. `127.0.0.1:5173` was
    added to `origins` — only the `localhost` alias was there, and the browser treats the two as
    different origins.
20. [x] **Back-end tests** — 46, in four files, on **SQLite in memory**: the suite needs no
    Docker, no server and no test database to create. `test_user`, `test_login`,
    `test_saved_lists` (parametrized over both lists, so every rule is asserted twice) and
    `test_movies`, where TMDB is monkeypatched and Redis is made to raise on purpose. The
    `client` fixture now clears `my_app.dependency_overrides`, which used to leak across the
    whole session.
21. [x] **Front-end tests** — 19, in three files, one per layer: `password.test.js` for pure
    logic, `client.test.js` for the network boundary with `fetch` stubbed, and
    `MovieCard.test.jsx` for a rendered component. One per layer is a defensible answer to "what
    did you test and why", which juries ask more often than "how many".
22. [ ] **`docs/db/`** — `model.md` with the conceptual and logical models as Mermaid ER
    diagrams following Merise, `schema.sql` from `pg_dump --schema-only --no-owner`, `roles.sql`
    granting a `watchlist_app` role `SELECT, INSERT, UPDATE, DELETE` on the three tables and
    nothing else, and a backup taken and restored with the output pasted in. Needs Docker.
23. [ ] **`docs/mockups.md`** — the CP2 deliverable: the style guide (the token table above with
    its contrast ratios), block wireframes of the three screens at both widths, the screen-flow
    diagram in Mermaid with the modal drawn as an overlay, and screenshots at 375 px and
    1440 px. Both adaptations are explicitly required.
24. [ ] **Three dossier chapters** — `security.md` maps the app onto the OWASP Top 10 (A01 with
    the step 13 diff, A02 bcrypt, A03 SQLAlchemy parameterising, A07 JWT expiry and the password
    policy) and states the gaps honestly: no rate limiting, no refresh token, non-revocable
    tokens. `test-dataset.md` is the mandatory *jeu d'essai*. `tech-watch.md` is the mandatory
    *veille*: ANSSI, CERT-FR, OWASP, CNIL, then our own A01 find.
25. [x] **`README.md`, `docs/JOURNAL.md`, `docs/GLOSSARY.md`** — install, run, the environment
    table and the request flow in the README; one entry per session in the journal; each new
    term once in the glossary.
26. [ ] *(optional)* **`scripts/`** — the wrappers, rebuilt last. Windows detail that cost time
    before: the venv executables live in `.venv/Scripts`, not `.venv/bin`, so probe for both
    instead of hard-coding either.
27. [x] **The watch-later list** — the second feature the scope now asks for: a `watch_later`
    table, a `/watch-later` router, a `WatchLater` page and a third nav link. It is not the old
    `watched` feature returning — that one demanded a `personal_rating` on insert, which is
    exactly the extra input the scope removes. This one holds the same columns as `favorites`
    and needs no input beyond the click.
28. [x] **One code path for both lists** — `app/movie_lists.py` holds `list_movies`, `add_movie`
    and `remove_movie`, each taking the table as a parameter. The two routers are six four-line
    handlers over it. The point is not the lines saved: **`user_id` is filtered in one place**,
    so per-user isolation cannot be half-applied across six handlers. On the front, the same
    reasoning gives one `SavedPage` rendered twice. Dependencies became `Annotated` aliases —
    `DbSession`, `CurrentUser` — borrowed from `geo-enrich`, which also removes every `B008`.

29. [x] **`GET /health`** — not a liveness probe: the process answering at all already proves it
    is alive. It reports what the service can *reach* — `{status, database, cache}` — because
    the whole architecture turns on browsing working without either, so "which one is missing"
    is the useful question. Always 200: a 503 would mean "do not use this service", and the
    public film list disproves that. The database is probed through the routers' own session, so
    a check that passes while every handler fails is not possible. Path declared without a
    `prefix`, or a probe on `/health` would eat a 307 to `/health/`.

**Verify, end to end:** `docker compose --env-file backend/.env up -d`, then from `backend/`:
`.venv/Scripts/alembic upgrade head` · `.venv/Scripts/uvicorn app.main:my_app --reload --reload-dir app` · from
`frontend/`: `npm run dev` · search returns cards with posters · saving while logged out opens
the modal · signing in fills both lists · a second account sees none of the first's rows ·
stopping Redis leaves the search working.

---

## Running throughout

- [ ] **One branch per unit of work** — `<type>/<subject>` off `main`, then a PR. Never commit
  on `main`.
- [ ] **Tick a box only after the verification command has run** and its output was read.
- [ ] **Append to `docs/JOURNAL.md` at the end of each day** — what was done and the concept it
  taught. It is the raw material for the dossier's reflective chapters.
- [ ] **Anything noticed but out of scope goes to the Backlog**, never into the current diff.

## Backlog

What is left, and why it was left. This belongs in the dossier's "what is still to do", which
scores better than silence.

**Deliberate, with the reason recorded**

- **The tests run on SQLite, not Postgres.** The suite needs no infrastructure and finishes in
  six seconds, which is what makes it get run at all. The cost is that a Postgres-only behaviour
  — a `CASCADE` delete, a concurrent-insert race on the unique constraint — is not covered.
  `geo-enrich` carries the "tested against the real engine" story; here the trade is the right
  way round.
- **The token lives in `localStorage`.** Readable by any script on the origin, so an XSS becomes
  a session theft. The alternative, an `HttpOnly` cookie, brings CSRF protection and a same-site
  policy with it — more moving parts than this scope can defend. Written up in `security.md`.
- **`oxlint` reports five warnings.** Two are `only-export-components`: each context exports its
  provider and its hook from one file, which costs Fast Refresh and buys the reader one file per
  context instead of two. Three are `set-state-in-effect` on `setStatus('loading')` before a
  fetch, which is the documented shape for exactly this case.
- **The watched feature was deleted, not parked.** Recoverable with
  `git show 6175ec6^:backend/app/routers/watched_list.py`. Reviving it means an
  `UpdateUser`-style schema review and a table named `watched_movies`, without the space the old
  one carried.
- **The cache holds whole pages, not individual films.** A film in the popular list and the
  same film in a search result are enriched and stored twice. Caching `get_movie_details` per
  `tmdb_id` would share them, at the price of twenty Redis reads per page instead of one and a
  second TTL policy to reason about. Not worth it at this size.

**Real defects, not yet fixed**

- **`backend/postman/` is stale and should go.** The collection calls `/to-watch/` and
  `/watched/`, routes that no longer exist, and both it and its README are in French, which
  `CLAUDE.md` forbids in files. `/docs` is generated from the code and cannot drift the same
  way. Left in place because deleting files is Alex's call: `git rm -r backend/postman`.

- `OAuth2PasswordBearer(tokenUrl="login")` advertises a form-encoded login, but `login.py` takes
  JSON — the Authorize button in `/docs` cannot work. Testing a private route by hand needs the
  token pasted into `curl`, or the front-end.
- Emails are never normalised, so `Alice@x.com` and `alice@x.com` are two accounts, and an
  account created with a capital cannot be logged into in lower case.
- Unknown-email login returns instantly while a real one costs a bcrypt verify — user
  enumeration by timing.
- `utils.py` opens an `aiohttp.ClientSession` per film and sets no timeout, so a slow OMDB holds
  the request open with nothing to cut it short.
- `async def` handlers run blocking psycopg2 queries on the event loop.
- `frontend/public/placeholder.png` weighs 284 kB for an image that carries no information.
  Eco-design is graded and the number gets asked about; re-exporting it under 20 kB takes a
  minute.
- No `.gitattributes`. Any `.sh` committed from Windows can arrive with CRLF and die on a
  carriage return — an error that points everywhere except its cause. Matters from step 26.
- No CI, no pre-commit, no LICENSE.
- `origin/prep-entretien` is a dead remote branch from the repository's interview past.
