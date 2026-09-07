from fastapi import APIRouter, HTTPException, status
from sqlalchemy.exc import IntegrityError

from app import models, schemas, utils
from app.auth import CurrentUser
from app.database import DbSession

router = APIRouter(prefix="/users", tags=["Users"])


@router.post("", status_code=status.HTTP_201_CREATED)
def create_user(user: schemas.CreateUser, db: DbSession) -> schemas.UserResponse:
    """Register an account, once the password clears the policy."""
    valid, message = utils.is_strong_password(user.password)
    if not valid:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, message)

    new_user = models.User(**user.model_dump())
    new_user.password = utils.hash_password(new_user.password)
    db.add(new_user)
    try:
        db.commit()
    except IntegrityError:
        # The unique index on email is the check. A SELECT first would still let
        # two simultaneous sign-ups through, and this cannot.
        db.rollback()
        raise HTTPException(
            status.HTTP_409_CONFLICT, "User with this email already exists"
        ) from None
    db.refresh(new_user)
    return new_user


@router.get("/me")
def read_me(user: CurrentUser) -> schemas.UserResponse:
    """Who the token belongs to. The front-end calls it to restore a session."""
    return user
    # No database session: get_current_user already loaded the row to prove the
    # token, so asking Postgres a second time would confirm what it just said.
