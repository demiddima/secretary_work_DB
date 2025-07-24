# src/routers/invite_links.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
import logging

from src.schemas import InviteLinkModel, InviteLinkIn
from src.database import get_session
from src import crud

router = APIRouter(
    prefix="/invite_links",
    tags=["invite_links"]
)
logger = logging.getLogger(__name__)


@router.post("/", response_model=InviteLinkModel)
async def save_invite_link(
    link: InviteLinkIn,
    session: AsyncSession = Depends(get_session)
):
    try:
        # Логируем только важный вход: данные ссылки
        logger.info(f"[{link.user_id}] - [POST /invite_links/] Сохранение ссылки: {link.dict()}")
        return await crud.save_invite_link(
            session,
            user_id=link.user_id,
            chat_id=link.chat_id,
            invite_link=link.invite_link,
            created_at=link.created_at,
            expires_at=link.expires_at
        )
    except Exception as e:
        logger.error(f"[{link.user_id}] - [POST /invite_links/] Ошибка при сохранении ссылки: {e}")
        raise HTTPException(status_code=500, detail="Ошибка при сохранении ссылки приглашения")


@router.get("/all/{user_id}", response_model=List[InviteLinkModel])
async def get_all_invite_links(
    user_id: int,
    session: AsyncSession = Depends(get_session)
):
    try:
        result = await crud.get_invite_links(session, user_id=user_id)
        # Логируем только важный выход: полный список ссылок
        logger.info(f"[{user_id}] - [GET /invite_links/all/{user_id}] Возвращены ссылки: {result}")
        return result
    except Exception as e:
        logger.error(f"[{user_id}] - [GET /invite_links/all/{user_id}] Ошибка при получении ссылок: {e}")
        raise HTTPException(status_code=500, detail="Ошибка при получении ссылок приглашений")


@router.get("/{user_id}", response_model=List[InviteLinkModel])
async def get_valid_invite_links(
    user_id: int,
    session: AsyncSession = Depends(get_session)
):
    try:
        result = await crud.get_valid_invite_links(session, user_id=user_id)
        # Логируем только важный выход: список действующих ссылок
        logger.info(f"[{user_id}] - [GET /invite_links/{user_id}] Возвращены действующие ссылки: {result}")
        return result
    except Exception as e:
        logger.error(f"[{user_id}] - [GET /invite_links/{user_id}] Ошибка при получении действующих ссылок: {e}")
        raise HTTPException(status_code=500, detail="Ошибка при получении действующих ссылок")


@router.delete("/{user_id}", response_model=None)
async def delete_invite_links(
    user_id: int,
    session: AsyncSession = Depends(get_session)
):
    try:
        await crud.delete_invite_links(session, user_id=user_id)
        # Логируем только важный выход: факт удаления ссылок
        logger.info(f"[{user_id}] - [DELETE /invite_links/{user_id}] Ссылки удалены")
        return {"ok": True}
    except Exception as e:
        logger.error(f"[{user_id}] - [DELETE /invite_links/{user_id}] Ошибка при удалении ссылок: {e}")
        raise HTTPException(status_code=500, detail="Ошибка при удалении ссылок приглашений")
