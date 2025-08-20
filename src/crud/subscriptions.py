# src/crud/subscriptions.py
from .base import (
    retry_db, AsyncSession, select, update, delete, mysql_insert
)
from sqlalchemy.exc import NoResultFound
from sqlalchemy import literal
from src.models import UserSubscription

DEFAULTS = {
    "news_enabled": False,
    "meetings_enabled": True,
    "important_enabled": True,
}


@retry_db
async def get_user_subscriptions(session: AsyncSession, user_id: int) -> UserSubscription | None:
    stmt = select(UserSubscription).where(UserSubscription.user_id == user_id)
    res = await session.execute(stmt)
    return res.scalar_one_or_none()


@retry_db
async def ensure_user_subscriptions_defaults(session: AsyncSession, user_id: int) -> UserSubscription:
    """
    Создаёт запись с дефолтами, если её нет.
    Если запись уже есть — ничего не меняет (no-op).
    """
    stmt = mysql_insert(UserSubscription).values(
        user_id=user_id,
        news_enabled=DEFAULTS["news_enabled"],
        meetings_enabled=DEFAULTS["meetings_enabled"],
        important_enabled=DEFAULTS["important_enabled"],
    ).on_duplicate_key_update(
        # no-op: присваиваем user_id самому себе
        user_id=UserSubscription.user_id
    )
    await session.execute(stmt)
    await session.commit()

    res = await session.execute(select(UserSubscription).where(UserSubscription.user_id == user_id))
    return res.scalar_one()


@retry_db
async def put_user_subscriptions(
    session: AsyncSession,
    *,
    user_id: int,
    news_enabled: bool,
    meetings_enabled: bool,
    important_enabled: bool,
) -> UserSubscription:
    """
    Upsert (PUT): вставка или полное обновление всех флагов.
    """
    stmt = mysql_insert(UserSubscription).values(
        user_id=user_id,
        news_enabled=news_enabled,
        meetings_enabled=meetings_enabled,
        important_enabled=important_enabled,
    ).on_duplicate_key_update(
        news_enabled=literal(news_enabled),
        meetings_enabled=literal(meetings_enabled),
        important_enabled=literal(important_enabled),
    )
    await session.execute(stmt)
    await session.commit()

    res = await session.execute(select(UserSubscription).where(UserSubscription.user_id == user_id))
    return res.scalar_one()


@retry_db
async def update_user_subscriptions(
    session: AsyncSession,
    user_id: int,
    **fields,
) -> UserSubscription:
    """
    Patch (частичное обновление полей).
    """
    allowed = {k: v for k, v in fields.items() if k in {"news_enabled", "meetings_enabled", "important_enabled"}}
    if not allowed:
        res = await session.execute(select(UserSubscription).where(UserSubscription.user_id == user_id))
        sub = res.scalar_one_or_none()
        if sub is None:
            raise NoResultFound
        return sub

    await session.execute(
        update(UserSubscription)
        .where(UserSubscription.user_id == user_id)
        .values(**allowed)
    )
    await session.commit()

    res = await session.execute(select(UserSubscription).where(UserSubscription.user_id == user_id))
    sub = res.scalar_one_or_none()
    if sub is None:
        raise NoResultFound
    return sub


@retry_db
async def delete_user_subscriptions(session: AsyncSession, user_id: int) -> None:
    await session.execute(delete(UserSubscription).where(UserSubscription.user_id == user_id))
    await session.commit()


@retry_db
async def toggle_user_subscription(session: AsyncSession, user_id: int, kind: str) -> UserSubscription:
    """
    Переключает один из флагов: news|meetings|important.
    Если записи нет — создаём с дефолтами, затем переключаем выбранный флаг.
    """
    if kind not in {"news", "meetings", "important"}:
        raise ValueError("Invalid kind")

    sub = await get_user_subscriptions(session, user_id)
    if sub is None:
        sub = await ensure_user_subscriptions_defaults(session, user_id)

    # вычисляем новое значение для выбранного флага
    current = {
        "news": bool(sub.news_enabled),
        "meetings": bool(sub.meetings_enabled),
        "important": bool(sub.important_enabled),
    }
    new_value = not current[kind]

    await session.execute(
        update(UserSubscription)
        .where(UserSubscription.user_id == user_id)
        .values({f"{kind}_enabled": new_value})
    )
    await session.commit()

    res = await session.execute(select(UserSubscription).where(UserSubscription.user_id == user_id))
    return res.scalar_one()
