from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import schemas, auth, models
from app.database import get_db

router = APIRouter(prefix="/watched", tags=["All watched movies list"])

@router.post("/", status_code=201, response_model=schemas.WatchedMovie)
def add_watched_movie(movie:schemas.WatchedMovie, db: Session = Depends(get_db),
                      current_user: models.User = Depends(auth.get_current_user)):
    user = db.query(models.User).filter(models.User.user_id == current_user.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    add_movie_request = models.WatchedMovies(**movie.model_dump())
    add_movie_request.user_id = current_user.user_id
    db.add(add_movie_request)
    db.commit()
    db.refresh(add_movie_request)
    return add_movie_request

@router.get("/", status_code=200, response_model=List[schemas.WatchedMovie])
def watched_movies(db: Session = Depends(get_db),
                   current_user: models.User = Depends(auth.get_current_user)):
    movies = db.query(models.WatchedMovies).filter(models.WatchedMovies.user_id == current_user.user_id).all()
    return movies