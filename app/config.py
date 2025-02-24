from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    TMDB_URL:str
    AUTHORIZATION:str
    OMDB_URL:str
    OMDB_API_KEY:str
    DATABASE_HOSTNAME:str
    DATABASE_PORT:str
    DATABASE_PASSWORD:str
    DATABASE_NAME:str
    DATABASE_USERNAME:str
    SECRET_KEY:str
    ALGORITHM:str
    EXPIRE_TIME:int
    class Config:
        env_file = ".env"

settings = Settings()