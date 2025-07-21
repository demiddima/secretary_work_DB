# src/routers/invite_links.py
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
import logging
from typing import List

from src.schemas import InviteLinkModel, InviteLinkIn
from src.database import get_session
from src import crud
from src.utils import invite_link_to_dict  # Импортируем функцию преобразования

# Настроим логгер
logger = logging.getLogger()

router = APIRouter(
    prefix="/invite_links",
    tags=["invite_links"]
)

# Сохраняем ссылку приглашения
@router.post("/", response_model=InviteLinkModel)
async def save_invite_link(
    link: InviteLinkIn,
    session: AsyncSession = Depends(get_session)
):
    logger.info(f"[{link.user_id}] - [POST /invite_links/] Входящий запрос для сохранения ссылки приглашения: {link.dict()}")

    try:
        # Сохраняем ссылку приглашения в базе данных
        db_link = await crud.save_invite_link(
            session,
            user_id=link.user_id,
            chat_id=link.chat_id,
            invite_link=link.invite_link,
            created_at=link.created_at,
            expires_at=link.expires_at
        )

        # Логируем исходящий ответ
        logger.info(f"[{link.user_id}] - [POST /invite_links/] Исходящий ответ: {invite_link_to_dict(db_link)}")
        return db_link
    except Exception as e:
        # Логируем ошибку при сохранении ссылки
        logger.error(f"[{link.user_id}] - [POST /invite_links/] Ошибка при сохранении ссылки приглашения: {str(e)}")
        raise

# Получаем все ссылки приглашений для пользователя
@router.get("/all/{user_id}", response_model=List[InviteLinkModel])
async def get_all_invite_links(
    user_id: int,
    session: AsyncSession = Depends(get_session)
):
    logger.info(f"[{user_id}] - [GET /invite_links/all/{user_id}] Входящий запрос для получения всех ссылок для пользователя с user_id={user_id}")

    try:
        result = await crud.get_invite_links(session, user_id=user_id)

        # Логируем исходящий ответ
        logger.info(f"[{user_id}] - [GET /invite_links/all/{user_id}] Исходящий ответ: {result}")
        return result
    except Exception as e:
        logger.error(f"[{user_id}] - [GET /invite_links/all/{user_id}] Ошибка при получении всех ссылок: {str(e)}")
        raise

# Получаем действующие ссылки для пользователя
@router.get("/{user_id}", response_model=List[InviteLinkModel])
async def get_valid_invite_links(
    user_id: int,
    session: AsyncSession = Depends(get_session)
):
    logger.info(f"[{user_id}] - [GET /invite_links/{user_id}] Входящий запрос для получения действующих ссылок для пользователя с user_id={user_id}")

    try:
        result = await crud.get_valid_invite_links(session, user_id=user_id)

        # Логируем исходящий ответ
        logger.info(f"[{user_id}] - [GET /invite_links/{user_id}] Исходящий ответ: {result}")
        return result
    except Exception as e:
        logger.error(f"[{user_id}] - [GET /invite_links/{user_id}] Ошибка при получении действующих ссылок: {str(e)}")
        raise

# Удаляем ссылки приглашений для пользователя
@router.delete("/{user_id}", response_model=None)
async def delete_invite_links(
    user_id: int,
    session: AsyncSession = Depends(get_session)
):
    logger.info(f"[{user_id}] - [DELETE /invite_links/{user_id}] Входящий запрос для удаления ссылок для пользователя с user_id={user_id}")

    try:
        await crud.delete_invite_links(session, user_id=user_id)

        # Логируем исходящий ответ
        logger.info(f"[{user_id}] - [DELETE /invite_links/{user_id}] Исходящий ответ: {{'ok': True}}")
        return {"ok": True}
    except Exception as e:
        logger.error(f"[{user_id}] - [DELETE /invite_links/{user_id}] Ошибка при удалении ссылок: {str(e)}")
        raise
