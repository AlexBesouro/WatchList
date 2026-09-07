from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings, read once from `.env` at import time."""

    model_config = SettingsConfigDict(env_file=".env")

    # External film data.
    TMDB_URL: str
    AUTHORIZATION: str
    OMDB_URL: str
    OMDB_API_KEY: str

    # PostgreSQL.
    DATABASE_HOSTNAME: str
    DATABASE_PORT: int
    DATABASE_PASSWORD: str
    DATABASE_NAME: str
    DATABASE_USERNAME: str

    # Redis is only a cache, so it keeps a default: a missing line degrades the
    # service to "always a miss", it never stops it from starting.
    REDIS_URL: str = "redis://localhost:6379"

    # JWT.
    SECRET_KEY: str
    ALGORITHM: str
    EXPIRE_TIME: int


settings = Settings()
# Built at import: a malformed .env kills the process at startup, never on the
# first request, where the caller would read it as a server bug.
