# src/crud/subscriptions.py
from .base import (
    retry_db, AsyncSession, select, update, delete, mysql_insert, IntegrityError
)
from sqlalchemy.exc import NoResultFound
from sqlalchemy import literal
from src.models import UserSubscription
from src.time_msk import now_msk_naive  # ⬅ MSK-naive

DEFAULTS = {
    "news_enabled": False,
    "meetings_enabled": True,
    "important_enabled": True,
}


@retry_db
async def get_user_subscriptions(session: AsyncSession, user_id: int) -> UserSubscription | None:
    res = await session.execute(select(UserSubscription).where(UserSubscription.user_id == user_id))
    return res.scalar_one_or_none()


@retry_db
async def ensure_user_subscriptions_defaults(session: AsyncSession, user_id: int) -> UserSubscription | None:
    """
    Создаёт запись с дефолтами, если её нет. Если есть — освежает updated_at.
    На нарушение FK (нет user) возбуждаем ValueError — пусть роутер отдаёт 422 (или вызывающая сторона игнорирует).
    """
    now = now_msk_naive()
    stmt = mysql_insert(UserSubscription).values(
        user_id=user_id,
        news_enabled=DEFAULTS["news_enabled"],
        meetings_enabled=DEFAULTS["meetings_enabled"],
        important_enabled=DEFAULTS["important_enabled"],
        created_at=now,
        updated_at=now,
    ).on_duplicate_key_update(
        # просто освежим updated_at, флаги не трогаем
        updated_at=literal(now),
    )

    try:
        await session.execute(stmt)
        await session.commit()
    except IntegrityError as e:
        await session.rollback()
        # FK (MySQL 1452): Cannot add or update a child row
        code = None
        orig = getattr(e, "orig", None)
        if orig is not None:
            try:
                code = int(getattr(orig, "args", [None])[0])
            except Exception:
                code = None
        if code == 1452:
            raise ValueError(f"FK violation for subscriptions: ensure user_id={user_id} exists") from e
        raise

    res = await session.execute(select(UserSubscription).where(UserSubscription.user_id == user_id))
    return res.scalar_one_or_none()


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
    Идемпотентный upsert (PUT): вставка или полная замена всех флагов.
    created_at/updated_at — MSK-naive.
    """
    now = now_msk_naive()
    stmt = mysql_insert(UserSubscription).values(
        user_id=user_id,
        news_enabled=bool(news_enabled),
        meetings_enabled=bool(meetings_enabled),
        important_enabled=bool(important_enabled),
        created_at=now,
        updated_at=now,
    ).on_duplicate_key_update(
        news_enabled=literal(bool(news_enabled)),
        meetings_enabled=literal(bool(meetings_enabled)),
        important_enabled=literal(bool(important_enabled)),
        updated_at=literal(now),
    )

    try:
        await session.execute(stmt)
        await session.commit()
    except IntegrityError as e:
        await session.rollback()
        code = None
        orig = getattr(e, "orig", None)
        if orig is not None:
            try:
                code = int(getattr(orig, "args", [None])[0])
            except Exception:
                code = None
        # FK нарушен: нет такого пользователя
        if code == 1452:
            raise ValueError(f"FK violation for subscriptions: ensure user_id={user_id} exists") from e
        raise

    res = await session.execute(select(UserSubscription).where(UserSubscription.user_id == user_id))
    sub = res.scalar_one_or_none()
    if sub is None:
        # очень редкий случай гонки/удаления между commit и select
        raise NoResultFound
    return sub


@retry_db
async def update_user_subscriptions(
    session: AsyncSession,
    user_id: int,
    **fields,
) -> UserSubscription:
    """
    PATCH (частичное обновление) + updated_at (MSK).
    Если записи нет — NoResultFound.
    """
    allowed = {k: v for k, v in fields.items() if k in {"news_enabled", "meetings_enabled", "important_enabled"}}
    res = await session.execute(select(UserSubscription).where(UserSubscription.user_id == user_id))
    sub = res.scalar_one_or_none()
    if sub is None:
        raise NoResultFound

    if not allowed:
        return sub

    allowed["updated_at"] = now_msk_naive()
    await session.execute(
        update(UserSubscription)
        .where(UserSubscription.user_id == user_id)
        .values(**allowed)
    )
    await session.commit()

    res = await session.execute(select(UserSubscription).where(UserSubscription.user_id == user_id))
    return res.scalar_one()


@retry_db
async def toggle_user_subscription(session: AsyncSession, *, user_id: int, kind: str) -> UserSubscription:
    """
    Переключение одного из флагов: kind in {"news", "meetings", "important"}.
    Если записи нет — NoResultFound.
    """
    if kind not in {"news", "meetings", "important"}:
        raise ValueError("invalid kind")

    res = await session.execute(select(UserSubscription).where(UserSubscription.user_id == user_id))
    sub = res.scalar_one_or_none()
    if sub is None:
        raise NoResultFound

    current = {
        "news": bool(sub.news_enabled),
        "meetings": bool(sub.meetings_enabled),
        "important": bool(sub.important_enabled),
    }
    new_value = not current[kind]

    await session.execute(
        update(UserSubscription)
        .where(UserSubscription.user_id == user_id)
        .values({f"{kind}_enabled": new_value, "updated_at": now_msk_naive()})
    )
    await session.commit()

    res = await session.execute(select(UserSubscription).where(UserSubscription.user_id == user_id))
    return res.scalar_one()


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

    current = {
        "news": bool(sub.news_enabled),
        "meetings": bool(sub.meetings_enabled),
        "important": bool(sub.important_enabled),
    }
    new_value = not current[kind]

    await session.execute(
        update(UserSubscription)
        .where(UserSubscription.user_id == user_id)
        .values({f"{kind}_enabled": new_value, "updated_at": now_msk_naive()})
    )
    await session.commit()

    res = await session.execute(select(UserSubscription).where(UserSubscription.user_id == user_id))
    return res.scalar_one()
