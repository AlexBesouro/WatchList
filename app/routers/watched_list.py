from fastapi import APIRouter

router = APIRouter(prefix="/watched", tags=["All watched movies list"])

@router.post("/")
def add_watched_movie():
    pass