
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
    stmt = select(UserMembership).where(
        UserMembership.user_id == user_id,
        UserMembership.chat_id == chat_id
    )
    res = await session.execute(stmt)
    membership = res.scalar_one_or_none()
    if membership is not None:
        return membership

    membership = UserMembership(user_id=user_id, chat_id=chat_id)
    session.add(membership)
    try:
        await session.flush()
    except IntegrityError:
        await session.rollback()
        res = await session.execute(stmt)
        membership = res.scalar_one()

    await session.commit()
    return membership

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
