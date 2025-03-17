from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import exists

from app import utils, auth
from sqlalchemy.orm import Session
from app import schemas, auth, utils
from app import models
from app.database import get_db

router = APIRouter(prefix="/users", tags=["users"])

@router.post("/", status_code=201, response_model=schemas.UserResponse)
def create_user(user:schemas.CreateUser, db: Session = Depends(get_db)):
    """
    Function with post request to create a new user and add it to Watchlist app database
    """
    if db.query(exists().where(models.User.email == user.email)).scalar():
        raise HTTPException(status_code=409, detail="User with this email already exists")
    valid, message = utils.is_strong_password(user.password)
    if not valid:
        raise HTTPException(status_code=400, detail=message)
    new_user = models.User(**user.model_dump())
    new_user.password = utils.hash_password(new_user.password)
    try:
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        return new_user
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="Internal server error")


@router.patch("/", status_code=200, response_model=schemas.UserResponse)
def update_user(user:schemas.CreateUser, db: Session = Depends(get_db),
                current_user: models.User = Depends(auth.get_current_user)):
    """
    Function with patch request to update a user in Watchlist app database
    """
    user_to_update = db.query(models.User).filter(models.User.user_id == current_user.user_id).first()
    data = user.model_dump(exclude_unset=True)
    if "email" in data and data["email"] != current_user.email:
        existing_user = db.query(models.User).filter(models.User.email == data["email"]).first()
        if existing_user:
            raise HTTPException(status_code=409, detail="User with this email already exists")


    if "password" in data:
        valid, message = utils.is_strong_password(user.password)
        if not valid:
            raise HTTPException(status_code=400, detail=message)

    for key, value in data.items():
        if key == "password":
            value = utils.hash_password(value)
        setattr(user_to_update, key, value)

    db.commit()
    db.refresh(user_to_update)
    return user_to_update