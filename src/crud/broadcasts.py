# src/crud/broadcasts.py
from typing import List, Optional, Dict, Any
from sqlalchemy import select, delete, insert, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import (
    Broadcast,
    BroadcastTarget,
    BroadcastDelivery,
    UserSubscription,
)
from src.schemas import (
    BroadcastCreate,
    BroadcastUpdate,
    BroadcastTargetCreate,
    DeliveryMaterializeRequest,
    DeliveryMaterializeResponse,
    DeliveryReportRequest,
    DeliveryReportResponse,
)
from src.time_msk import now_msk_naive, to_msk_naive
from src.audience_sql import exec_preview


# ----------------- helpers -----------------

def _cap(n: int, hi: int) -> int:
    return max(0, min(int(n), int(hi)))


def _uniq_keep_order(ids: List[int], limit: int | None = None) -> List[int]:
    out: List[int] = []
    seen = set()
    lim = int(limit) if limit else None
    for x in ids:
        try:
            uid = int(x)
        except Exception:
            continue
        if uid <= 0 or uid in seen:
            continue
        seen.add(uid)
        out.append(uid)
        if lim is not None and len(out) >= lim:
            break
    return out


async def _resolve_target_ids(
    session: AsyncSession,
    broadcast_id: int,
    inline_target: Optional[BroadcastTargetCreate],
    limit: int,
) -> List[int]:
    """
    Резолв аудитории для materialize:
      - если inline_target есть → используем его,
      - иначе берём сохранённый BroadcastTarget по broadcast_id.
    Поддерживаем ids|kind|sql. Возвращаем uniq + keep order до limit.
    """
    # 1) взять таргет
    target: Optional[BroadcastTargetCreate] = inline_target
    if target is None:
        res = await session.execute(select(BroadcastTarget).where(BroadcastTarget.broadcast_id == broadcast_id).limit(1))
        t: Optional[BroadcastTarget] = res.scalars().first()
        if not t:
            return []
        if t.type == "ids":
            target = BroadcastTargetCreate(type="ids", user_ids=t.user_ids_json or [])
        elif t.type == "sql":
            target = BroadcastTargetCreate(type="sql", sql=t.sql_text or "")
        else:
            target = BroadcastTargetCreate(type="kind", kind=t.kind)  # type: ignore

    # 2) развернуть ids
    if target.type == "ids":
        return _uniq_keep_order(list(target.user_ids), limit)

    if target.type == "kind":
        kind = target.kind
        flag = f"{kind}_enabled"
        q = select(UserSubscription.user_id).where(getattr(UserSubscription, flag) == True)  # noqa: E712
        if limit:
            q = q.limit(limit)
        rows = (await session.execute(q)).scalars().all()
        return _uniq_keep_order(list(rows), limit)

    if target.type == "sql":
        ids = await exec_preview(session, target.sql, limit=limit)
        return _uniq_keep_order(list(ids), limit)

    return []


# ----------------- broadcasts -----------------

async def create_broadcast(session: AsyncSession, payload: BroadcastCreate) -> Broadcast:
    """
    Создание рассылки.
    Храним content как JSON (dict) вида {"text": "<html>", "files": "id1,id2"}.
    Все таймстемпы выставляются приложением в МСК (naive).
    """
    content_dict: Dict[str, Any] = payload.content.model_dump() if hasattr(payload.content, "model_dump") else dict(payload.content)  # type: ignore
    obj = Broadcast(
        kind=payload.kind,
        title=payload.title,
        content=content_dict,
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

    # content из pydantic-модели → dict
    if "content" in data and data["content"] is not None:
        content_val = data["content"]
        if hasattr(content_val, "model_dump"):
            data["content"] = content_val.model_dump()
        elif isinstance(content_val, dict):
            data["content"] = content_val
        else:
            # на всякий случай
            data["content"] = dict(content_val)

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


# ----------------- targets -----------------

async def get_target(session: AsyncSession, broadcast_id: int) -> Optional[BroadcastTarget]:
    res = await session.execute(select(BroadcastTarget).where(BroadcastTarget.broadcast_id == broadcast_id))
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


# ----------------- deliveries (read-only list) -----------------

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


# ----------------- NEW (optional): deliveries – materialize & report -----------------
# Оставлено для совместимости; маршруты используют собственные реализации в routers/deliveries.py

_INSERT_CHUNK = 1_000
_UPDATE_CHUNK = 1_000
_RESOLVE_CAP = 500_000


async def deliveries_materialize(
    session: AsyncSession,
    broadcast_id: int,
    req: DeliveryMaterializeRequest,
) -> DeliveryMaterializeResponse:
    limit = _cap(req.limit, _RESOLVE_CAP)
    if req.ids:
        ids = _uniq_keep_order(list(req.ids), limit)
    else:
        ids = await _resolve_target_ids(session, broadcast_id, req.target, limit)

    if not ids:
        return DeliveryMaterializeResponse(total=0, created=0, existed=0)

    existed: set[int] = set()
    for i in range(0, len(ids), _INSERT_CHUNK):
        chunk = ids[i : i + _INSERT_CHUNK]
        rows = await session.execute(
            select(BroadcastDelivery.user_id).where(
                BroadcastDelivery.broadcast_id == broadcast_id,
                BroadcastDelivery.user_id.in_(chunk),
            )
        )
        existed.update(int(x) for x in rows.scalars().all())

    to_insert = [uid for uid in ids if uid not in existed]
    created = 0

    if to_insert:
        for i in range(0, len(to_insert), _INSERT_CHUNK):
            chunk = to_insert[i : i + _INSERT_CHUNK]
            values = [
                {
                    "broadcast_id": broadcast_id,
                    "user_id": uid,
                    "status": "pending",
                    "attempts": 0,
                }
                for uid in chunk
            ]
            await session.execute(insert(BroadcastDelivery), values)
            created += len(values)

    await session.commit()
    return DeliveryMaterializeResponse(total=len(ids), created=created, existed=len(existed))


async def deliveries_report(
    session: AsyncSession,
    broadcast_id: int,
    req: DeliveryReportRequest,
) -> DeliveryReportResponse:
    items = req.items or []
    if not items:
        return DeliveryReportResponse(processed=0, updated=0, inserted=0)

    by_uid: Dict[int, Any] = {}
    for it in items:
        try:
            uid = int(it.user_id)
        except Exception:
            continue
        if uid <= 0:
            continue
        by_uid[uid] = it

    processed = updated = inserted = 0

    uids = list(by_uid.keys())
    for i in range(0, len(uids), _UPDATE_CHUNK):
        chunk_uids = uids[i : i + _UPDATE_CHUNK]

        rows = await session.execute(
            select(BroadcastDelivery.user_id).where(
                BroadcastDelivery.broadcast_id == broadcast_id,
                BroadcastDelivery.user_id.in_(chunk_uids),
            )
        )
        existing = set(int(x) for x in rows.scalars().all())

        for uid in existing:
            it = by_uid[uid]
            stmt = (
                update(BroadcastDelivery)
                .where(
                    BroadcastDelivery.broadcast_id == broadcast_id,
                    BroadcastDelivery.user_id == uid,
                )
                .values(
                    status=it.status,
                    attempts=BroadcastDelivery.attempts + (it.attempt_inc or 1),
                    message_id=it.message_id,
                    error_code=it.error_code,
                    error_message=it.error_message,
                    sent_at=it.sent_at,
                )
            )
            await session.execute(stmt)
            updated += 1
            processed += 1

        to_insert = [uid for uid in chunk_uids if uid not in existing]
        if to_insert:
            values = []
            for uid in to_insert:
                it = by_uid[uid]
                values.append(
                    {
                        "broadcast_id": broadcast_id,
                        "user_id": uid,
                        "status": it.status,
                        "attempts": int(it.attempt_inc or 1),
                        "message_id": it.message_id,
                        "error_code": it.error_code,
                        "error_message": it.error_message,
                        "sent_at": it.sent_at,
                        "created_at": now_msk_naive(),
                    }
                )
            await session.execute(insert(BroadcastDelivery), values)
            inserted += len(values)
            processed += len(values)

    await session.commit()
    return DeliveryReportResponse(processed=processed, updated=updated, inserted=inserted)
