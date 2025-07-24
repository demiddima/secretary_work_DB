# src/routers/chats.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from datetime import datetime
import logging

from src.schemas import ChatModel
from src.database import get_session
from src import crud

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/chats", tags=["chats"])


@router.post("/", response_model=ChatModel)
async def upsert_chat(
    chat: ChatModel,
    session: AsyncSession = Depends(get_session)
):
    try:
        # Логируем подробности входных параметров
        logger.info(
            f"[{chat.id}] - [POST /chats/] Получены параметры для создания/обновления чата "
            f"(id={chat.id}, title={chat.title!r}, type={chat.type}, added_at={chat.added_at or datetime.utcnow()})"
        )
        return await crud.upsert_chat(
            session,
            chat_id=chat.id,
            title=chat.title,
            type_=chat.type,
            added_at=chat.added_at or datetime.utcnow()
        )
    except Exception as e:
        logger.error(f"[{chat.id}] - [POST /chats/] Ошибка при сохранении чата: {e}")
        raise HTTPException(status_code=500, detail="Ошибка при сохранении чата")


@router.get("/", response_model=List[int])
async def get_all_chats(session: AsyncSession = Depends(get_session)):
    try:
        result = await crud.get_all_chats(session)
        # Логируем подробности выходных данных
        logger.info(
            f"[GET /chats/] Возвращён список идентификаторов чатов "
            f"(total={len(result)}): {result}"
        )
        return result
    except Exception as e:
        logger.error(f"[GET /chats/] Ошибка при получении чатов: {e}")
        raise HTTPException(status_code=500, detail="Ошибка при получении чатов")


@router.delete("/{chat_id}", response_model=None)
async def delete_chat(chat_id: int, session: AsyncSession = Depends(get_session)):
    try:
        await crud.delete_chat(session, chat_id)
        # Логируем факт успешного удаления
        logger.info(
            f"[{chat_id}] - [DELETE /chats/] Чат с указанным id успешно удалён"
        )
        return {"ok": True}
    except Exception as e:
        logger.error(f"[{chat_id}] - [DELETE /chats/] Ошибка при удалении чата: {e}")
        raise HTTPException(status_code=500, detail="Ошибка при удалении чата")
