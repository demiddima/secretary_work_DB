# src/routers/deliveries.py
from __future__ import annotations

from typing import List, Dict, Any, Optional

import logging
from fastapi import APIRouter, Depends, HTTPException, Path
from sqlalchemy import select, insert, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.dependencies import get_session
from src.models import UserSubscription, BroadcastTarget, BroadcastDelivery
from src.schemas import (
    DeliveryMaterializeRequest,
    DeliveryMaterializeResponse,
    DeliveryReportRequest,
    DeliveryReportResponse,
    BroadcastTargetCreate,  # union ids|kind|sql
)
from src.audience_sql import exec_preview, AudienceSQLValidationError

router = APIRouter(prefix="/broadcasts/{broadcast_id}/deliveries", tags=["deliveries"])
logger = logging.getLogger(__name__)

# Защитные верхние лимиты
_RESOLVE_CAP = 500_000
_INSERT_CHUNK = 1_000
_UPDATE_CHUNK = 1_000


def _cap(n: Optional[int], hi: int) -> int:
    return max(0, min(int(n or hi), hi))


def _uniq_keep_order(ids: List[Any], limit: int | None = None) -> List[int]:
    """uniq + keep order + опциональный лимит; фильтруем мусор/<=0."""
    out: List[int] = []
    seen = set()
    lim = int(limit) if limit else None
    for x in ids or []:
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


async def _resolve_target_full(session: AsyncSession, target: BroadcastTargetCreate, limit: int) -> List[int]:
    """Резолв аудитории на бэке: ids/kind/sql → полный список user_id (до limit)."""
    ttype = target.type
    if ttype == "ids":
        return _uniq_keep_order(list(getattr(target, "user_ids", []) or []), limit)

    if ttype == "kind":
        kind = getattr(target, "kind", None)
        if kind not in {"news", "meetings", "important"}:
            raise HTTPException(status_code=400, detail="Unknown kind")
        col = {
            "news": UserSubscription.news_enabled,
            "meetings": UserSubscription.meetings_enabled,
            "important": UserSubscription.important_enabled,
        }[kind]
        q = select(UserSubscription.user_id).where(col == True)  # noqa: E712
        if limit:
            q = q.limit(limit)
        rows = (await session.execute(q)).scalars().all()
        return _uniq_keep_order(rows, limit)

    if ttype == "sql":
        try:
            ids = await exec_preview(session, getattr(target, "sql", ""), limit=limit)
            return _uniq_keep_order(ids, limit)
        except AudienceSQLValidationError as e:
            raise HTTPException(status_code=400, detail=str(e))

    raise HTTPException(status_code=400, detail="Unsupported target.type")


@router.post("/materialize", response_model=DeliveryMaterializeResponse)
async def materialize_deliveries(
    payload: DeliveryMaterializeRequest,
    broadcast_id: int = Path(..., ge=1),
    session: AsyncSession = Depends(get_session),
):
    try:
        # None → без лимита; иначе кап до _RESOLVE_CAP
        limit = _cap(payload.limit, _RESOLVE_CAP) if (payload.limit is not None) else None

        # 0) Источник списка user_id
        ids: List[int] = []
        source = "stored"

        if payload.ids:
            ids = _uniq_keep_order(payload.ids, limit)
            source = f"inline_ids({len(payload.ids)})"

        elif payload.target:
            ids = await _resolve_target_full(session, payload.target, limit or 10_000_000)
            source = f"inline_target:{payload.target.type}"

        else:
            # Пытаемся взять таргет из таблицы broadcast_targets
            tgt = await session.execute(
                select(BroadcastTarget).where(BroadcastTarget.broadcast_id == broadcast_id).limit(1)
            )
            tgt_row: Optional[BroadcastTarget] = tgt.scalars().first()
            if not tgt_row:
                logger.warning(
                    f"[{broadcast_id}] - [POST /broadcasts/{broadcast_id}/deliveries/materialize] "
                    f"Нет inline-источника и не найден сохранённый target"
                )
                raise HTTPException(status_code=400, detail="No target provided and no target found for broadcast")

            # Собираем суррогат pydantic-объекта (минимум полей)
            # NOTE: поля из модели: user_ids_json, sql_text.
            tdict: Dict[str, Any] = {"type": tgt_row.type}
            if tgt_row.type == "ids":
                tdict["user_ids"] = (tgt_row.user_ids_json or [])
            elif tgt_row.type == "kind":
                tdict["kind"] = tgt_row.kind
            elif tgt_row.type == "sql":
                tdict["sql"] = tgt_row.sql_text
            else:
                raise HTTPException(status_code=400, detail="Unsupported stored target.type")
            ids = await _resolve_target_full(session, BroadcastTargetCreate.model_validate(tdict), limit)
            source = f"stored_target:{tgt_row.type}"

        total_in = len(ids)
        logger.info(
            f"[{broadcast_id}] - [POST /broadcasts/{broadcast_id}/deliveries/materialize] "
            f"Принят запрос материализации (source={source}, limit={limit}, total_in={total_in})"
        )

        if not ids:
            logger.info(
                f"[{broadcast_id}] - [POST /broadcasts/{broadcast_id}/deliveries/materialize] "
                f"Аудитория пуста — ничего не создано"
            )
            return DeliveryMaterializeResponse(total=0, created=0, existed=0)

        # 1) Достаём уже существующие deliveries по этому broadcast_id для переданных ids
        existed_set: set[int] = set()
        for i in range(0, len(ids), _INSERT_CHUNK):
            chunk = ids[i : i + _INSERT_CHUNK]
            rows = await session.execute(
                select(BroadcastDelivery.user_id).where(
                    BroadcastDelivery.broadcast_id == broadcast_id,
                    BroadcastDelivery.user_id.in_(chunk),
                )
            )
            existed_chunk = rows.scalars().all()
            existed_set.update(int(x) for x in existed_chunk)

        to_insert = [uid for uid in ids if uid not in existed_set]
        if not to_insert:
            logger.info(
                f"[{broadcast_id}] - [POST /broadcasts/{broadcast_id}/deliveries/materialize] "
                f"Все записи уже существовали (total={total_in}, existed={len(existed_set)})"
            )
            return DeliveryMaterializeResponse(total=total_in, created=0, existed=len(existed_set))

        # 2) Вставляем недостающие pending-записи батчами
        created = 0
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

        logger.info(
            f"[{broadcast_id}] - [POST /broadcasts/{broadcast_id}/deliveries/materialize] "
            f"Готово (created={created}, existed={len(existed_set)})"
        )
        return DeliveryMaterializeResponse(total=total_in, created=created, existed=len(existed_set))

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"[{broadcast_id}] - [POST /broadcasts/{broadcast_id}/deliveries/materialize] "
            f"Ошибка при материализации: {e}"
        )
        raise HTTPException(status_code=500, detail="Ошибка при материализации доставок")


@router.post("/report", response_model=DeliveryReportResponse)
async def report_deliveries(
    payload: DeliveryReportRequest,
    broadcast_id: int = Path(..., ge=1),
    session: AsyncSession = Depends(get_session),
):
    """
    Батч-обновление статусов для отправок данного broadcast_id.
    Не читает из таблицы, только пишет. Если записи не было — создаём её с указанным статусом.
    attempts инкрементируем на attempt_inc (по умолчанию 1).
    """
    try:
        items = payload.items or []
        if not items:
            logger.info(
                f"[{broadcast_id}] - [POST /broadcasts/{broadcast_id}/deliveries/report] "
                f"Пустой батч (0 items)"
            )
            return DeliveryReportResponse(processed=0, updated=0, inserted=0)

        logger.info(
            f"[{broadcast_id}] - [POST /broadcasts/{broadcast_id}/deliveries/report] "
            f"Принят батч на обновление статусов (items={len(items)})"
        )

        processed = updated = inserted = 0

        # Делаем чанками, чтобы не ловить таймауты и лишние round trips
        for i in range(0, len(items), _UPDATE_CHUNK):
            chunk = items[i : i + _UPDATE_CHUNK]

            # 1) Обновим тех, кто уже есть
            by_uid: Dict[int, Any] = {}
            for it in chunk:
                try:
                    uid = int(it.user_id)
                except Exception:
                    continue
                if uid <= 0:
                    continue
                by_uid[uid] = it

            if not by_uid:
                continue

            # Узнаём, кто уже есть в таблице
            rows = await session.execute(
                select(BroadcastDelivery.user_id).where(
                    BroadcastDelivery.broadcast_id == broadcast_id,
                    BroadcastDelivery.user_id.in_(list(by_uid.keys())),
                )
            )
            existing_uids = set(int(x) for x in rows.scalars().all())

            # Обновление существующих
            for uid in existing_uids:
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

            # Вставка тех, кого не было
            to_insert = [uid for uid in by_uid.keys() if uid not in existing_uids]
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
                        }
                    )
                await session.execute(insert(BroadcastDelivery), values)
                inserted += len(values)
                processed += len(values)

        await session.commit()

        logger.info(
            f"[{broadcast_id}] - [POST /broadcasts/{broadcast_id}/deliveries/report] "
            f"Обновлено: processed={processed}, updated={updated}, inserted={inserted}"
        )
        return DeliveryReportResponse(processed=processed, updated=updated, inserted=inserted)

    except Exception as e:
        logger.error(
            f"[{broadcast_id}] - [POST /broadcasts/{broadcast_id}/deliveries/report] "
            f"Ошибка при обновлении статусов: {e}"
        )
        raise HTTPException(status_code=500, detail="Ошибка при обновлении статусов доставок")
