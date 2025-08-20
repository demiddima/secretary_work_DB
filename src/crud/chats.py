
from .base import retry_db, AsyncSession, select, delete, datetime
from src.models import Chat

@retry_db
async def upsert_chat(
    session: AsyncSession,
    chat_id: int,
    title: str,
    type_: str,
    added_at: datetime,
):
    async with session.begin():
        stmt = select(Chat).where(Chat.id == chat_id)
        res = await session.execute(stmt)
        chat = res.scalar_one_or_none()

        if chat:
            chat.title = title
            chat.type = type_
            chat.added_at = added_at
        else:
            chat = Chat(
                id=chat_id,
                title=title,
                type=type_,
                added_at=added_at
            )
            session.add(chat)

    return chat

@retry_db
async def delete_chat(session: AsyncSession, chat_id: int):
    async with session.begin():
        await session.execute(delete(Chat).where(Chat.id == chat_id))

@retry_db
async def get_all_chats(session: AsyncSession):
    stmt = select(Chat.id)
    res = await session.execute(stmt)
    return [row[0] for row in res.all()]
