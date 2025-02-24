from fastapi import FastAPI

from app.routers import movie_list, watched_list, user, login

app = FastAPI()
app.include_router(user.router)
app.include_router(login.router)
app.include_router(movie_list.router)
app.include_router(watched_list.router)


@app.get("/")
def home():
    """
    WatchList is a personal movie tracking application that helps users keep track of films they have watched
    and those they plan to see. It allows users to rate movies, add personal notes, categorize films,
    and explore recommendations based on their preferences.
    """
    return {"Message": "Welcome to WatchList home page"}