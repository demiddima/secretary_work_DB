# src/crud/broadcasts.py
from typing import List, Optional
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import (
    Broadcast,
    BroadcastTarget,
    BroadcastMedia,
    BroadcastDelivery,
)
from src.schemas import (
    BroadcastCreate,
    BroadcastUpdate,
    BroadcastMediaPut,
    BroadcastTargetCreate,
)
from src.time_msk import now_msk_naive, to_msk_naive


async def create_broadcast(session: AsyncSession, payload: BroadcastCreate) -> Broadcast:
    """
    Создание рассылки.
    Все таймстемпы выставляются приложением в МСК (naive).
    """
    obj = Broadcast(
        kind=payload.kind,
        title=payload.title,
        content_html=payload.content_html,
        status=payload.status,
        scheduled_at=to_msk_naive(payload.scheduled_at) if payload.scheduled_at else None,
        created_by=payload.created_by,
        created_at=now_msk_naive(),
        updated_at=now_msk_naive(),
    )
    session.add(obj)
    await session.commit()
    await session.refresh(obj)
    return obj


async def get_broadcast(session: AsyncSession, broadcast_id: int) -> Optional[Broadcast]:
    return await session.get(Broadcast, broadcast_id)


async def list_broadcasts(session: AsyncSession, limit: int = 100, offset: int = 0) -> List[Broadcast]:
    q = select(Broadcast).order_by(Broadcast.id.desc()).limit(limit).offset(offset)
    res = await session.execute(q)
    return list(res.scalars().all())


async def update_broadcast(session: AsyncSession, broadcast_id: int, patch: BroadcastUpdate) -> Optional[Broadcast]:
    """
    Частичное обновление. Если приходит scheduled_at — приводим к МСК-naive.
    Всегда обновляем updated_at (МСК-naive).
    """
    obj = await session.get(Broadcast, broadcast_id)
    if not obj:
        return None

    data = patch.model_dump(exclude_unset=True)
    if "scheduled_at" in data and data["scheduled_at"] is not None:
        data["scheduled_at"] = to_msk_naive(data["scheduled_at"])

    for k, v in data.items():
        setattr(obj, k, v)

    obj.updated_at = now_msk_naive()
    await session.commit()
    await session.refresh(obj)
    return obj


async def delete_broadcast(session: AsyncSession, broadcast_id: int) -> bool:
    obj = await session.get(Broadcast, broadcast_id)
    if not obj:
        return False
    await session.delete(obj)
    await session.commit()
    return True


async def send_now(session: AsyncSession, broadcast_id: int) -> Optional[Broadcast]:
    """
    Переводит рассылку в статус 'scheduled' и ставит scheduled_at=сейчас (МСК-naive).
    Никаких func.now()/SQL NOW().
    """
    obj = await session.get(Broadcast, broadcast_id)
    if not obj:
        return None
    obj.status = "scheduled"
    obj.scheduled_at = now_msk_naive()
    obj.updated_at = now_msk_naive()
    await session.commit()
    await session.refresh(obj)
    return obj


# --- targets ---
async def get_target(session: AsyncSession, broadcast_id: int) -> Optional[BroadcastTarget]:
    q = select(BroadcastTarget).where(BroadcastTarget.broadcast_id == broadcast_id)
    res = await session.execute(q)
    return res.scalars().first()


async def put_target(session: AsyncSession, broadcast_id: int, payload: BroadcastTargetCreate) -> BroadcastTarget:
    # Один таргет на рассылку: удаляем старый
    await session.execute(delete(BroadcastTarget).where(BroadcastTarget.broadcast_id == broadcast_id))

    if payload.type == "ids":
        obj = BroadcastTarget(broadcast_id=broadcast_id, type="ids", user_ids_json=payload.user_ids)
    elif payload.type == "sql":
        obj = BroadcastTarget(broadcast_id=broadcast_id, type="sql", sql_text=payload.sql)
    else:  # kind
        obj = BroadcastTarget(broadcast_id=broadcast_id, type="kind", kind=payload.kind)

    session.add(obj)
    await session.commit()
    await session.refresh(obj)
    return obj


# --- media ---
async def get_media(session: AsyncSession, broadcast_id: int) -> List[BroadcastMedia]:
    res = await session.execute(
        select(BroadcastMedia).where(BroadcastMedia.broadcast_id == broadcast_id).order_by(BroadcastMedia.position.asc())
    )
    return list(res.scalars().all())


async def put_media(session: AsyncSession, broadcast_id: int, payload: BroadcastMediaPut) -> List[BroadcastMedia]:
    await session.execute(delete(BroadcastMedia).where(BroadcastMedia.broadcast_id == broadcast_id))
    objects: List[BroadcastMedia] = []
    for it in payload.items:
        obj = BroadcastMedia(
            broadcast_id=broadcast_id,
            type=it.type,
            payload_json=it.payload,
            position=it.position or 0,
        )
        objects.append(obj)
    for obj in objects:
        session.add(obj)
    await session.commit()
    return await get_media(session, broadcast_id)


# --- deliveries ---
async def list_deliveries(
    session: AsyncSession,
    broadcast_id: int,
    status: Optional[str] = None,
    limit: int = 200,
    offset: int = 0,
) -> List[BroadcastDelivery]:
    q = select(BroadcastDelivery).where(BroadcastDelivery.broadcast_id == broadcast_id)
    if status:
        q = q.where(BroadcastDelivery.status == status)
    q = q.order_by(BroadcastDelivery.id.asc()).limit(limit).offset(offset)
    res = await session.execute(q)
    return list(res.scalars().all())
