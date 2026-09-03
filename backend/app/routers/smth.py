from fastapi import APIRouter

router = APIRouter(prefix="/smth", tags=["All movies list"])


@router.get("/")
async def get_movies():
    return {"message": "Rabotaet"}
