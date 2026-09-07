import pytest
import redis
from sqlalchemy.exc import OperationalError

from app import cache


@pytest.fixture
def reachable_redis(monkeypatch):
    """Stand in for a running Redis: the machine may not have one."""
    monkeypatch.setattr(cache.red, "ping", lambda: True)


def unreachable(*args, **kwargs):
    raise redis.ConnectionError("Redis is unreachable")


# --- 1. Everything the service needs is reachable ---------------------------
def test_health_reports_both_dependencies_up(client, reachable_redis):
    """The probe names each component, not just an overall verdict."""
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "up", "cache": "up"}


# ------------
def test_health_has_no_trailing_slash(client, reachable_redis):
    """A probe hitting /health must not be answered with a 307 to /health/."""
    assert client.get("/health", follow_redirects=False).status_code == 200


# --- 2. A dependency is missing ---------------------------------------------
def test_a_missing_redis_is_reported_not_hidden(client, monkeypatch):
    """Still 200: the film list answers with no Redis at all, so the API is usable."""
    monkeypatch.setattr(cache.red, "ping", unreachable)

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "degraded", "database": "up", "cache": "down"}


# ------------
def test_a_missing_database_is_reported(client, session, monkeypatch, reachable_redis):
    """The check runs through the session the routers use, so it fails with them."""

    def broken(*args, **kwargs):
        raise OperationalError("SELECT 1", {}, Exception("connection refused"))

    monkeypatch.setattr(session, "execute", broken)

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["database"] == "down"
    assert response.json()["status"] == "degraded"
