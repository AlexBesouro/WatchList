"""Redis as an optional cache: when it is unreachable, every call is a miss."""

import json
import logging

import redis

from app.config import settings

log = logging.getLogger(__name__)

# from_url() opens nothing: the client connects on the first command, so a Redis
# that is down never stops the app from importing or starting.
red = redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)


def cache_get(key: str) -> dict | list | None:
    """The value stored under `key`, or None on a miss or an unreachable Redis."""
    try:
        raw = red.get(key)
    except redis.RedisError:
        # Every failure, not only the first one of an outage: a cache that is
        # off has to stay visible, or its silence reads as "everything is fine".
        log.warning("Redis unreachable, reading %s as a miss", key)
        return None
    return json.loads(raw) if raw else None


def cache_set(key: str, value: dict | list, ttl: int) -> None:
    """Store `value` for `ttl` seconds. Failing here costs the cache, not the answer."""
    try:
        red.set(key, json.dumps(value), ex=ttl)
    except redis.RedisError:
        log.warning("Redis unreachable, %s stays uncached", key)
