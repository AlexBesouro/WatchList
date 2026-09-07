from datetime import UTC, datetime, timedelta
from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from app import models
from app.config import settings
from app.database import DbSession

# The dependency that reads "Authorization: Bearer <token>". auto_error=True, so
# a call with no header is refused before the handler body ever runs.
oauth2_schema = OAuth2PasswordBearer(tokenUrl="login")

# One wording for every way a token can fail, so the answer never says which.
REFUSED = "Could not validate credentials"


def create_access_token(data: dict) -> str:
    """Sign a token carrying `data` plus the moment it stops being valid."""
    expires_at = datetime.now(UTC) + timedelta(minutes=settings.EXPIRE_TIME)
    return jwt.encode(data | {"exp": expires_at}, settings.SECRET_KEY, settings.ALGORITHM)


def verify_token(token: str) -> dict | None:
    """The payload, or None when the token is forged, altered or expired."""
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except jwt.PyJWTError:
        return None


def get_current_user(
    token: Annotated[str, Depends(oauth2_schema)], db: DbSession
) -> models.User:
    """The user the token names — the single gate in front of the private routes."""
    payload = verify_token(token)
    if not payload:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, REFUSED)

    user = (
        db.query(models.User).filter(models.User.email == payload["user_email"]).first()
    )
    if not user:
        # 401 and not 404: a valid token for a deleted account is a failed
        # authentication, and 404 would confirm which emails exist.
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, REFUSED)
    return user


CurrentUser = Annotated[models.User, Depends(get_current_user)]
# Every private handler takes `user: CurrentUser`, so the gate is one word long
# and impossible to half-apply.
