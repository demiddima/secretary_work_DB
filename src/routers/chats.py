# src/routers/chats.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from datetime import datetime
import logging

from src.schemas import ChatModel
from src.database import get_session
from src import crud
from src.utils import chat_to_dict  # Импортируем функцию для преобразования в словарь

# Настроим логгер (используем корневой логгер)
logger = logging.getLogger()

router = APIRouter(
    prefix="/chats",
    tags=["chats"]
)

# Обновляем или создаем чат
@router.post("/", response_model=ChatModel)
async def upsert_chat(
    chat: ChatModel,
    session: AsyncSession = Depends(get_session)
):
    logger.info(f"[{chat.id}] - [POST /chats/] - [upsert_chat] Входящий запрос: {chat.dict()}")

    try:
        # Выполняем операцию обновления или создания чата
        db_chat = await crud.upsert_chat(
            session,
            chat_id=chat.id,
            title=chat.title,
            type_=chat.type,
            added_at=chat.added_at or datetime.utcnow()
        )

        # Логируем исходящий ответ с преобразованием данных через chat_to_dict
        logger.info(f"[{chat.id}] - [POST /chats/] - [upsert_chat] Исходящий ответ: {chat_to_dict(db_chat)}")
        return db_chat
    except Exception as e:
        # Логируем ошибку при возникновении исключения
        logger.error(f"[{chat.id}] - [POST /chats/] - [upsert_chat] Ошибка при обновлении чата: {str(e)}")
        raise HTTPException(status_code=500, detail="Ошибка при обновлении чата")

# Получаем все чаты
@router.get("/", response_model=List[int])
async def get_all_chats(
    session: AsyncSession = Depends(get_session)
):
    logger.info(f"[GET /chats/] - [get_all_chats] Входящий запрос для получения всех чатов.")
    
    try:
        # Получаем все chat_id
        result = await crud.get_all_chats(session)
        
        logger.info(f"[GET /chats/] - [get_all_chats] Исходящий ответ с chat_id: {result}")
        return result
    except Exception as e:
        # Логируем ошибку при получении данных
        logger.error(f"[GET /chats/] - [get_all_chats] Ошибка при получении чатов: {str(e)}")
        raise HTTPException(status_code=500, detail="Ошибка при получении чатов")

# Удаляем чат
@router.delete("/{chat_id}", response_model=None)
async def delete_chat(
    chat_id: int,
    session: AsyncSession = Depends(get_session)
):
    logger.info(f"[{chat_id}] - [DELETE /chats/{chat_id}] - [delete_chat] Входящий запрос для удаления чата.")

    try:
        # Удаляем чат по chat_id
        await crud.delete_chat(session, chat_id)
        
        logger.info(f"[{chat_id}] - [DELETE /chats/{chat_id}] - [delete_chat] Исходящий ответ: {{'ok': True}}")
        return {"ok": True}
    except Exception as e:
        # Логируем ошибку при удалении чата
        logger.error(f"[{chat_id}] - [DELETE /chats/{chat_id}] - [delete_chat] Ошибка при удалении чата: {str(e)}")
        raise HTTPException(status_code=500, detail="Ошибка при удалении чата")
