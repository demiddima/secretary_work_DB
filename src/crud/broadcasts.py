# src/crud/broadcasts.py
from __future__ import annotations

from typing import List, Optional, Dict, Any
from sqlalchemy import select, delete, insert, update, and_
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
    BroadcastTargetIds,
    BroadcastTargetSql,
    BroadcastTargetKind,
    DeliveryMaterializeRequest,
    DeliveryMaterializeResponse,
    DeliveryReportRequest,
    DeliveryReportResponse,
)
from src.time_msk import now_msk_naive, to_msk_naive
from src.audience_sql import exec_preview
from src.utils import BROADCAST_KINDS


# ----------------- helpers -----------------

_RESOLVE_CAP = 500_000
_INSERT_CHUNK = 1_000
_UPDATE_CHUNK = 1_000


def _cap(n: Optional[int], hi: int) -> int:
    if n is None:
        return hi
    try:
        return max(0, min(int(n), int(hi)))
    except Exception:
        return hi


def _uniq_keep_order(ids: List[int], limit: Optional[int] = None) -> List[int]:
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


async def _load_saved_target(session: AsyncSession, broadcast_id: int) -> Optional[BroadcastTargetCreate]:
    res = await session.execute(
        select(BroadcastTarget).where(BroadcastTarget.broadcast_id == broadcast_id).limit(1)
    )
    t: Optional[BroadcastTarget] = res.scalars().first()
    if not t:
        return None
    if t.type == "ids":
        return BroadcastTargetIds(type="ids", user_ids=t.user_ids_json or [])
    if t.type == "sql":
        return BroadcastTargetSql(type="sql", sql=t.sql_text or "")
    if t.type == "kind":
        return BroadcastTargetKind(type="kind", kind=t.kind)
    return None


async def _resolve_target_ids(
    session: AsyncSession,
    target: BroadcastTargetCreate,
    *,
    limit: Optional[int],
) -> List[int]:
    """
    Поддерживаем ids|kind|sql. Возвращаем uniq + keep order до limit.
    """
    if target.type == "ids":
        return _uniq_keep_order(list(target.user_ids), limit)

    if target.type == "kind":
        if target.kind not in BROADCAST_KINDS:
            raise ValueError(f"Unknown kind: {target.kind}")
        flag_col = {
            "news": UserSubscription.news_enabled,
            "meetings": UserSubscription.meetings_enabled,
            "important": UserSubscription.important_enabled,
        }[target.kind]
        q = select(UserSubscription.user_id).where(flag_col.is_(True))  # noqa: E712
        if limit:
            q = q.limit(limit)
        rows = (await session.execute(q)).scalars().all()
        return _uniq_keep_order([int(x) for x in rows], limit)

    if target.type == "sql":
        ids = await exec_preview(session, target.sql, limit=limit or _RESOLVE_CAP)
        return _uniq_keep_order([int(x) for x in ids], limit)

    return []


# ----------------- broadcasts -----------------

async def create_broadcast(session: AsyncSession, payload: BroadcastCreate) -> Broadcast:
    """
    Создание рассылки.
    content — JSON (dict) вида {"text": "<html>", "files": "id1,id2"}.
    Все таймстемпы выставляются приложением в МСК (naive).
    NEW: сохраняем schedule и enabled.
    """
    content_dict: Dict[str, Any] = (
        payload.content.model_dump()
        if hasattr(payload.content, "model_dump")
        else dict(payload.content)  # type: ignore[arg-type]
    )

    obj = Broadcast(
        kind=payload.kind,
        title=payload.title,
        content=content_dict,
        status=payload.status,
        scheduled_at=to_msk_naive(payload.scheduled_at) if payload.scheduled_at else None,
        # NEW:
        schedule=payload.schedule,
        enabled=bool(payload.enabled),
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


async def list_broadcasts(
    session: AsyncSession,
    *,
    status: Optional[str] = None,
    enabled: Optional[bool] = None,
    limit: int = 100,
    offset: int = 0,
) -> List[Broadcast]:
    """
    Возвращает список рассылок.
    NEW: поддержка фильтров status и enabled.
    """
    stmt = select(Broadcast).order_by(Broadcast.id.desc()).limit(limit).offset(offset)
    if status is not None:
        stmt = stmt.where(Broadcast.status == status)
    if enabled is not None:
        stmt = stmt.where(Broadcast.enabled == enabled)
    res = await session.execute(stmt)
    return list(res.scalars().all())


async def update_broadcast(session: AsyncSession, broadcast_id: int, patch: BroadcastUpdate) -> Optional[Broadcast]:
    """
    Частичное обновление. Если приходит scheduled_at — приводим к МСК-naive.
    Всегда обновляем updated_at (МСК-naive).
    NEW: поддержка полей schedule и enabled.
    """
    obj = await session.get(Broadcast, broadcast_id)
    if not obj:
        return None

    data = patch.model_dump(exclude_unset=True)

    if "scheduled_at" in data and data["scheduled_at"] is not None:
        data["scheduled_at"] = to_msk_naive(data["scheduled_at"])

    if "content" in data and data["content"] is not None:
        c = data["content"]
        data["content"] = c.model_dump() if hasattr(c, "model_dump") else c

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
    Немедленная отправка: переводим в 'scheduled' и scheduled_at=сейчас (МСК-naive).
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
    res = await session.execute(
        select(BroadcastTarget).where(BroadcastTarget.broadcast_id == broadcast_id).limit(1)
    )
    return res.scalars().first()


async def put_target(session: AsyncSession, broadcast_id: int, payload: BroadcastTargetCreate) -> BroadcastTarget:
    """
    Один таргет на рассылку: удаляем старый и создаём новый.
    """
    await session.execute(delete(BroadcastTarget).where(BroadcastTarget.broadcast_id == broadcast_id))

    if payload.type == "ids":
        obj = BroadcastTarget(broadcast_id=broadcast_id, type="ids", user_ids_json=payload.user_ids)
    elif payload.type == "sql":
        obj = BroadcastTarget(broadcast_id=broadcast_id, type="sql", sql_text=payload.sql)
    else:  # kind
        if payload.kind not in BROADCAST_KINDS:
            raise ValueError(f"Unknown kind: {payload.kind}")
        obj = BroadcastTarget(broadcast_id=broadcast_id, type="kind", kind=payload.kind)

    obj.created_at = now_msk_naive()
    session.add(obj)
    await session.commit()
    await session.refresh(obj)
    return obj


# ----------------- deliveries -----------------

async def list_deliveries(
    session: AsyncSession,
    broadcast_id: int,
    *,
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


async def deliveries_materialize(
    session: AsyncSession,
    broadcast_id: int,
    req: DeliveryMaterializeRequest,
) -> DeliveryMaterializeResponse:
    """
    Создаёт недостающие BroadcastDelivery(pending) для заданной аудитории.
    Источник: req.ids или req.target или сохранённый таргет.
    """
    limit = _cap(req.limit, _RESOLVE_CAP)

    if req.ids:
        ids = _uniq_keep_order([int(x) for x in req.ids], limit)
    else:
        target = req.target or await _load_saved_target(session, broadcast_id)
        if not target:
            return DeliveryMaterializeResponse(total=0, created=0, existed=0)
        ids = await _resolve_target_ids(session, target, limit=limit)

    if not ids:
        return DeliveryMaterializeResponse(total=0, created=0, existed=0)

    # уже существующие
    existed_rows = await session.execute(
        select(BroadcastDelivery.user_id).where(
            and_(
                BroadcastDelivery.broadcast_id == broadcast_id,
                BroadcastDelivery.user_id.in_(ids),
            )
        )
    )
    existed = {int(x) for (x,) in existed_rows.all()}
    to_insert = [uid for uid in ids if uid not in existed]

    if to_insert:
        values = [
            {
                "broadcast_id": broadcast_id,
                "user_id": uid,
                "status": "pending",
                "attempts": 0,
                "created_at": now_msk_naive(),
            }
            for uid in to_insert
        ]
        for i in range(0, len(values), _INSERT_CHUNK):
            await session.execute(insert(BroadcastDelivery), values[i : i + _INSERT_CHUNK])

    await session.commit()
    return DeliveryMaterializeResponse(total=len(ids), created=len(to_insert), existed=len(existed))


async def deliveries_report(
    session: AsyncSession,
    broadcast_id: int,
    req: DeliveryReportRequest,
) -> DeliveryReportResponse:
    """
    Принимаем батч статусов доставки и обновляем строки по (broadcast_id, user_id).
    Если записи нет — создаём.
    """
    items = req.items or []
    if not items:
        return DeliveryReportResponse(processed=0, updated=0, inserted=0)

    processed = updated = inserted = 0

    # сгруппируем по uid
    by_uid: Dict[int, Any] = {}
    for it in items:
        try:
            uid = int(it.user_id)
        except Exception:
            continue
        if uid <= 0:
            continue
        by_uid[uid] = it

    uids = list(by_uid.keys())
    for i in range(0, len(uids), _UPDATE_CHUNK):
        chunk = uids[i : i + _UPDATE_CHUNK]

        # какие уже есть
        existing_rows = await session.execute(
            select(BroadcastDelivery.user_id).where(
                and_(
                    BroadcastDelivery.broadcast_id == broadcast_id,
                    BroadcastDelivery.user_id.in_(chunk),
                )
            )
        )
        existing = {int(x) for (x,) in existing_rows.all()}

        # обновим существующие
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

        # вставим недостающие
        to_insert = [uid for uid in chunk if uid not in existing]
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
