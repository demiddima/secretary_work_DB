# src/routers/chats.py
# commit: вариант A — выровнено под CRUD (get_all_chat_ids), response_model сохранён, ok-обёртки для delete

import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src import crud
from src.dependencies import get_session
from src.schemas import ChatModel
from src.time_msk import now_msk_naive

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/chats", tags=["chats"])


@router.post("/", response_model=ChatModel)
async def upsert_chat(
    chat: ChatModel,
    session: AsyncSession = Depends(get_session),
):
    try:
        added_at = chat.added_at or now_msk_naive()
        logger.info(
            f"[{chat.id}] - [POST /chats/] upsert chat: "
            f"title={chat.title!r}, type={chat.type}, added_at(msk)={added_at}"
        )
        return await crud.upsert_chat(
            session,
            chat_id=chat.id,
            title=chat.title,
            type_=chat.type,
            added_at=added_at,
        )
    except Exception as e:
        logger.error(f"[{chat.id}] - [POST /chats/] Ошибка: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Ошибка при сохранении чата")


@router.get("/", response_model=List[int])
async def get_all_chats(session: AsyncSession = Depends(get_session)):
    try:
        result = await crud.get_all_chat_ids(session)
        logger.info(f"[GET /chats/] total={len(result)}")
        return result
    except Exception as e:
        logger.error(f"[GET /chats/] Ошибка: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Ошибка при получении чатов")


@router.delete("/{chat_id}", response_model=dict)
async def delete_chat(chat_id: int, session: AsyncSession = Depends(get_session)):
    try:
        await crud.delete_chat(session, chat_id=chat_id)
        logger.info(f"[{chat_id}] - [DELETE /chats/] deleted")
        return {"ok": True}
    except Exception as e:
        logger.error(f"[{chat_id}] - [DELETE /chats/] Ошибка: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Ошибка при удалении чата")
