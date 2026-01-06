# src/crud/users.py
# commit: исправление — добавление пользователя и его подписки в чат в одной сессии

from __future__ import annotations

from .base import (
    AsyncSession,
    IntegrityError,
    delete,
    mysql_insert,
    retry_db,
    select,
    update,
)
from src.models import User, UserMembership
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException
from sqlalchemy.orm import Session

# Функция для проверки сессии
def get_session_or_create(session: AsyncSession | None) -> AsyncSession:
    if session is None:
        raise HTTPException(status_code=400, detail="Session is required")
    return session


@retry_db
async def upsert_user(
    session: AsyncSession,
    *,
    id: int,
    username: str | None,
    full_name: str | None,
    terms_accepted: bool | None = None,
) -> User:
    terms_val = False if terms_accepted is None else terms_accepted

    stmt = mysql_insert(User).values(
        id=id,
        username=username,
        full_name=full_name,
        terms_accepted=terms_val
    )

    update_fields: dict[str, object] = {
        "username": stmt.inserted.username,
        "full_name": stmt.inserted.full_name,
        "terms_accepted": stmt.inserted.terms_accepted,
    }

    stmt = stmt.on_duplicate_key_update(**update_fields)

    try:
        await session.execute(stmt)
        await session.flush()  # Сохраняем изменения в сессию
    except IntegrityError as e:
        await session.rollback()  # Откатываем транзакцию в случае ошибки
        raise

    # После выполнения upsert пытаемся получить пользователя
    user = await session.get(User, id)
    if user is None:
        raise RuntimeError(f"Failed to fetch user after upsert: id={id}")
    
    return user

@retry_db
async def get_user(session: AsyncSession, *, id: int) -> User | None:
    stmt = select(User).where(User.id == id)
    res = await session.execute(stmt)
    return res.scalar_one_or_none()


@retry_db
async def update_user(session: AsyncSession, *, id: int, **fields) -> None:
    stmt = update(User).where(User.id == id).values(**fields)
    async with session.begin():
        await session.execute(stmt)


@retry_db
async def delete_user(session: AsyncSession, *, id: int) -> None:
    stmt = delete(User).where(User.id == id)
    async with session.begin():
        await session.execute(stmt)


@retry_db
async def upsert_user_to_chat(session: AsyncSession, *, user_id: int, chat_id: int) -> UserMembership:
    stmt = select(UserMembership).where(
        UserMembership.user_id == user_id,
        UserMembership.chat_id == chat_id,
    )

    res = await session.execute(stmt)
    existed = res.scalar_one_or_none()
    if existed is not None:
        return existed

    # Добавление в таблицу UserMembership
    obj = UserMembership(user_id=user_id, chat_id=chat_id)
    session.add(obj)

    try:
        await session.flush()  # Сохраняем изменения в сессию
        await session.commit()  # Зафиксировать транзакцию
    except IntegrityError as e:
        await session.rollback()  # Откатываем транзакцию при ошибке
        raise

    return obj

@retry_db
async def remove_user_from_chat(session: AsyncSession, *, user_id: int, chat_id: int) -> None:
    stmt = delete(UserMembership).where(
        UserMembership.user_id == user_id,
        UserMembership.chat_id == chat_id
    )
    async with session.begin():
        await session.execute(stmt)


@retry_db
async def is_user_in_chat(session: AsyncSession, *, user_id: int, chat_id: int) -> bool:
    stmt = select(UserMembership.user_id).where(
        UserMembership.user_id == user_id,
        UserMembership.chat_id == chat_id,
    )
    res = await session.execute(stmt)
    return res.scalar_one_or_none() is not None


@retry_db
async def list_memberships_by_chat(
    session: AsyncSession,
    *,
    chat_id: int,
    limit: int | None = None,
    offset: int | None = None,
) -> list[int]:
    q = select(UserMembership.user_id).where(UserMembership.chat_id == chat_id).order_by(UserMembership.user_id)
    if offset:
        q = q.offset(int(offset))
    if limit:
        q = q.limit(int(limit))
    res = await session.execute(q)
    return [int(r[0]) for r in res.fetchall()]


@retry_db
async def upsert_user_and_membership(
    session: AsyncSession,
    *,
    user_id: int,
    username: str,
    full_name: str,
    chat_id: int,
    terms_accepted: bool | None = None,
) -> User:
    async with session.begin():  # Начинаем транзакцию для всех операций
        # Создаем или обновляем пользователя
        user = await upsert_user(
            session,
            id=user_id,
            username=username,
            full_name=full_name,
            terms_accepted=terms_accepted
        )

        # Подписка пользователя на чат
        await upsert_user_to_chat(session, user_id=user_id, chat_id=chat_id)

    return user