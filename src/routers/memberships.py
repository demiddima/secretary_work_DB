from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_session
from src import crud

router = APIRouter(
    prefix="/memberships",
    tags=["memberships"]
)

@router.post("/", response_model=None)
async def upsert_user_to_chat(
    user_id: int,
    chat_id: int,
    session: AsyncSession = Depends(get_session)
):
    await crud.upsert_user_to_chat(session, user_id=user_id, chat_id=chat_id)
    return {"ok": True}

@router.delete("/", response_model=None)
async def remove_user_from_chat(
    user_id: int,
    chat_id: int,
    session: AsyncSession = Depends(get_session)
):
    await crud.remove_user_from_chat(session, user_id=user_id, chat_id=chat_id)
    return {"ok": True}
