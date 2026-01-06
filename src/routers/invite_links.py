# src/routers/invite_links.py
# commit: вариант A — pydantic v2 model_dump в логах, response_model оставлен на InviteLinkModel

import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src import crud
from src.dependencies import get_session
from src.schemas import InviteLinkIn, InviteLinkModel

router = APIRouter(prefix="/invite_links", tags=["invite_links"])
logger = logging.getLogger(__name__)


@router.post("/", response_model=InviteLinkModel)
async def save_invite_link(
    link: InviteLinkIn,
    session: AsyncSession = Depends(get_session),
):
    try:
        logger.info(f"[{link.user_id}] - [POST /invite_links/] save: {link.model_dump()}")
        return await crud.save_invite_link(
            session,
            user_id=link.user_id,
            chat_id=link.chat_id,
            invite_link=link.invite_link,
            created_at=link.created_at,
            expires_at=link.expires_at,
        )
    except Exception as e:
        logger.error(f"[{link.user_id}] - [POST /invite_links/] Ошибка: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Ошибка при сохранении ссылки приглашения")


@router.get("/all/{user_id}", response_model=List[InviteLinkModel])
async def get_all_invite_links(
    user_id: int,
    session: AsyncSession = Depends(get_session),
):
    try:
        result = await crud.get_invite_links(session, user_id=user_id)
        logger.info(f"[{user_id}] - [GET /invite_links/all/{user_id}] total={len(result)}")
        return result
    except Exception as e:
        logger.error(f"[{user_id}] - [GET /invite_links/all/{user_id}] Ошибка: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Ошибка при получении ссылок приглашений")


@router.get("/{user_id}", response_model=List[InviteLinkModel])
async def get_valid_invite_links(
    user_id: int,
    session: AsyncSession = Depends(get_session),
):
    try:
        result = await crud.get_valid_invite_links(session, user_id=user_id)
        logger.info(f"[{user_id}] - [GET /invite_links/{user_id}] valid_total={len(result)}")
        return result
    except Exception as e:
        logger.error(f"[{user_id}] - [GET /invite_links/{user_id}] Ошибка: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Ошибка при получении действующих ссылок")


@router.delete("/{user_id}", response_model=dict)
async def delete_invite_links(
    user_id: int,
    session: AsyncSession = Depends(get_session),
):
    try:
        await crud.delete_invite_links(session, user_id=user_id)
        logger.info(f"[{user_id}] - [DELETE /invite_links/{user_id}] deleted")
        return {"ok": True}
    except Exception as e:
        logger.error(f"[{user_id}] - [DELETE /invite_links/{user_id}] Ошибка: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Ошибка при удалении ссылок приглашений")
