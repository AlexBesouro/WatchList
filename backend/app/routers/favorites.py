from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app import schemas, auth, models
from app.database import get_db

router = APIRouter(prefix="/favorites", tags=["Favorites"])


@router.post("/", status_code=201, response_model=schemas.Favorite)
def add_favorite(
    movie: schemas.Favorite,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    user = (
        db.query(models.User)
        .filter(models.User.user_id == current_user.user_id)
        .first()
    )
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    add_movie_request = models.Favorite(**movie.model_dump())
    add_movie_request.user_id = current_user.user_id
    try:
        db.add(add_movie_request)
        db.commit()
        db.refresh(add_movie_request)
        return add_movie_request
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409, detail="Movie already in favorites."
        )


@router.get("/", status_code=200, response_model=List[schemas.Favorite])
def list_favorites(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    movies = (
        db.query(models.Favorite)
        .filter(models.Favorite.user_id == current_user.user_id)
        .all()
    )
    return movies
