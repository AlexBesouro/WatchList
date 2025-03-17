import uvicorn
from fastapi import FastAPI

from app.routers import movie_list, watched_list, user, login, to_be_watched

my_app = FastAPI()
my_app.include_router(user.router)
my_app.include_router(login.router)
my_app.include_router(movie_list.router)
my_app.include_router(watched_list.router)
my_app.include_router(to_be_watched.router)


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