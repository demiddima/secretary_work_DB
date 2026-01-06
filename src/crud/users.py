# src/crud/users.py

from __future__ import annotations

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, update

from .base import retry_db, mysql_insert, db_tx
from src.models import User, UserMembership


def _mysql_err_code(err: IntegrityError) -> int | None:
    """Достаём MySQL errno (1062, 1452 и т.д.) из IntegrityError."""
    orig = getattr(err, "orig", None)
    if orig is None:
        return None
    args = getattr(orig, "args", None)
    if not args:
        return None
    try:
        return int(args[0])
    except Exception:
        return None


@retry_db
async def upsert_user(
    session: AsyncSession,
    *,
    id: int,
    username: str | None,
    full_name: str | None,
    terms_accepted: bool | None = None,
) -> User:
    """
    Upsert пользователя (создать/обновить).
    Работает и отдельно (с COMMIT), и вложенно (через SAVEPOINT), без конфликтов транзакций.
    """
    terms_val = False if terms_accepted is None else terms_accepted

    insert_stmt = mysql_insert(User).values(
        id=id,
        username=username,
        full_name=full_name,
        terms_accepted=terms_val,
    )

    # ВАЖНО: используем insert_stmt.inserted.<col> ОТ ТОГО ЖЕ insert_stmt
    stmt = insert_stmt.on_duplicate_key_update(
        username=insert_stmt.inserted.username,
        full_name=insert_stmt.inserted.full_name,
        terms_accepted=insert_stmt.inserted.terms_accepted,
    )

    async with db_tx(session):
        try:
            await session.execute(stmt)
        except IntegrityError:
            # db_tx сам откатит нужный уровень (txn или savepoint)
            raise

        res = await session.execute(
            select(User).where(User.id == id).execution_options(populate_existing=True)
        )
        user = res.scalar_one_or_none()

    if user is None:
        raise RuntimeError(f"Не удалось прочитать пользователя после upsert: id={id}")
    return user


@retry_db
async def get_user(session: AsyncSession, *, id: int) -> User | None:
    """Получить пользователя по id."""
    res = await session.execute(select(User).where(User.id == id))
    return res.scalar_one_or_none()


@retry_db
async def update_user(session: AsyncSession, *, id: int, **fields) -> None:
    """
    Обновить поля пользователя.
    Работает и отдельно, и внутри общей транзакции (через db_tx).
    """
    async with db_tx(session):
        await session.execute(update(User).where(User.id == id).values(**fields))


@retry_db
async def delete_user(session: AsyncSession, *, id: int) -> None:
    """Удалить пользователя."""
    async with db_tx(session):
        await session.execute(delete(User).where(User.id == id))


@retry_db
async def upsert_user_to_chat(session: AsyncSession, *, user_id: int, chat_id: int) -> UserMembership:
    """
    Подписать пользователя на чат (user_memberships).

    Важно:
    - Если user/chat не существуют → MySQL FK 1452 → кидаем ValueError (под 422).
    - Дубликаты (уже подписан) → возвращаем существующую запись.
    - Отдельно/вложенно — одинаково стабильно (db_tx + SAVEPOINT).
    """
    stmt_find = select(UserMembership).where(
        UserMembership.user_id == user_id,
        UserMembership.chat_id == chat_id,
    )

    # Быстрая проверка (без транзакции)
    res = await session.execute(stmt_find)
    existed = res.scalar_one_or_none()
    if existed is not None:
        return existed

    obj = UserMembership(user_id=user_id, chat_id=chat_id)

    try:
        async with db_tx(session):
            session.add(obj)
            await session.flush()
        return obj

    except IntegrityError as e:
        code = _mysql_err_code(e)

        # Дубликат: кто-то успел вставить параллельно
        if code == 1062:
            res2 = await session.execute(stmt_find)
            dup = res2.scalar_one_or_none()
            if dup is not None:
                return dup
            raise

        # FK: нет user или нет chat
        if code == 1452:
            raise ValueError(
                f"FK violation: проверь, что user_id={user_id} существует в users "
                f"и chat_id={chat_id} существует в chats"
            ) from e

        raise


@retry_db
async def remove_user_from_chat(session: AsyncSession, *, user_id: int, chat_id: int) -> None:
    """Отписать пользователя от чата."""
    async with db_tx(session):
        await session.execute(
            delete(UserMembership)
            .where(UserMembership.user_id == user_id)
            .where(UserMembership.chat_id == chat_id)
        )


@retry_db
async def is_user_in_chat(session: AsyncSession, *, user_id: int, chat_id: int) -> bool:
    """Проверка подписки."""
    res = await session.execute(
        select(UserMembership.user_id).where(
            UserMembership.user_id == user_id,
            UserMembership.chat_id == chat_id,
        )
    )
    return res.scalar_one_or_none() is not None


@retry_db
async def list_memberships_by_chat(
    session: AsyncSession,
    *,
    chat_id: int,
    limit: int | None = None,
    offset: int | None = None,
) -> list[int]:
    """Список user_id в чате."""
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
    username: str | None,
    full_name: str | None,
    chat_id: int,
    terms_accepted: bool | None = None,
) -> User:
    """
    Атомарно: upsert пользователя + подписка на чат.

    Работает:
    - как отдельный вызов (COMMIT будет),
    - как часть более крупной транзакции (будет SAVEPOINT).
    """
    async with db_tx(session):
        user = await upsert_user(
            session,
            id=user_id,
            username=username,
            full_name=full_name,
            terms_accepted=terms_accepted,
        )
        await upsert_user_to_chat(session, user_id=user_id, chat_id=chat_id)
        return user
