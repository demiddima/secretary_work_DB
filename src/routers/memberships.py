# src/routers/memberships.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from src.database import get_session
from src import crud

# Настроим логгер
logger = logging.getLogger()

router = APIRouter(
    prefix="/memberships",
    tags=["memberships"]
)

# Добавляем пользователя в чат
@router.post("/", response_model=None)
async def upsert_user_to_chat(
    user_id: int,
    chat_id: int,
    session: AsyncSession = Depends(get_session)
):
    logger.info(f"[{user_id}] - [POST /memberships/] Входящий запрос для добавления пользователя с user_id={user_id} в чат с chat_id={chat_id}")

    try:
        # Выполняем операцию добавления пользователя в чат
        await crud.upsert_user_to_chat(session, user_id=user_id, chat_id=chat_id)

        logger.info(f"[{user_id}] - [POST /memberships/] Исходящий ответ: {{'ok': True}}")
        return {"ok": True}
    except Exception as e:
        # Логируем ошибку при добавлении пользователя
        logger.error(f"[{user_id}] - [POST /memberships/] Ошибка при добавлении пользователя в чат: {str(e)}")
        raise HTTPException(status_code=500, detail="Ошибка при добавлении пользователя в чат")

# Удаляем пользователя из чата
@router.delete("/", response_model=None)
async def remove_user_from_chat(
    user_id: int,
    chat_id: int,
    session: AsyncSession = Depends(get_session)
):
    logger.info(f"[{user_id}] - [DELETE /memberships/] Входящий запрос для удаления пользователя с user_id={user_id} из чата с chat_id={chat_id}")

    try:
        # Выполняем операцию удаления пользователя из чата
        await crud.remove_user_from_chat(session, user_id=user_id, chat_id=chat_id)

        logger.info(f"[{user_id}] - [DELETE /memberships/] Исходящий ответ: {{'ok': True}}")
        return {"ok": True}
    except Exception as e:
        # Логируем ошибку при удалении пользователя
        logger.error(f"[{user_id}] - [DELETE /memberships/] Ошибка при удалении пользователя из чата: {str(e)}")
        raise HTTPException(status_code=500, detail="Ошибка при удалении пользователя из чата")
