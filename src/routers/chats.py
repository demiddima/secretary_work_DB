from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from src.schemas import ChatModel
from src.database import get_session
from src import crud


router = APIRouter(
    prefix="/chats",
    tags=["chats"]
)

@router.post("/", response_model=ChatModel)
async def upsert_chat(
    chat: ChatModel,
    session: AsyncSession = Depends(get_session)
):
    """Создать или обновить чат."""
    db_chat = await crud.upsert_chat(session, chat_id=chat.id, title=chat.title, type_=chat.type)
    return db_chat

@router.get("/", response_model=List[int])
async def get_all_chats(
    session: AsyncSession = Depends(get_session)
):
    """Получить список всех chat_id."""
    return await crud.get_all_chats(session)

@router.delete("/{chat_id}", response_model=None)
async def delete_chat(
    chat_id: int,
    session: AsyncSession = Depends(get_session)
):
    """Удалить чат по chat_id."""
    await crud.delete_chat(session, chat_id)
    return {"ok": True}
