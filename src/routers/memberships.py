# src/routers/memberships.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from src.database import get_session
from src import crud

logger = logging.getLogger("api_logger")

router = APIRouter(
    prefix="/memberships",
    tags=["memberships"]
)

FILE_NAME = "MEMBERSHIPS"


@router.post("/", response_model=None)
async def upsert_user_to_chat(
    user_id: int,
    chat_id: int,
    session: AsyncSession = Depends(get_session)
):
    # входящий запрос
    logger.info(
        f"{FILE_NAME} - {user_id} - upsert_user_to_chat - POST /memberships - входящий запрос: "
        f"user_id={user_id}, chat_id={chat_id}"
    )
    try:
        await crud.upsert_user_to_chat(session, user_id=user_id, chat_id=chat_id)
        # исходящий ответ
        logger.info(
            f"{FILE_NAME} - {user_id} - upsert_user_to_chat - POST /memberships - исходящий ответ: ok=True"
        )
        return {"ok": True}
    except Exception as e:
        logger.error(
            f"{FILE_NAME} - {user_id} - upsert_user_to_chat - POST /memberships - ошибка: {e}"
        )
        raise HTTPException(status_code=500, detail="Ошибка при добавлении пользователя в чат")


@router.delete("/", response_model=None)
async def remove_user_from_chat(
    user_id: int,
    chat_id: int,
    session: AsyncSession = Depends(get_session)
):
    # входящий запрос
    logger.info(
        f"{FILE_NAME} - {user_id} - remove_user_from_chat - DELETE /memberships - входящий запрос: "
        f"user_id={user_id}, chat_id={chat_id}"
    )
    try:
        await crud.remove_user_from_chat(session, user_id=user_id, chat_id=chat_id)
        # исходящий ответ
        logger.info(
            f"{FILE_NAME} - {user_id} - remove_user_from_chat - DELETE /memberships - исходящий ответ: ok=True"
        )
        return {"ok": True}
    except Exception as e:
        logger.error(
            f"{FILE_NAME} - {user_id} - remove_user_from_chat - DELETE /memberships - ошибка: {e}"
        )
        raise HTTPException(status_code=500, detail="Ошибка при удаления пользователя из чата")


@router.get("/", response_model=bool)
async def is_user_in_chat(
    user_id: int,
    chat_id: int,
    session: AsyncSession = Depends(get_session)
):
    # входящий запрос
    logger.info(
        f"{FILE_NAME} - {user_id} - is_user_in_chat - GET /memberships - входящий запрос: "
        f"user_id={user_id}, chat_id={chat_id}"
    )
    try:
        exists = await crud.is_user_in_chat(session, user_id=user_id, chat_id=chat_id)
        # исходящий ответ
        logger.info(
            f"{FILE_NAME} - {user_id} - is_user_in_chat - GET /memberships - исходящий ответ: exists={exists}"
        )
        return exists
    except Exception as e:
        logger.error(
            f"{FILE_NAME} - {user_id} - is_user_in_chat - GET /memberships - ошибка: {e}"
        )
        raise HTTPException(status_code=500, detail="Ошибка при проверке подписки")
