import redis
from fastapi import APIRouter
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app import cache, schemas
from app.database import DbSession

# No prefix: the path is exactly /health, so a probe never eats the 307 that a
# router registered on "/" would answer with.
router = APIRouter(tags=["Health"])


@router.get("/health")
def health(db: DbSession) -> schemas.Health:
    """What the service can reach right now, component by component."""
    database = _database_state(db)
    cache_state = _cache_state()
    # "degraded" and not an error status: browsing works with both of these
    # down, so the word says what is missing without claiming the API is unusable.
    both_up = database == "up" and cache_state == "up"

    return schemas.Health(
        status="ok" if both_up else "degraded",
        database=database,
        cache=cache_state,
    )
    # Always 200: a 503 would mean "do not use this service", and the public film
    # list is proof that is false — it answers with neither of them running.


def _database_state(db: Session) -> str:
    """Ask Postgres the cheapest question there is, through the app's own session."""
    try:
        db.execute(text("SELECT 1"))
    except SQLAlchemyError:
        return "down"
    return "up"
    # The session the routers use, not a fresh engine.connect(): a check that
    # takes a different path can report "up" while every handler is failing.


def _cache_state() -> str:
    """PING is the one Redis command that costs nothing and proves the link."""
    try:
        cache.red.ping()
    except redis.RedisError:
        return "down"
    return "up"
