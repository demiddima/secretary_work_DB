# src/routers/memberships.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from src.database import get_session
from src import crud

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/memberships", tags=["memberships"])


@router.post("/", response_model=None)
async def upsert_user_to_chat(
    user_id: int,
    chat_id: int,
    session: AsyncSession = Depends(get_session)
):
    try:
        # Логируем только важный вход: добавление пользователя в чат
        logger.info(
            f"[{user_id}] - [POST /memberships/] Запрос на добавление user_id={user_id} в чат chat_id={chat_id}"
        )
        # CRUD-функция уже проверяет существование и идемпотентно добавляет
        await crud.upsert_user_to_chat(session, user_id=user_id, chat_id=chat_id)
        return {"ok": True}
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
