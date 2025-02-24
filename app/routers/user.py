from fastapi import APIRouter, Depends, HTTPException
# from app import utils, auth
from sqlalchemy.orm import Session
from app import schemas, auth, utils
from app import models
from app.database import get_db

router = APIRouter(prefix="/users", tags=["users"])

@router.post("/", status_code=201, response_model=schemas.UserResponse)
def create_user(user:schemas.CreateUser, db: Session = Depends(get_db)):
    new_user = models.User(**user.model_dump())
    user_query = db.query(models.User).filter(models.User.email == new_user.email).first()
    if user_query:
        raise HTTPException(status_code=409, detail="User with this email already exist")
    if len(new_user.password) < 3:
        raise HTTPException(status_code=400, detail="Password must be at least 3 characters long")
    new_user.password = utils.hash_password(new_user.password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@router.patch("/", status_code=200, response_model=schemas.UserResponse)
def update_user(user:schemas.CreateUser, db: Session = Depends(get_db),
                current_user: models.User = Depends(auth.get_current_user)):
    user_to_update = db.query(models.User).filter(models.User.user_id == current_user.user_id).first()
    data = user.model_dump(exclude_unset=True)
    user_query = db.query(models.User).filter(models.User.email == data["email"]).first()
    if user_query:
        raise HTTPException(status_code=409, detail="User with this email already exist")
    for key, value in data.items():
        setattr(user_to_update, key, value)
    if len(user_to_update.password) < 3:
        raise HTTPException(status_code=400, detail="Password must be at least 3 characters long")
    user_to_update.password = utils.hash_password(user_to_update.password)
    db.commit()
    db.refresh(user_to_update)
    return user_to_update