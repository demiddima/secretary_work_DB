from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from src.schemas import InviteLinkModel, InviteLinkIn
from src.database import get_session
from src import crud

router = APIRouter(
    prefix="/invite_links",
    tags=["invite_links"]
)

@router.post("/", response_model=InviteLinkModel)
async def save_invite_link(
    link: InviteLinkIn,
    session: AsyncSession = Depends(get_session)
):
    db_link = await crud.save_invite_link(
        session,
        user_id=link.user_id,
        chat_id=link.chat_id,
        invite_link=link.invite_link,
        created_at=link.created_at,
        expires_at=link.expires_at
    )
    return db_link

@router.get("/{user_id}", response_model=List[InviteLinkModel])
async def get_valid_invite_links(
    user_id: int,
    session: AsyncSession = Depends(get_session)
):
    return await crud.get_valid_invite_links(session, user_id=user_id)

@router.delete("/{user_id}", response_model=None)
async def delete_invite_links(
    user_id: int,
    session: AsyncSession = Depends(get_session)
):
    await crud.delete_invite_links(session, user_id=user_id)
    return {"ok": True}
