# src/crud/ads.py
# commit: feat(crud): CRUD для Ad и AdRandomBranch (async SQLAlchemy)
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete

from src.models import Ad, AdRandomBranch
from src.schemas import (
    AdCreate, AdUpdate,
    RandomBranchCreate, RandomBranchUpdate,
)


# --- Ad ---

async def create_ad(session: AsyncSession, data: AdCreate) -> Ad:

    obj = Ad(
        title=data.title,
        chat_id=data.chat_id,
        thread_id=data.thread_id,
        content_json=data.content_json.model_dump(),
        schedule_type=data.schedule_type,
        schedule_cron=data.schedule_cron,
        n_days_start_date=data.n_days_start_date,
        n_days_time=data.n_days_time,
        n_days_interval=data.n_days_interval,
        enabled=data.enabled,
        delete_previous=data.delete_previous,
        dedupe_minute=data.dedupe_minute,
        auto_delete_ttl_hours=data.auto_delete_ttl_hours,
        auto_delete_cron=data.auto_delete_cron,
        created_by=data.created_by,
    )
    session.add(obj)
    await session.commit()
    await session.refresh(obj)
    return obj


async def get_ads(session: AsyncSession) -> List[Ad]:
    res = await session.execute(select(Ad).order_by(Ad.id.desc()))
    return res.scalars().all()


async def get_ad(session: AsyncSession, ad_id: int) -> Optional[Ad]:
    res = await session.execute(select(Ad).where(Ad.id == ad_id))
    return res.scalar_one_or_none()


async def update_ad(session: AsyncSession, ad_id: int, data: AdUpdate) -> Optional[Ad]:
    """
    Частичное обновление.
    Поддерживаем мягкий бридж: если вдруг прилетит legacy `content`, переложим его в `content_json`.
    """
    obj = await get_ad(session, ad_id)
    if not obj:
        return None

    payload = data.model_dump(exclude_unset=True)

    # Legacy-бридж: content -> content_json
    if "content" in payload and payload["content"] is not None:
        payload["content_json"] = payload.pop("content")

    # Если пришёл явно content_json — просто оставляем.
    # last_message_id: не перетирать на None
    if "last_message_id" in payload and payload["last_message_id"] is None:
        payload.pop("last_message_id")

    for k, v in payload.items():
        setattr(obj, k, v)

    await session.commit()
    await session.refresh(obj)
    return obj


async def delete_ad(session: AsyncSession, ad_id: int) -> bool:
    obj = await get_ad(session, ad_id)
    if not obj:
        return False
    await session.delete(obj)
    await session.commit()
    return True


# --- Random branches ---

async def upsert_random_branch(session: AsyncSession, data: RandomBranchCreate) -> AdRandomBranch:
    # Уникальность по (chat_id, thread_id)
    res = await session.execute(
        select(AdRandomBranch)
        .where(AdRandomBranch.chat_id == data.chat_id, AdRandomBranch.thread_id == data.thread_id)
    )
    obj = res.scalar_one_or_none()
    if obj:
        obj.window_from = data.window_from
        obj.window_to = data.window_to
        obj.rebuild_time = data.rebuild_time
        obj.enabled = data.enabled
    else:
        obj = AdRandomBranch(
            chat_id=data.chat_id,
            thread_id=data.thread_id,
            window_from=data.window_from,
            window_to=data.window_to,
            rebuild_time=data.rebuild_time,
            enabled=data.enabled,
        )
        session.add(obj)
    await session.commit()
    await session.refresh(obj)
    return obj


async def list_random_branches(session: AsyncSession) -> list[AdRandomBranch]:
    res = await session.execute(select(AdRandomBranch).order_by(AdRandomBranch.chat_id, AdRandomBranch.thread_id))
    return res.scalars().all()


async def get_random_branch(session: AsyncSession, branch_id: int) -> Optional[AdRandomBranch]:
    res = await session.execute(select(AdRandomBranch).where(AdRandomBranch.id == branch_id))
    return res.scalar_one_or_none()


async def get_random_branch_by_target(session: AsyncSession, chat_id: int, thread_id: Optional[int]) -> Optional[AdRandomBranch]:
    res = await session.execute(
        select(AdRandomBranch)
        .where(AdRandomBranch.chat_id == chat_id, AdRandomBranch.thread_id == thread_id)
    )
    return res.scalar_one_or_none()


async def update_random_branch(session: AsyncSession, branch_id: int, data: RandomBranchUpdate) -> Optional[AdRandomBranch]:
    obj = await get_random_branch(session, branch_id)
    if not obj:
        return None
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(obj, k, v)
    await session.commit()
    await session.refresh(obj)
    return obj


async def delete_random_branch(session: AsyncSession, branch_id: int) -> bool:
    obj = await get_random_branch(session, branch_id)
    if not obj:
        return False
    await session.delete(obj)
    await session.commit()
    return True
