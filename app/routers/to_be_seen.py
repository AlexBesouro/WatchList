from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import schemas, auth, models
from app.database import get_db

router = APIRouter(prefix="/to-watch", tags=["A list of movies user would like to watch"])

@router.post("/", status_code=201, response_model=schemas.UnWatched)
def add_watched_movie(movie:schemas.UnWatched, db: Session = Depends(get_db),
                      current_user: models.User = Depends(auth.get_current_user)):
    user = db.query(models.User).filter(models.User.user_id == current_user.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    add_movie_request = models.UnWatched(**movie.model_dump())
    add_movie_request.user_id = current_user.user_id
    db.add(add_movie_request)
    db.commit()
    db.refresh(add_movie_request)
    return add_movie_request

@router.get("/", status_code=200, response_model=List[schemas.UnWatched])
def watched_movies(db: Session = Depends(get_db),
                   current_user: models.User = Depends(auth.get_current_user)):
    movies = db.query(models.UnWatched).filter(models.UnWatched.user_id == current_user.user_id).all()
    return movies