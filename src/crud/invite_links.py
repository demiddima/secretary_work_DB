
from .base import retry_db, AsyncSession, select, delete, func, SQLAlchemyError, mysql_insert
from src.models import InviteLink

@retry_db
async def save_invite_link(
    session: AsyncSession, user_id: int, chat_id: int,
    invite_link: str, created_at, expires_at
):
    stmt = mysql_insert(InviteLink).values(
        user_id=user_id,
        chat_id=chat_id,
        invite_link=invite_link,
        created_at=created_at,
        expires_at=expires_at
    )
    upsert_stmt = stmt.on_duplicate_key_update(
        invite_link=stmt.inserted.invite_link,
        created_at=stmt.inserted.created_at,
        expires_at=stmt.inserted.expires_at
    )
    try:
        await session.execute(upsert_stmt)
        await session.commit()
    except SQLAlchemyError:
        await session.rollback()
        raise

    result = await session.execute(
        select(InviteLink).where(
            InviteLink.user_id == user_id,
            InviteLink.chat_id == chat_id
        )
    )
    return result.scalar_one()

@retry_db
async def get_valid_invite_links(session: AsyncSession, user_id: int):
    now = func.now()
    stmt = select(InviteLink).where(
        InviteLink.user_id == user_id,
        InviteLink.expires_at > now
    )
    res = await session.execute(stmt)
    return res.scalars().all()

@retry_db
async def get_invite_links(session: AsyncSession, user_id: int):
    stmt = select(InviteLink).where(
        InviteLink.user_id == user_id
    )
    res = await session.execute(stmt)
    return res.scalars().all()

@retry_db
async def delete_invite_links(session: AsyncSession, user_id: int):
    async with session.begin():
        await session.execute(delete(InviteLink).where(InviteLink.user_id == user_id))
