# src/crud/invite_links.py
# commit: унифицированы транзакции (session.begin), сохранён upsert через mysql_insert, убран ручной commit/rollback

from __future__ import annotations

from datetime import datetime

from .base import AsyncSession, SQLAlchemyError, delete, func, mysql_insert, retry_db, select
from src.models import InviteLink


@retry_db
async def save_invite_link(
    session: AsyncSession,
    *,
    user_id: int,
    chat_id: int,
    invite_link: str,
    created_at: datetime,
    expires_at: datetime,
) -> InviteLink:
    stmt = mysql_insert(InviteLink).values(
        user_id=user_id,
        chat_id=chat_id,
        invite_link=invite_link,
        created_at=created_at,
        expires_at=expires_at,
    ).on_duplicate_key_update(
        invite_link=mysql_insert(InviteLink).inserted.invite_link,
        created_at=mysql_insert(InviteLink).inserted.created_at,
        expires_at=mysql_insert(InviteLink).inserted.expires_at,
    )

    try:
        async with session.begin():
            await session.execute(stmt)
    except SQLAlchemyError:
        raise

    result = await session.execute(
        select(InviteLink).where(
            InviteLink.user_id == user_id,
            InviteLink.chat_id == chat_id,
        )
    )
    return result.scalar_one()


@retry_db
async def get_valid_invite_links(session: AsyncSession, *, user_id: int) -> list[InviteLink]:
    now = func.now()
    stmt = select(InviteLink).where(
        InviteLink.user_id == user_id,
        InviteLink.expires_at > now,
    )
    res = await session.execute(stmt)
    return list(res.scalars().all())


@retry_db
async def get_invite_links(session: AsyncSession, *, user_id: int) -> list[InviteLink]:
    stmt = select(InviteLink).where(InviteLink.user_id == user_id)
    res = await session.execute(stmt)
    return list(res.scalars().all())


@retry_db
async def delete_invite_links(session: AsyncSession, *, user_id: int) -> None:
    async with session.begin():
        await session.execute(delete(InviteLink).where(InviteLink.user_id == user_id))
