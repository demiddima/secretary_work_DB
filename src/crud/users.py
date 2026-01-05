
# src/crud/users.py

from .base import retry_db, AsyncSession, select, delete, func, update, mysql_insert, IntegrityError
from src.models import User, UserMembership

@retry_db
async def upsert_user(
    session: AsyncSession,
    *,
    id: int,
    username: str | None,
    full_name: str | None,
    terms_accepted: bool | None = None
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
    }
    if terms_accepted is not None:
        update_fields["terms_accepted"] = stmt.inserted.terms_accepted
    stmt = stmt.on_duplicate_key_update(**update_fields)
    await session.execute(stmt)
    await session.commit()
    return await session.get(User, id)

@retry_db
async def get_user(session: AsyncSession, id: int):
    stmt = select(User).where(User.id == id)
    res = await session.execute(stmt)
    return res.scalar_one_or_none()

@retry_db
async def update_user(session: AsyncSession, id: int, **fields):
    async with session.begin():
        stmt = update(User).where(User.id == id).values(**fields)
        await session.execute(stmt)

@retry_db
async def delete_user(session: AsyncSession, id: int):
    async with session.begin():
        await session.execute(delete(User).where(User.id == id))

@retry_db
async def upsert_user_to_chat(session: AsyncSession, user_id: int, chat_id: int):
    # Быстрая проверка существования
    stmt = select(UserMembership).where(
        UserMembership.user_id == user_id,
        UserMembership.chat_id == chat_id
    )
    res = await session.execute(stmt)
    existed = res.scalar_one_or_none()
    if existed is not None:
        return existed

    # Пытаемся вставить
    obj = UserMembership(user_id=user_id, chat_id=chat_id)
    session.add(obj)
    try:
        await session.flush()
    except IntegrityError as e:
        # Откатываем текущее действие, чтобы сессия осталась консистентной
        await session.rollback()

        # Выясняем код MySQL (PyMySQL/aiomysql обычно кладут int-код в orig.args[0])
        code = None
        orig = getattr(e, "orig", None)
        if orig is not None:
            try:
                code = int(getattr(orig, "args", [None])[0])
            except Exception:
                code = None

        if code == 1062:
            # Дубликат: кто-то успел вставить — читаем спокойно
            res2 = await session.execute(stmt)
            dup = res2.scalar_one_or_none()
            if dup is not None:
                return dup
            # Если не нашли — пробрасываем исходную ошибку (нестандартная ситуация)
            raise

        if code == 1452:
            # FK нарушен: нет user или chat — это 422, а не 500
            raise ValueError(
                f"FK violation for membership: ensure user_id={user_id} and chat_id={chat_id} exist"
            ) from e

        # Иные причины — пробрасываем
        raise

    # Успешно
    await session.commit()
    return obj

@retry_db
async def remove_user_from_chat(session: AsyncSession, user_id: int, chat_id: int):
    async with session.begin():
        await session.execute(
            delete(UserMembership)
            .where(UserMembership.user_id == user_id)
            .where(UserMembership.chat_id == chat_id)
        )

@retry_db
async def is_user_in_chat(session: AsyncSession, user_id: int, chat_id: int) -> bool:
    stmt = select(UserMembership).where(
        UserMembership.user_id == user_id,
        UserMembership.chat_id == chat_id
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
) -> list[dict]:
    q = select(UserMembership.user_id).where(UserMembership.chat_id == chat_id).order_by(UserMembership.user_id)
    if offset:
        q = q.offset(int(offset))
    if limit:
        q = q.limit(int(limit))
    res = await session.execute(q)
    return [{"user_id": int(r[0])} for r in res.fetchall()]

@retry_db
async def upsert_user_and_membership(
    session: AsyncSession,
    user_id: int,
    username: str,
    full_name: str,
    chat_id: int,
    terms_accepted: bool | None = None
):
    """
    Обновляет или добавляет пользователя в базу данных и добавляет его в чат.
    """
    # Обновляем или добавляем пользователя
    await upsert_user(
        session,
        id=user_id,
        username=username,
        full_name=full_name,
        terms_accepted=terms_accepted
    )

    # Добавляем пользователя в чат
    await upsert_user_to_chat(session, user_id=user_id, chat_id=chat_id)