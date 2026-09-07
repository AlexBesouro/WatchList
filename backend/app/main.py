import uvicorn
from fastapi import FastAPI
from app.routers import movie_list, user, login, favorites
from fastapi.middleware.cors import CORSMiddleware
import logging

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

my_app = FastAPI()
my_app.include_router(user.router)
my_app.include_router(login.router)
my_app.include_router(movie_list.router)
my_app.include_router(favorites.router)

origins = [
    "http://localhost:5173",
]

my_app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@my_app.get("/")
def home():
    """
    WatchList is a personal movie tracking my_application that helps users keep track of films they have watched
    and those they plan to see. It allows users to rate movies, add personal notes, categorize films,
    and explore recommendations based on their preferences.
    """
    return {"Message": "Welcome to WatchList home page"}


if __name__ == "__main__":
    uvicorn.run(my_app, host="0.0.0.0", port=8000)
