from fastapi import APIRouter, HTTPException, status

from app import auth, models, schemas, utils
from app.database import DbSession

router = APIRouter(prefix="/login", tags=["Authentication"])


@router.post("")
def login(credentials: schemas.UserCredentials, db: DbSession) -> schemas.TokenResponse:
    """Exchange an email and a password for a bearer token."""
    user = db.query(models.User).filter(models.User.email == credentials.email).first()
    # One message for both failures: telling them apart would say which emails
    # are registered, which is half of a password-guessing attack.
    if not user or not utils.verify_password(credentials.password, user.password):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid credentials")

    token = auth.create_access_token({"user_email": user.email})
    return {"access_token": token, "token_type": "bearer"}
