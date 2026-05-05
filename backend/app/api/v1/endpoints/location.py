from fastapi import APIRouter

router = APIRouter()

@router.get("/geocode")
async def geocode():
    return {"message": "not implemented"}