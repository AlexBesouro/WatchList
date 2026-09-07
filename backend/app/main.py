import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import favorites, health, login, movie_list, user, watch_later

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)



my_app = FastAPI(
    title="WatchList",
    description="Browse films, keep a favorites list and a watch-later list.",
    version="1.0.0",
)

origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]


my_app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


my_app.include_router(health.router)
my_app.include_router(user.router)
my_app.include_router(login.router)
my_app.include_router(movie_list.router)
my_app.include_router(favorites.router)
my_app.include_router(watch_later.router)

# Vite serves the same site under both names and the browser treats them as two
# different origins, so both are listed or one of them fails every request.



@my_app.get("/")
def home() -> dict[str, str]:
    """The human-facing proof that the API is up."""
    return {"message": "Welcome to the WatchList API"}
