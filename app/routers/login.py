from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app import models, utils, auth
from app import schemas
from app.database import get_db

router = APIRouter(prefix="/login", tags=["Authentication"])

@router.post("/", response_model=schemas.TokenResponse)#
def login(user_credentials: schemas.UserCredentials, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == user_credentials.email).first()
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if not utils.verify_password(user_credentials.password, user.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    access_token = auth.create_access_token(data={"user_email":user.email})

    return {"access_token": access_token, "token_type":"bearer"}