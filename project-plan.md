<!-- markdownlint-disable MD029 -->
<!-- Step numbers run continuously across the four days so a step can be cited by number alone. -->

# Tasks — WatchList

Roadmap for the DWWM study project, **2 → 5 September 2026**. Scope authority:
`../projet_dwwm/REV2_DWWM_V04_02072024.pdf` (the evaluation reference) and
`../projet_dwwm/REAC_DWWM_V04_02072024.pdf` (the competency wording).
One step = one branch `<type>/<subject>` off `main` → PR → merge.

Legend: `[x]` verified · `[ ]` to do.
A box is ticked only when its verification command has run **and its output was seen**.

---

## What this project has to prove

Six competencies. Their titles are quoted verbatim from the REAC, because the dossier must
reproduce them word for word.

| | Competency (REAC verbatim) | Where it is earned |
| --- | --- | --- |
| CP2 | *Maquetter des interfaces utilisateur web ou web mobile* | Figma: 2 pages + 1 modal, each at 2 widths, + screen-flow diagram |
| CP3 | *Réaliser des interfaces utilisateur statiques web ou web mobile* | React + hand-written CSS, responsive, accessibility, eco-design |
| CP4 | *Développer la partie dynamique des interfaces utilisateur* | fetch → REST API, validation, error handling, Vitest |
| CP5 | *Mettre en place une base de données relationnelle* | Conceptual/logical/physical models, SQL script, roles, test dataset, backup |
| CP6 | *Développer des composants d'accès aux données SQL et NoSQL* | SQLAlchemy (SQL) + Redis key/value (NoSQL) |
| CP7 | *Développer des composants métier côté serveur* | routers, security, OOP, tests |

**Scope ceiling: 2 pages and 1 modal.** A Search page and a Favorites page (two tabs: watched
and to-watch), with sign-in and sign-up in a modal dialog opened from the header. Theme: black
with a single green accent. No feature is added to satisfy an idea; every screen exists to
exercise a competency.

**The `scripts/` folder was deleted and is rebuilt from scratch at the end (step 33).** Until
then every command is written out in full. Three things that lived there are not shell
convenience and cannot wait: the compose file (step 3), the seed data (step 15) and the
TMDB/OMDB stand-in server (step 18). Each is rebuilt at the point it is first needed.

---

## Day 1 (Wed 2 Sep) — The back-end runs, and is safe to point a browser at

The back-end does not currently start: `app/routers/movie_list.py:18-21` carries a duplicated
decorator and signature from merge `93667f9`, so every import of `app.main` raises
`IndentationError`. Nothing below can be verified until step 4 lands.

1. [x] **Write this roadmap** — `project-plan.md`, the file you are reading. `CLAUDE.md` treats
   it as the session-start read, and it was empty.
2. [x] **Adopt Poetry as the dependency manifest** — same tooling as `stage-alex`, so one
   defence does not have to account for two package managers. `pyproject.toml` with
   `package-mode = false`, `[tool.pytest.ini_options]` carrying `testpaths` and
   `pythonpath = ["."]`, a `dev` group, `poetry.toml` pinning the venv in-project, and a
   committed `poetry.lock`. `bcrypt` stays pinned at exactly 4.0.1 — passlib 1.7.4 raises on
   4.1 and later. Reasoning recorded in `notes/decisions.md`.
3. [ ] **Write `.env` and a root `compose.yml`** — `Settings()` runs at import time, so nothing
   imports without `.env`; copy `.env_example` and set **`DATABASE_PORT=5442`**, since the
   template says 5432 and contradicts the container. The compose file declares postgres and
   redis and lives at the repository root, where `docker compose up -d` finds it with no `-f`
   flag. It is also the CP1 evidence: *les conteneurs implémentent les services requis*.
4. [ ] **Fix the merge wreck** — `app/routers/movie_list.py:18-21`: drop the first decorator
   and signature pair, keep `params: schemas.MovieSearch = Depends()`, the query-string form
   introduced by commit `9805e71`.
5. [ ] **Close the cross-user leak** — `GET /movies/` has no auth dependency
   (`movie_list.py:19`) and reads every user's rows with `.all()` (`movie_list.py:55,57`), so
   it hands out other people's `personal_rating`. Add `get_current_user` and filter both
   queries by `current_user.user_id`. Save the before and after: this is OWASP A01 Broken
   Access Control found in our own code, and it is the dossier's security-watch chapter.
6. [ ] **Add `DELETE /to-watch/{tmdb_id}`** — the only endpoint the SPA needs and does not
   have; Favorites must delete from both tabs. Mirror `watched_list.py:45`, which already
   filters by owner, and rename its path parameter `id` → `tmdb_id` (it is matched against
   `tmdb_id`, not the primary key).
7. [ ] **Make Redis a cache, not a dependency** — `movie_list.py:29,43` are unguarded, so Redis
   down means HTTP 500. Wrap in `try/except redis.RedisError` and fall through to TMDB. Four
   lines, and it is the CP6 criterion on handling exception cases.
8. [ ] **Delete the leftovers** — `app/routers/smth.py`, a public stub returning `"Rabotaet"`,
   mounted at `main.py:3,17`.
9. [ ] **Fill the test gaps** — `tests/test_login.py` is 0 bytes. Add login success, wrong
   password, unknown email; a `/to-watch` create-read-delete cycle; a 401 on a missing token;
   and the regression test for step 5. Reset `my_app.dependency_overrides` in the `client`
   fixture — `conftest.py:36` leaks it across the whole session.

**Verify:** `docker compose up -d` then `.venv/Scripts/alembic upgrade head` ·
`.venv/Scripts/pytest -q` green · `.venv/Scripts/uvicorn app.main:my_app --reload` →
`http://localhost:8000/docs` lists the routes without `/smth` and with the new DELETE.

## Day 2 (Thu 3 Sep) — CP2 and CP5, the two that cannot be improvised

Neither of these is code, and neither can be produced the night before. Juries check them
first.

10. [ ] **Mockups in Figma** — the two pages and the auth modal, each at **desktop and mobile**
    width. Both adaptations are explicitly required, in the dossier and in the defence. Fix the
    visual identity here: black background, one green accent, a 2-step type scale, one spacing
    unit. Choose the green with a contrast checker now, not in CSS later — a mid green such as
    `#22c55e` clears 4.5:1 on `#0a0a0a`, a dark forest green does not.
11. [ ] **Screen-flow diagram** — a separate, explicitly required deliverable, not a
    nice-to-have. Search to Favorites and back, with the auth modal drawn as an overlay that
    any authenticated-only action opens, and the return arrow to the action the user was
    attempting. Mermaid in `docs/mockups.md`.
12. [ ] **Squash the migrations** — delete all 8 files in `alembic/versions/` (two have broken
    downgrades: `ada860ce836a:22-27` drops unnamed constraints, `dd1da675dc2e:33` drops the
    wrong constraint name), rename the two space-containing tables in `app/models.py` to
    `watched_movies` and `movies_to_watch`, add a naming convention to `Base.metadata`, then
    generate one `initial schema` revision. This wipes the local data, which is why the seed
    script comes back at step 15.
13. [ ] **`docs/db/schema.sql`** — the creation script the dossier requires, taken from the
    clean database with `pg_dump --schema-only --no-owner`. Generated, not hand-written, so it
    cannot drift from the code.
14. [ ] **`docs/db/roles.sql`** — a `watchlist_app` role holding `SELECT, INSERT, UPDATE,
    DELETE` on the three tables and nothing else. A literal CP5 criterion that almost every
    candidate skips.
15. [ ] **Rebuild the seed script** — `scripts/seed.py` was deleted with the rest of the
    folder, but the data it produced is a graded deliverable: CP5 asks for *un jeu d'essai
    complet dans une base de données de test*. Two users with populated lists, so that the
    isolation fixed in step 5 can be demonstrated rather than asserted.
16. [ ] **Backup and restore** — `pg_dump` and `pg_restore` against the container, run both
    ways to prove the restore works, and write the procedure into `docs/db/backup.md`. Another
    literal CP5 criterion. The convenience wrapper lands later, at step 33.
17. [ ] **Conceptual, logical and physical data models** — Merise, following
    `../projet_dwwm/Cheatsheet-merise.pdf`: entities singular and uppercase, identifiers
    underlined, cardinalities shown. Three tables only. Mermaid ER diagrams in
    `docs/db/model.md`; the physical model is the `schema.sql` from step 13.

**Verify:** `docker compose down -v && docker compose up -d`, then `alembic upgrade head` and
the seed script, rebuild the database from zero · `watchlist_app` can read and write but not
`DROP` · a restore from the dump brings the seeded rows back.

## Day 3 (Fri 4 Sep) — React: skeleton, auth modal, search page

18. [ ] **Rebuild the TMDB/OMDB stand-in server** — a small FastAPI app on port 9100 mimicking
    the two upstreams, so the SPA can be built and demonstrated with no API keys. Skip only if
    real TMDB and OMDB keys are on hand; the front-end cannot be exercised without one or the
    other.
19. [ ] **Scaffold `frontend/`** — Vite React template plus `react-router-dom`. Layout
    `src/{api,components,context,pages}`. Add `node_modules/` and `dist/` to `.gitignore`.
20. [ ] **`src/api/client.js`** — one fetch wrapper: base URL from `VITE_API_URL`, the
    `Authorization: Bearer` header, and the single place that turns a non-2xx into a thrown
    `ApiError` carrying `status` and the FastAPI `detail`. Every screen's error message comes
    from here. Mind the trailing slash: the routers register `"/"`, so call `/movies/`, not
    `/movies`, or eat a 307.
21. [ ] **`src/context/AuthContext.jsx`** — token, current user, `login()`, `logout()`, and
    `openAuth()`. There is no login route to redirect to, so an authenticated-only action on a
    logged-out session opens the modal instead. The token goes in `localStorage`; write the
    trade-off into `docs/security.md` rather than leaving it unexamined.
22. [ ] **`src/components/AuthModal.jsx`** — one dialog, two tabs. Client-side validation
    mirroring `app/utils.py:9-21` (at least 8 characters, upper, lower, digit, special) shown
    live, with the server staying the authority; errors in an `aria-live="polite"` region,
    labels tied to inputs with `htmlFor`. Build it on the native `<dialog>`: `showModal()`
    gives the focus trap, the backdrop and `Escape` for free, and focus must return to the
    trigger on close.
23. [ ] **Search page (`/`)** — `GET /movies/` with year, language and page controls. Cards
    show title, OMDB rating and the two flags the API computes (`already_seen`, `watch_later`),
    plus buttons posting to `/watched/` and `/to-watch/`. Logged out, the cards still render
    but the buttons call `openAuth()`. Loading and empty states explicit: the endpoint is slow
    on a cache miss.

**Verify:** an add button while logged out opens the modal; registering in it closes the modal
and completes the original action · `Escape` closes it and focus lands back on the trigger ·
with the API stopped the page shows a readable error, not a blank screen.

## Day 4 (Sat 5 Sep) — Favorites, responsive, accessibility, dossier material

24. [ ] **Favorites page (`/favorites`)** — two tabs over `GET /watched/` and `GET /to-watch/`,
    delete on both (step 6), `personal_rating` displayed. Tabs as real buttons carrying
    `aria-selected`, not styled divs. Reached logged out, it opens the modal instead of
    rendering an empty list.
25. [ ] **CSS pass** — one `index.css`: custom properties for the black-and-green identity,
    mobile-first, a single `@media (min-width: 768px)` breakpoint, contrast at least 4.5:1,
    Grid for the film list and Flexbox for the bars. On a dark theme the focus ring is the
    trap — the default outline is nearly invisible on black, so set `:focus-visible`
    explicitly in the accent green.
26. [ ] **Accessibility pass** — `lang` on `<html>`, one `<h1>` per page, landmarks, `alt` on
    every poster, full keyboard traversal, errors announced, and the modal's focus behaviour
    re-checked after the CSS lands. Record what was checked in `docs/accessibility.md` against
    the RGAA, alongside the eco-design decisions: no UI framework, no icon font, posters
    requested at `w200`, the Redis cache avoiding repeat upstream calls.
27. [ ] **`docs/test-dataset.md`** — the mandatory chapter on the most representative feature.
    Take *add a film to my watched list*: input data, expected data, obtained data, and the
    analysis of any gap.
28. [ ] **`docs/tech-watch.md`** — the other mandatory chapter. Sources: ANSSI, CERT-FR, OWASP,
    CNIL. Then the real find: the step 5 cross-user leak, its OWASP A01 classification, and the
    fix diff.
29. [ ] **`docs/security.md`** — the app mapped onto the OWASP Top 10: A01 (the fix and the
    per-user filters), A02 (bcrypt, no plaintext), A03 (SQLAlchemy parameterises, no
    string-built SQL), A07 (JWT expiry, password policy) — plus the honest gaps: no rate
    limiting, no refresh token, five-hour non-revocable tokens.
30. [ ] **`docs/deployment.md` and an app Dockerfile** — CP8's written procedure and documented
    scripts. Add `api` and `frontend` services to `compose.yml` behind a profile, and prove
    `docker compose --profile app up` serves the SPA.
31. [ ] **Vitest — three tests, no more** — the password validator rejects a weak input,
    `client.js` throws `ApiError` on a 401, the film list renders the "already seen" flag from
    a stubbed response. One per layer: pure logic, the network boundary, a rendered component.
    That is a defensible answer to "what did you test and why", which a jury asks more often
    than "how many". Run last, once the pages are stable.
32. [ ] **Screenshots, README and the two mandated docs** — both pages and the open modal at
    375 px and 1440 px, for the dossier and the slide deck. The README is two lines today and
    needs install, run, an environment-variable table and the architecture. `docs/JOURNAL.md`
    and `docs/GLOSSARY.md` are mandated by `CLAUDE.md` and do not exist.
33. [ ] **Rebuild `scripts/`** — the convenience layer, written last, once every command it
    wraps is known to work. One entry point per concern: infrastructure, the app, the tests,
    the seed, the backup. Windows detail that cost time before: the venv executables live in
    `.venv/Scripts`, not `.venv/bin`, so probe for both instead of hard-coding either.

**Verify:** a cold start on a clean machine following the README alone · the back-end suite and
`npm test` both green · both pages and the modal photographed at both widths.

## If time remains

Dropped first, and dropped without regret — nothing here blocks the defence.

- [ ] *(bonus)* **Rename the two misnamed handlers** — `to_be_watched.py:14` is called
  `add_watched_movie` and `:41` is called `watched_movies`, colliding with `watched_list.py` in
  the OpenAPI document and poisoning any generated client.
- [ ] *(bonus)* **OpenAPI metadata** — title, version, tags, `operation_id`. `FastAPI()` at
  `main.py:11` takes no arguments at all.

---

## Running throughout

- [ ] **One branch per step** — `<type>/<subject>` off `main`, then a PR. Never commit on
  `main`.
- [ ] **Tick a box only after its verification command has run**, and only if the output was
  actually read.
- [ ] **Append to `docs/JOURNAL.md` at the end of each day** — what was done, and the concept
  it taught. It is the raw material for the dossier's reflective chapters.
- [ ] **Anything noticed but out of scope goes to the Backlog below**, never into the current
  diff.

## Backlog

Real defects found while auditing the repository, which four days do not have room for. They
belong in the dossier's "what is left to do", which scores better than silence.

- `PATCH /users/` takes `CreateUser`, whose four fields are all required, so
  `exclude_unset=True` (`user.py:52`) excludes nothing and a partial body returns 422. It needs
  an `UpdateUser` schema with optional fields. Its `db.commit()` (`user.py:72`) is unwrapped,
  unlike the one in `create_user`.
- Emails are never normalised (`models.py:14`), so `Alice@x.com` and `alice@x.com` are two
  accounts, and someone who signs up with a capital cannot log in with lowercase.
- Unknown-email login returns instantly while a real one costs a bcrypt verify — user
  enumeration by timing (`login.py:17`).
- `utils.py:37-57` opens an `aiohttp.ClientSession` per film, about 20 per page, never uses
  `async with` on the responses, and has no timeout and no `raise_for_status()`.
- `async def` handlers run blocking psycopg2 queries on the event loop (`movie_list.py:19,55`).
- `except IntegrityError` reports 409 "already exists" for any integrity failure, including a
  `NOT NULL` violation (`watched_list.py:32`, `to_be_watched.py:33`).
- `schemas.ToBeWatched` lacks `from_attributes` while serving as an ORM `response_model`
  (`to_be_watched.py:40`).
- `alembic.ini:65` holds a dead literal f-string with a typo — `setting.` for `settings.`.
- **No `.gitattributes`** — line endings are left to each machine's `core.autocrlf`. Harmless
  for Markdown, fatal for a shell script: a `.sh` checked out with CRLF fails as
  `$'\r': command not found`, an error that points nowhere near its cause. Matters from step 33.
- No pre-commit hook, no CI, no LICENSE. Ruff is installed but never run automatically.
- `postman/README.md` is French, while `CLAUDE.md` requires English in files. Touching it means
  translating it in the same change.
