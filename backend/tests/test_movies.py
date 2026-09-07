import logging

import aiohttp
import pytest
import redis

from app import cache, utils
from app.routers import movie_list

# A TMDB discover page cut down to the four keys we read. The second film has
# neither a date nor a poster, which real answers do contain.
TMDB_PAGE = {
    "results": [
        {
            "id": 329865,
            "original_title": "Arrival",
            "release_date": "2016-11-11",
            "poster_path": "/arrival.jpg",
        },
        {
            "id": 111,
            "original_title": "Not Out Yet",
            "release_date": "",
            "poster_path": None,
        },
    ]
}


@pytest.fixture
def offline_tmdb(monkeypatch):
    """Replace both upstream calls, so the test never leaves the machine."""

    async def fake_fetch(url, headers=None):
        return TMDB_PAGE

    async def fake_details(tmdb_id, headers):
        return ("tt2543164", 7.9) if tmdb_id == 329865 else (None, None)

    monkeypatch.setattr(utils, "fetch_data", fake_fetch)
    monkeypatch.setattr(utils, "get_movie_details", fake_details)
    # The cache is neutralised too: a Redis left running from another session
    # would answer with yesterday's films and the assertions would drift.
    monkeypatch.setattr(movie_list, "cache_get", lambda key: None)
    monkeypatch.setattr(movie_list, "cache_set", lambda key, value, ttl: None)


# --- 1. The public list is public -------------------------------------------
def test_movies_needs_no_account(client, offline_tmdb):
    """No Authorization header, no database session, and still a full page."""
    response = client.get("/movies")

    assert response.status_code == 200
    films = response.json()
    assert [film["title"] for film in films] == ["Arrival", "Not Out Yet"]
    assert films[0]["imdb_rating"] == 7.9


# ------------
def test_an_unreleased_film_does_not_break_the_page(client, offline_tmdb):
    """TMDB sends an empty string for a date it has not got; that must read as null."""
    films = client.get("/movies").json()

    assert films[1]["release_date"] is None
    assert films[1]["poster_path"] is None


# ------------
def test_no_saved_flag_is_returned(client, offline_tmdb):
    """The endpoint reads no user data, so it cannot say whether a film is saved."""
    films = client.get("/movies").json()

    assert "is_favorite" not in films[0]


# --- 2. The query string is checked before TMDB is called -------------------
@pytest.mark.parametrize("query", ["?query=ab", "?page=0", "?page=501"])
def test_a_bad_query_is_refused(client, query):
    """422 from Pydantic, so a pointless upstream call is never made."""
    assert client.get("/movies" + query).status_code == 422


# --- 3. When TMDB is down ---------------------------------------------------
def test_tmdb_failure_is_an_empty_page(client, monkeypatch):
    """An empty list and not a 500: an upstream being down is not our own bug."""

    async def boom(url, headers=None):
        raise aiohttp.ClientError("TMDB is unreachable")

    monkeypatch.setattr(utils, "fetch_data", boom)
    monkeypatch.setattr(movie_list, "cache_get", lambda key: None)

    response = client.get("/movies")

    assert response.status_code == 200
    assert response.json() == []


# --- 4. When Redis is down --------------------------------------------------
def test_an_unreachable_redis_reads_as_a_miss(monkeypatch):
    """The cache guard is what lets the whole page work with no Redis at all."""

    def broken(*args, **kwargs):
        raise redis.ConnectionError("Redis is unreachable")

    monkeypatch.setattr(cache.red, "get", broken)

    assert cache.cache_get("any-key") is None


# ------------
def test_an_unreachable_redis_does_not_break_a_write(monkeypatch):
    """The films are already fetched, so a failed write costs only the cache."""

    def broken(*args, **kwargs):
        raise redis.ConnectionError("Redis is unreachable")

    monkeypatch.setattr(cache.red, "set", broken)

    assert cache.cache_set("any-key", {"a": 1}, 10) is None


# --- 5. The cache key tells the pages apart ---------------------------------
def test_the_home_page_and_a_search_for_none_use_different_keys(client, monkeypatch):
    """ "None" is a three-letter word, so it passes validation and reaches the key."""
    seen = []

    async def fake_fetch(url, headers=None):
        return TMDB_PAGE

    async def fake_details(tmdb_id, headers):
        return (None, None)

    monkeypatch.setattr(utils, "fetch_data", fake_fetch)
    monkeypatch.setattr(utils, "get_movie_details", fake_details)
    monkeypatch.setattr(movie_list, "cache_get", lambda key: seen.append(key))
    monkeypatch.setattr(movie_list, "cache_set", lambda key, value, ttl: None)

    client.get("/movies")
    client.get("/movies?query=None")

    # Without the `or ""` both calls build "movies:None:1", and whichever
    # ran first decides what the other one shows.
    assert seen == ["movies::1", "movies:None:1"]


# --- 6. The log says the cache is off, on every call ------------------------
def test_every_failed_read_is_logged(caplog, monkeypatch):
    """One line per call: a missed line would make an outage look like a hit."""

    def broken(*args, **kwargs):
        raise redis.ConnectionError("Redis is unreachable")

    monkeypatch.setattr(cache.red, "get", broken)

    with caplog.at_level(logging.WARNING, logger="app.cache"):
        cache.cache_get("k")
        cache.cache_get("k")

    assert len(caplog.records) == 2
    assert "reading k as a miss" in caplog.records[0].message


# ------------
def test_a_failed_write_is_logged_and_swallowed(caplog, monkeypatch):
    """A cache that cannot store must still answer: the page owes nothing to Redis."""

    def broken(*args, **kwargs):
        raise redis.ConnectionError("Redis is unreachable")

    monkeypatch.setattr(cache.red, "set", broken)

    with caplog.at_level(logging.WARNING, logger="app.cache"):
        assert cache.cache_set("k", {"a": 1}, 10) is None

    assert "k stays uncached" in caplog.records[0].message


# --- 7. What a cache hit is actually worth ----------------------------------
# One finished film, the shape the cache now holds.
CACHED_FILMS = [
    {
        "tmdb_id": 329865,
        "title": "Arrival",
        "release_date": "2016-11-11",
        "poster_path": "/arrival.jpg",
        "imdb_id": "tt2543164",
        "imdb_rating": 7.9,
    }
]


def test_a_cache_hit_costs_no_upstream_call_at_all(client, monkeypatch):
    """The whole point: caching the TMDB page saved 1 request out of 41."""
    calls = []

    async def fetch(url, headers=None):
        calls.append(url)
        return TMDB_PAGE

    async def details(tmdb_id, headers):
        calls.append(tmdb_id)
        return (None, None)

    monkeypatch.setattr(utils, "fetch_data", fetch)
    monkeypatch.setattr(utils, "get_movie_details", details)
    monkeypatch.setattr(movie_list, "cache_get", lambda key: CACHED_FILMS)
    monkeypatch.setattr(movie_list, "cache_set", lambda key, value, ttl: None)

    response = client.get("/movies")

    assert response.status_code == 200
    assert response.json() == CACHED_FILMS
    assert calls == []


# ------------
def test_what_goes_into_the_cache_is_enriched(client, offline_tmdb, monkeypatch):
    """Storing the raw page would put the expensive half outside the cache."""
    stored = {}
    monkeypatch.setattr(
        movie_list, "cache_set", lambda key, value, ttl: stored.update({key: value})
    )

    client.get("/movies")

    assert list(stored) == ["movies::1"]
    # imdb_rating comes from OMDB, one call per film: its presence in the stored
    # value is the proof that a later hit will not have to ask again.
    assert stored["movies::1"][0]["imdb_rating"] == 7.9


# ------------
def test_a_tmdb_failure_is_never_cached(client, monkeypatch):
    """One bad minute upstream must not blank the home page for ten hours."""
    stored = {}

    async def boom(url, headers=None):
        raise aiohttp.ClientError("TMDB is unreachable")

    monkeypatch.setattr(utils, "fetch_data", boom)
    monkeypatch.setattr(movie_list, "cache_get", lambda key: None)
    monkeypatch.setattr(
        movie_list, "cache_set", lambda key, value, ttl: stored.update({key: value})
    )

    assert client.get("/movies").json() == []
    assert stored == {}
