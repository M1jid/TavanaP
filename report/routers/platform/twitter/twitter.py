from fastapi import APIRouter, Depends, HTTPException

from auth.auth import get_current_active_user

router = APIRouter(
    prefix="/twitter",
    tags=["Twitter"],
    dependencies=[Depends(get_current_active_user)],
    responses={404: {"description": "Not found"}},
)


@router.get("/platform")
async def get_context():
    return __name__
