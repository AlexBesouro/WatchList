# Work journal

One entry per session: what was done, and the concept it taught.

---

## Mon 7 Sep 2026 — two zones, two lists, one code path

### What was done

The project was cut down to the structure it was supposed to have, then finished.

**The scope, stated in two lines.** Browsing is public; saving needs an account. Everything else
followed from that. `GET /movies/` lost its database session, its `models` import and its user:
it is now a pure TMDB call behind a Redis cache. That is what closed the cross-user leak — the
public list used to read the whole `favorites` table — and it is also why the home page now works
with Postgres stopped.

**A second list.** `watch_later` joined `favorites`: same columns, same rules, its own table, its
own router, its own page. Two tables rather than one with a flag, because a film can sit in both
and a flag turns "in both" into a state to encode.

**One code path for both.** `app/movie_lists.py` holds `list_movies`, `add_movie` and
`remove_movie`, each taking the table as a parameter; the two routers are six four-line handlers
over it. On the front, one `SavedPage` is rendered twice. The saving is not in the line count —
it is that `user_id` is filtered in exactly one place.

**The wiring.** `client.js` became the only file that touches the network. `AuthContext` holds
the token and validates a restored one against `GET /users/me`; `SavedContext` holds both lists,
loads them with one `Promise.all`, and owns every add and remove. Saving a film while signed out
opens the modal.

**The evidence.** 46 back-end tests on SQLite in memory and 19 front-end tests under Vitest, both
runnable with nothing else running. `ruff check` and `ruff format` clean. One hand-written
migration replacing eight, verified against the models without a database. A `compose.yml` that
reads the back-end's own `.env`, so the container and the application cannot disagree about the
password.

**Two real bugs found on the way.** TMDB sends `release_date: ""` for a film with no announced
date, which a non-nullable `date` field turns into a 500 on the home page — the column, the
schema and the router all had to accept it. And `SavedMovie` had no `poster_path`, so every saved
film would have rendered as a placeholder.

**A cache that cached the wrong half.** `/movies` stored the TMDB page and then enriched it
on every single request — twenty films, two upstream calls each. A hit saved one request out of
forty-one, so a warm cache was as slow as a cold one. Caching the finished list instead: 1.255 s
to 0.003 s, measured against the real TMDB.

### What it taught

**Removing a query beats filtering it.** The leak could have been fixed with
`.filter(user_id == current_user.user_id)`. Deleting the query instead made the endpoint
stateless: there is no user in scope to forget to filter on, and the next person to edit the
handler cannot reintroduce the bug. A filter is a promise; a missing import is a fact.

**The parameter that removes a duplicate is often the table itself.** Two routers that differ
only in which model they touch are not two features. Passing the model as an argument turned six
handlers into three functions and made the security rule — filter on `user_id` — a single line
that every path goes through.

**Annotated dependencies.** `DbSession = Annotated[Session, Depends(get_db)]`, borrowed from
`geo-enrich`. Every signature got shorter, and the whole `B008` category disappeared from ruff
without a single `# noqa`.

**Testing on SQLite is a trade, not a shortcut** — as long as it is named. The suite runs in six
seconds with no Docker, which is what makes it get run. What it cannot see is anything
engine-specific: a `CASCADE`, a concurrency race on a unique constraint. That went into the
Backlog with its reason, not into silence.

**Cache the result, not the input.** The bug was invisible because the code *looked* cached:
there was a key, a TTL, a guarded Redis and two log lines proving it ran. What it cached was the
cheap 2% of the work. The question to ask of any cache is not "does it store something" but
"what does a hit actually skip".

**A default that is portable beats one that is correct on one engine.** `server_default=func.now()`
looked right and passed on Postgres; on SQLite it stores a timestamp into a `DATE` column and
every test died on `Invalid isoformat string`. `func.current_date()` says what the column
actually is.
