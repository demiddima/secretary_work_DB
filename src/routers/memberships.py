# src/routers/memberships.py
# commit: вариант A — list_by_chat возвращает list[int] (без dict), остальные ответы оставлены ok-обёрткой

import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src import crud
from src.dependencies import get_session

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/memberships", tags=["memberships"])


@router.post("/", response_model=dict)
async def upsert_user_to_chat(
    user_id: int,
    chat_id: int,
    session: AsyncSession = Depends(get_session),
):
    try:
        logger.info(f"[{user_id}] - [POST /memberships/] add user_id={user_id} to chat_id={chat_id}")
        await crud.upsert_user_to_chat(session, user_id=user_id, chat_id=chat_id)
        return {"ok": True}
    except ValueError as e:
        logger.error(f"[{user_id}] - [POST /memberships/] FK/validation error: {e}")
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.error(f"[{user_id}] - [POST /memberships/] Ошибка: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Ошибка при добавлении пользователя в чат")


@router.delete("/", response_model=dict)
async def remove_user_from_chat(
    user_id: int,
    chat_id: int,
    session: AsyncSession = Depends(get_session),
):
    try:
        await crud.remove_user_from_chat(session, user_id=user_id, chat_id=chat_id)
        logger.info(f"[{user_id}] - [DELETE /memberships/] removed from chat_id={chat_id}")
        return {"ok": True}
    except Exception as e:
        logger.error(f"[{user_id}] - [DELETE /memberships/] Ошибка: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Ошибка при удалении пользователя из чата")


@router.get("/", response_model=bool)
async def is_user_in_chat(
    user_id: int,
    chat_id: int,
    session: AsyncSession = Depends(get_session),
):
    try:
        exists = await crud.is_user_in_chat(session, user_id=user_id, chat_id=chat_id)
        logger.info(f"[{user_id}] - [GET /memberships/] chat_id={chat_id}, exists={exists}")
        return exists
    except Exception as e:
        logger.error(f"[{user_id}] - [GET /memberships/] Ошибка: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Ошибка при проверке подписки пользователя")


@router.get("/by-chat", response_model=list[int])
async def list_by_chat(
    chat_id: int = Query(..., description="ID чата"),
    limit: int | None = Query(None, ge=1, description="необязательный лимит"),
    offset: int | None = Query(None, ge=0, description="смещение"),
    session: AsyncSession = Depends(get_session),
):
    try:
        rows = await crud.list_memberships_by_chat(session, chat_id=chat_id, limit=limit, offset=offset)
        logger.info(f"[GET /memberships/by-chat] chat_id={chat_id}, limit={limit}, offset={offset}, rows={len(rows)}")
        return rows
    except Exception as e:
        logger.error(f"[GET /memberships/by-chat] Ошибка: chat_id={chat_id}, ошибка={e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Ошибка при получении списка мемберств")
