from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from sqlalchemy.exc import OperationalError
from sqlalchemy import select, delete, func
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException

from .models import (
    Chat, User, UserMembership, InviteLink, UserAlgorithmProgress, Setting, Link
)

# Retry configuration: up to 5 attempts, exponential backoff
retry_db = retry(
    reraise=True,
    retry=retry_if_exception_type(OperationalError),
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=1, min=1, max=10),
)

# ---- Chats ----
@retry_db
async def upsert_chat(session: AsyncSession, chat_id: int, title: str, type_: str):
    async with session.begin():
        stmt = select(Chat).where(Chat.id == chat_id)
        res = await session.execute(stmt)
        chat = res.scalar_one_or_none()
        if chat:
            chat.title = title
            chat.type = type_
        else:
            chat = Chat(id=chat_id, title=title, type=type_)
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

# ---- Users ----
@retry_db
async def upsert_user(session: AsyncSession, id: int, username: str = None, full_name: str = None):
    async with session.begin():
        stmt = select(User).where(User.id == id)
        res = await session.execute(stmt)
        user = res.scalar_one_or_none()
        if user:
            user.username = username
            user.full_name = full_name
        else:
            user = User(id=id, username=username, full_name=full_name)
            session.add(user)
    return user

@retry_db
async def get_user(session: AsyncSession, id: int):
    stmt = select(User).where(User.id == id)
    res = await session.execute(stmt)
    return res.scalar_one_or_none()

@retry_db
async def update_user(session: AsyncSession, id: int, **fields):
    async with session.begin():
        await session.execute(
            update(User).where(User.id == id).values(**fields)
        )

@retry_db
async def delete_user(session: AsyncSession, id: int):
    async with session.begin():
        await session.execute(delete(User).where(User.id == id))

# ---- Memberships ----
@retry_db
async def upsert_user_to_chat(session: AsyncSession, user_id: int, chat_id: int):
    async with session.begin():
        stmt = select(UserMembership).where(
            UserMembership.user_id == user_id,
            UserMembership.chat_id == chat_id
        )
        res = await session.execute(stmt)
        membership = res.scalar_one_or_none()
        if not membership:
            membership = UserMembership(user_id=user_id, chat_id=chat_id)
            session.add(membership)
    return membership

@retry_db
async def remove_user_from_chat(session: AsyncSession, user_id: int, chat_id: int):
    async with session.begin():
        await session.execute(
            delete(UserMembership)
            .where(UserMembership.user_id == user_id)
            .where(UserMembership.chat_id == chat_id)
        )

# ---- Invite Links ----
@retry_db
async def save_invite_link(
    session: AsyncSession, user_id: int, chat_id: int,
    invite_link: str, created_at, expires_at
):
    async with session.begin():
        link = InviteLink(
            user_id=user_id, chat_id=chat_id,
            invite_link=invite_link,
            created_at=created_at, expires_at=expires_at
        )
        session.add(link)
    return link

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
async def delete_invite_links(session: AsyncSession, user_id: int):
    async with session.begin():
        await session.execute(delete(InviteLink).where(InviteLink.user_id == user_id))

# ---- Algorithm Progress ----
@retry_db
async def get_user_step(session: AsyncSession, user_id: int):
    stmt = select(UserAlgorithmProgress.current_step).where(UserAlgorithmProgress.user_id == user_id)
    res = await session.execute(stmt)
    return res.scalar_one_or_none()

@retry_db
async def set_user_step(session: AsyncSession, user_id: int, step: int):
    async with session.begin():
        obj = await session.get(UserAlgorithmProgress, user_id)
        if obj:
            obj.current_step = step
        else:
            obj = UserAlgorithmProgress(user_id=user_id, current_step=step)
            session.add(obj)
    return obj

@retry_db
async def get_basic_completed(session: AsyncSession, user_id: int):
    stmt = select(UserAlgorithmProgress.basic_completed).where(UserAlgorithmProgress.user_id == user_id)
    res = await session.execute(stmt)
    return res.scalar_one_or_none()

@retry_db
async def set_basic_completed(session: AsyncSession, user_id: int, completed: bool):
    async with session.begin():
        obj = await session.get(UserAlgorithmProgress, user_id)
        if obj:
            obj.basic_completed = completed
        else:
            obj = UserAlgorithmProgress(user_id=user_id, basic_completed=completed)
            session.add(obj)
    return obj

@retry_db
async def get_advanced_completed(session: AsyncSession, user_id: int):
    stmt = select(UserAlgorithmProgress.advanced_completed).where(UserAlgorithmProgress.user_id == user_id)
    res = await session.execute(stmt)
    return res.scalar_one_or_none()

@retry_db
async def set_advanced_completed(session: AsyncSession, user_id: int, completed: bool):
    async with session.begin():
        obj = await session.get(UserAlgorithmProgress, user_id)
        if obj:
            obj.advanced_completed = completed
        else:
            obj = UserAlgorithmProgress(user_id=user_id, advanced_completed=completed)
            session.add(obj)
    return obj

@retry_db
async def clear_user_data(session: AsyncSession, user_id: int):
    async with session.begin():
        await session.execute(delete(UserAlgorithmProgress).where(UserAlgorithmProgress.user_id == user_id))

# ---- Settings & Cleanup ----
@retry_db
async def get_cleanup_cron(session: AsyncSession):
    stmt = select(Setting.cleanup_cron).where(Setting.id == 1)
    res = await session.execute(stmt)
    return res.scalar_one_or_none() or '0 3 * * 6'

@retry_db
async def set_cleanup_cron(session: AsyncSession, cron_str: str):
    async with session.begin():
        obj = await session.get(Setting, 1)
        if obj:
            obj.cleanup_cron = cron_str
        else:
            obj = Setting(id=1, cleanup_cron=cron_str)
            session.add(obj)
    return obj

@retry_db
async def cleanup_orphan_users(session: AsyncSession):
    subq = select(UserMembership.user_id)
    stmt = select(User.id).where(~User.id.in_(subq))
    res = await session.execute(stmt)
    user_ids = [row[0] for row in res.all()]
    if user_ids:
        async with session.begin():
            await session.execute(delete(User).where(User.id.in_(user_ids)))
    return user_ids

@retry_db
async def increment_link_visit(session: AsyncSession, link_key: str) -> Link:
    stmt = select(Link).where(Link.link_key == link_key)
    result = await session.execute(stmt)
    link = result.scalars().first()

    if not link:
        raise HTTPException(status_code=404, detail="Link not found")

    link.visits += 1
    await session.commit()
    return link