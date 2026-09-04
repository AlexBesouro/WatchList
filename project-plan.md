<!-- markdownlint-disable MD029 -->
<!-- Steps are numbered continuously 1..26 across the day sections so that a step can be
     cited by its number alone. MD029 would demand each list restart at 1. -->

# WatchList — roadmap

`[ ]` open · `[x]` done, and the verification command was run and its output seen.

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

Two pages and one modal. Every screen exists to exercise a competency; nothing is added
because it would be nice.

- **Search `/`** — one text field, a grid of film cards, pagination. Card shows poster, title,
  year, IMDb rating, and one button: add to favourites.
- **Favourites `/favorites`** — the same cards with a remove button. Logged out, it opens the
  modal instead of rendering an empty list.
- **Auth modal** — a native `<dialog>` over either page, two tabs: sign in (2 fields), sign up
  (4 fields: email, password, first name, last name).

**Favourites is the `movies_to_be_watched` table.** The `watched_movies` table needs a
`personal_rating` on insert, which is exactly the extra input the scope removes. It stays in
the database, in the API and under test — it is CP5 and CP7 evidence — but the SPA never
touches it.

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

10. [ ] **`.env` and a root `compose.yml`** — `Settings()` runs at import time, so nothing in
    `backend/` imports without `.env`. Copy `backend/.env_example` and set
    **`DATABASE_PORT=5442`**: the template says 5432 and contradicts the container. The compose
    file declares postgres and redis and sits at the repository root, where `docker compose up
    -d` finds it with no `-f`.
11. [ ] **Fix the merge wreck** — `backend/app/routers/movie_list.py:18-21` carries a duplicated
    decorator and signature, so `import app.main` raises `IndentationError` and the whole test
    suite is dead. Keep the `Depends()` form; the bare `params: schemas.MovieSearch` form would
    demand a request body on a GET.
12. [ ] **The three schema changes the scope requires** — `MovieSearch` becomes an **optional**
    `query: str | None` plus `page: int`. An empty query keeps the existing `discover/movie`
    call, which is what fills the home page with popular films; a query of three characters or
    more goes to `search/movie` instead;
    `poster_path` is added to `MovieResponse` and read from the raw result at
    `movie_list.py:70`; `ToBeWatched.imdb_id` and `imdb_rating` become `Optional` with nullable
    columns, because a film absent from OMDB currently returns 422 on add.
13. [ ] **Close the cross-user leak** — `get_movies` has no `get_current_user` dependency and
    reads both tables with `.all()` (`movie_list.py:19,55,57`), so every user's rows are
    cross-referenced. This is OWASP A01, found in our own code; write the before and after down
    as it is fixed, because it is the whole of the security-watch chapter at step 24. Add one
    regression test: user B never sees user A's rows.
14. [ ] **Three small repairs** — wrap the two Redis calls (`movie_list.py:29,43`) in
    `try/except redis.RedisError` so a stopped Redis degrades to a cache miss instead of a 500,
    which is CP6's exception-handling criterion in four lines; add
    `DELETE /to-watch/{tmdb_id}`, mirroring `watched_list.py:45`; delete `app/routers/smth.py`
    and its mount in `main.py:3,17`.
15. [ ] **One migration** — delete all 8 files in `backend/alembic/versions/` (two have broken
    downgrades) and generate a single `initial schema`. Do it here, not later: the table renames
    (`"watched movies"` and `"movies to be watched"` carry spaces) and the nullable columns from
    step 12 need a migration anyway, and one is cheaper than two. Add a naming convention to
    `Base.metadata` so constraints stop getting random names.
16. [ ] **Seed script** — two users with populated lists. This is the CP5 *jeu d'essai*, and the
    two accounts are what proves the step 13 isolation fix by demonstration rather than
    assertion.
17. [ ] **TMDB/OMDB stand-in server** — a small FastAPI app on port 9100 serving `search/movie`,
    `external_ids` and the OMDB rating, so the SPA runs with no API keys. Skip only if real keys
    are on hand.
18. [ ] **`src/api/client.js`** — one fetch wrapper: base URL from `VITE_API_URL`, the
    `Authorization: Bearer` header, and the single place that turns a non-2xx into a thrown
    `ApiError` carrying `status` and the FastAPI `detail`. Every error message on screen comes
    from here. Trap: the routers register `"/"`, so call `/movies/`, not `/movies`, or eat a 307
    that drops the Authorization header.
19. [ ] **`src/context/AuthContext.jsx` and the wiring** — token, current user, `login()`,
    `logout()`, and `openAuth()`: there is no login route to redirect to, so an
    authenticated-only action on a logged-out session opens the modal and replays the action
    after success. Swap the fixtures for real calls on both pages. The token goes in
    `localStorage`; the trade-off is written into `docs/security.md` at step 24 rather than left
    unexamined. Add `127.0.0.1:5173` to `origins` in `main.py:19` — only the `localhost` alias
    is there.

**Verify:** `docker compose up -d`, then from `backend/`: `.venv/Scripts/alembic upgrade head`,
the seed script, `.venv/Scripts/uvicorn app.main:my_app --reload` · search returns cards with
posters · adding while logged out opens the modal, and the add completes after signing in ·
stopping Redis degrades the search instead of returning 500 · logging in as the second seeded
user shows none of the first user's rows.

## Day 4 (Sat 5 Sep) — the evidence

20. [ ] **Minimal back-end tests** — `backend/tests/test_login.py` is 0 bytes. Add login
    success, wrong password, unknown email, a `/to-watch` create-read-delete cycle, a 401 on a
    missing token, and the isolation test from step 13. Reset `my_app.dependency_overrides` in
    the `client` fixture: `conftest.py:36` leaks it across the whole session.
21. [ ] **Three Vitest tests, no more** — the password validator rejects a weak input,
    `client.js` throws `ApiError` on a 401, and `MovieCard` renders the "in favourites" state
    from a stubbed prop. One per layer — pure logic, the network boundary, a rendered component
    — which is a defensible answer to "what did you test and why", a question juries ask more
    often than "how many".
22. [ ] **`docs/db/`** — `model.md` with the conceptual and logical models as Mermaid ER
    diagrams following Merise, `schema.sql` produced by `pg_dump --schema-only --no-owner` so it
    cannot drift from the code, `roles.sql` granting a `watchlist_app` role `SELECT, INSERT,
    UPDATE, DELETE` on the three tables and nothing else, and a backup taken and restored with
    the output pasted in. The role and the restore are literal CP5 criteria that most candidates
    skip.
23. [ ] **`docs/mockups.md`** — the CP2 deliverable, replacing the cancelled Figma file: the
    style guide (the token table above, with its contrast ratios), block wireframes of the three
    screens at desktop and mobile width, the screen-flow diagram in Mermaid with the modal drawn
    as an overlay any authenticated-only action opens, and screenshots at 375 px and 1440 px.
    Both adaptations are explicitly required, in the dossier and in the defence.
24. [ ] **Three dossier chapters** — `security.md` maps the app onto the OWASP Top 10 (A01 with
    the step 13 diff, A02 bcrypt, A03 SQLAlchemy parameterising, A07 JWT expiry and the password
    policy) and states the gaps honestly: no rate limiting, no refresh token, non-revocable
    tokens. `test-dataset.md` is the mandatory *jeu d'essai* on one feature — add a film to
    favourites — as input, expected, obtained, and the analysis of the gap. `tech-watch.md` is
    the mandatory *veille*: ANSSI, CERT-FR, OWASP, CNIL, then our own A01 find.
25. [ ] **`README.md`, `docs/JOURNAL.md`, `docs/GLOSSARY.md`** — the README is two lines today
    and needs install, run, an environment-variable table and the request flow. The other two are
    mandated by `CLAUDE.md` and do not exist.
26. [ ] *(optional)* **`scripts/`** — the wrappers, rebuilt last, once every command they wrap
    has been written out and verified. Windows detail that cost time before: the venv
    executables live in `.venv/Scripts`, not `.venv/bin`, so probe for both instead of
    hard-coding either. Dropped without regret if the clock runs out.

**Verify:** a cold start on a clean machine following the README alone · `pytest` and
`npm test` both green · the restore brings the seeded rows back · all three screens
photographed at both widths.

---

## Running throughout

- [ ] **One branch per unit of work** — `<type>/<subject>` off `main`, then a PR. Never commit
  on `main`.
- [ ] **Tick a box only after the verification command has run** and its output was read.
- [ ] **Append to `docs/JOURNAL.md` at the end of each day** — what was done and the concept it
  taught. It is the raw material for the dossier's reflective chapters.
- [ ] **Anything noticed but out of scope goes to the Backlog**, never into the current diff.

## Backlog

Real defects found in the audit that the remaining days cannot absorb. They belong in the
dossier's "what is left to do", which scores better than silence.

- `PATCH /users/` takes `CreateUser`, whose four fields are all required, so `exclude_unset=True`
  (`user.py:52`) excludes nothing and a partial body returns 422. It needs an `UpdateUser`
  schema. Its `db.commit()` (`user.py:72`) is unwrapped.
- `OAuth2PasswordBearer(tokenUrl="login")` advertises a form-encoded login, but `login.py:11`
  takes JSON — the Authorize button in `/docs` cannot work.
- Emails are never normalised (`models.py:14`), so `Alice@x.com` and `alice@x.com` are two
  accounts and a capitalised signup cannot log in.
- Unknown-email login returns instantly while a real one costs a bcrypt verify — user
  enumeration by timing (`login.py:17`).
- `utils.py:37-57` opens an `aiohttp.ClientSession` per film, never uses `async with` on the
  responses, and has no timeout and no `raise_for_status()`.
- `async def` handlers run blocking psycopg2 queries on the event loop (`movie_list.py:19,55`).
- `except IntegrityError` reports 409 "already exists" for any integrity failure, including a
  `NOT NULL` violation (`watched_list.py:32`, `to_be_watched.py:33`).
- `schemas.ToBeWatched` lacks `from_attributes` while serving as an ORM `response_model`
  (`to_be_watched.py:40`).
- No OpenAPI metadata: no title, version, tags or `operation_id`; two handlers share the name
  `watched_movies`, which poisons any generated client.
- `alembic.ini:65` holds a dead literal f-string with a typo — `setting.` for `settings.`.
- No `.gitattributes`. Any `.sh` file committed from Windows can arrive with CRLF and die as
  `$'\r': command not found`, an error that points everywhere except its cause. Matters from
  step 26.
- `frontend/public/placeholder.png` weighs 284 kB for an image that carries no
  information. It is cached after the first request, but eco-design is graded and the
  number gets asked about; re-exporting it under 20 kB takes a minute.
- No CI, no pre-commit, no LICENSE.
- The `watched_movies` table has no UI. Fine for now — it is API and test evidence — but the
  README must say so, or a jury reads it as dead code.
- `origin/prep-entretien` is a dead remote branch from the repository's interview past.
- `backend/postman/README.md` and `backend/tests/test_watched.py` are in French; `CLAUDE.md`
  requires English in files, and touching one means translating it.
