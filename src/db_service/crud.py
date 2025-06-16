from sqlalchemy import select, update, delete, func
from sqlalchemy.ext.asyncio import AsyncSession
from .models import (
    Chat, User, UserMembership, InviteLink, UserAlgorithmProgress
)

# ---- Chats ----
async def upsert_chat(session: AsyncSession, chat_id: int, title: str, type_: str):
    stmt = select(Chat).where(Chat.id == chat_id)
    res = await session.execute(stmt)
    chat = res.scalar_one_or_none()
    if chat:
        chat.title = title
        chat.type = type_
    else:
        chat = Chat(id=chat_id, title=title, type=type_)
        session.add(chat)
    await session.commit()
    return chat

async def delete_chat(session: AsyncSession, chat_id: int):
    await session.execute(delete(Chat).where(Chat.id == chat_id))
    await session.commit()

async def get_all_chats(session: AsyncSession):
    res = await session.execute(select(Chat.id))
    return [row[0] for row in res.all()]

# ---- Users ----
async def create_user(session: AsyncSession, id: int, username: str = None, full_name: str = None):
    user = User(id=id, username=username, full_name=full_name)
    session.add(user)
    await session.commit()
    return user

async def get_user(session: AsyncSession, id: int):
    res = await session.execute(select(User).where(User.id == id))
    return res.scalar_one_or_none()

async def update_user(session: AsyncSession, id: int, **fields):
    await session.execute(update(User).where(User.id == id).values(**fields))
    await session.commit()

async def delete_user(session: AsyncSession, id: int):
    await session.execute(delete(User).where(User.id == id))
    await session.commit()

# ---- Memberships ----
async def add_user_to_chat(session: AsyncSession, user_id: int, chat_id: int):
    membership = UserMembership(user_id=user_id, chat_id=chat_id)
    session.add(membership)
    await session.commit()
    return membership

async def remove_user_from_chat(session: AsyncSession, user_id: int, chat_id: int):
    await session.execute(
        delete(UserMembership)
        .where(UserMembership.user_id == user_id)
        .where(UserMembership.chat_id == chat_id)
    )
    await session.commit()

# ---- Invite Links ----
async def save_invite_link(
    session: AsyncSession, user_id: int, chat_id: int,
    invite_link: str, created_at, expires_at
):
    link = InviteLink(
        user_id=user_id, chat_id=chat_id,
        invite_link=invite_link,
        created_at=created_at, expires_at=expires_at
    )
    session.add(link)
    await session.commit()
    return link

async def get_valid_invite_links(session: AsyncSession, user_id: int):
    now = func.now()
    res = await session.execute(
        select(InviteLink)
        .where(InviteLink.user_id == user_id)
        .where(InviteLink.expires_at > now)
    )
    return res.scalars().all()

async def delete_invite_links(session: AsyncSession, user_id: int):
    await session.execute(
        delete(InviteLink).where(InviteLink.user_id == user_id)
    )
    await session.commit()

# ---- Algorithm Progress ----
async def get_user_step(session: AsyncSession, user_id: int):
    res = await session.execute(
        select(UserAlgorithmProgress.current_step)
        .where(UserAlgorithmProgress.user_id == user_id)
    )
    return res.scalar_one_or_none()

async def set_user_step(session: AsyncSession, user_id: int, step: int):
    obj = await session.get(UserAlgorithmProgress, user_id)
    if obj:
        obj.current_step = step
    else:
        obj = UserAlgorithmProgress(user_id=user_id, current_step=step)
        session.add(obj)
    await session.commit()
    return obj

async def get_basic_completed(session: AsyncSession, user_id: int):
    res = await session.execute(
        select(UserAlgorithmProgress.basic_completed)
        .where(UserAlgorithmProgress.user_id == user_id)
    )
    return res.scalar_one_or_none()

async def set_basic_completed(session: AsyncSession, user_id: int, completed: bool):
    obj = await session.get(UserAlgorithmProgress, user_id)
    if obj:
        obj.basic_completed = completed
    else:
        obj = UserAlgorithmProgress(user_id=user_id, basic_completed=completed)
        session.add(obj)
    await session.commit()
    return obj

async def get_advanced_completed(session: AsyncSession, user_id: int):
    res = await session.execute(
        select(UserAlgorithmProgress.advanced_completed)
        .where(UserAlgorithmProgress.user_id == user_id)
    )
    return res.scalar_one_or_none()

async def set_advanced_completed(session: AsyncSession, user_id: int, completed: bool):
    obj = await session.get(UserAlgorithmProgress, user_id)
    if obj:
        obj.advanced_completed = completed
    else:
        obj = UserAlgorithmProgress(user_id=user_id, advanced_completed=completed)
        session.add(obj)
    await session.commit()
    return obj

async def clear_user_data(session: AsyncSession, user_id: int):
    await session.execute(
        delete(UserAlgorithmProgress).where(UserAlgorithmProgress.user_id == user_id)
    )
    await session.commit()
