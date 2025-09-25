# src/routers/memberships.py

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from src.dependencies import get_session
from src import crud

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/memberships", tags=["memberships"])


@router.post("/", response_model=dict)
async def upsert_user_to_chat(
    user_id: int,
    chat_id: int,
    session: AsyncSession = Depends(get_session)
):
    try:
        logger.info(
            f"[{user_id}] - [POST /memberships/] Запрос на добавление user_id={user_id} в чат chat_id={chat_id}"
        )
        await crud.upsert_user_to_chat(session, user_id=user_id, chat_id=chat_id)
        return {"ok": True}
    except ValueError as e:
        # Нарушение FK/валидация — это 422, а не 500
        logger.error(
            f"[{user_id}] - [POST /memberships/] FK/validation error: user_id={user_id}, chat_id={chat_id}, err={e}"
        )
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.error(
            f"[{user_id}] - [POST /memberships/] Ошибка при добавлении пользователя "
            f"user_id={user_id} в чат chat_id={chat_id}: {e}"
        )
        raise HTTPException(status_code=500, detail="Ошибка при добавлении пользователя в чат")


@router.delete("/", response_model=None)
async def remove_user_from_chat(
    user_id: int,
    chat_id: int,
    session: AsyncSession = Depends(get_session)
):
    try:
        await crud.remove_user_from_chat(session, user_id=user_id, chat_id=chat_id)
        # Логируем успешное удаление пользователя из чата
        logger.info(
            f"[{user_id}] - [DELETE /memberships/] Пользователь user_id={user_id} "
            f"успешно удалён из чата chat_id={chat_id}"
        )
        return {"ok": True}
    except Exception as e:
        logger.error(
            f"[{user_id}] - [DELETE /memberships/] Ошибка при удалении пользователя "
            f"user_id={user_id} из чата chat_id={chat_id}: {e}"
        )
        raise HTTPException(status_code=500, detail="Ошибка при удалении пользователя из чата")


@router.get("/", response_model=bool)
async def is_user_in_chat(
    user_id: int,
    chat_id: int,
    session: AsyncSession = Depends(get_session)
):
    try:
        exists = await crud.is_user_in_chat(session, user_id=user_id, chat_id=chat_id)
        # Логируем результат проверки подписки пользователя на чат
        logger.info(
            f"[{user_id}] - [GET /memberships/] Проверка подписки: user_id={user_id}, "
            f"chat_id={chat_id}, подписан={exists}"
        )
        return exists
    except Exception as e:
        logger.error(
            f"[{user_id}] - [GET /memberships/] Ошибка при проверке подписки "
            f"user_id={user_id} в чат chat_id={chat_id}: {e}"
        )
        raise HTTPException(status_code=500, detail="Ошибка при проверке подписки пользователя")
    
@router.get("/by-chat", response_model=list[dict])
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
        logger.error(f"[GET /memberships/by-chat] Ошибка: chat_id={chat_id}, ошибка={e}")
        raise HTTPException(status_code=500, detail="Ошибка при получении списка мемберств")
