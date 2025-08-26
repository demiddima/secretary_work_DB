# src/routers/broadcasts.py
from typing import List, Optional
import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.dependencies import get_session
from src.schemas import (
    BroadcastCreate,
    BroadcastUpdate,
    BroadcastRead,
    BroadcastTargetCreate,
    BroadcastTargetRead,
    BroadcastDeliveryRead,
)
from src.crud.broadcasts import (
    create_broadcast,
    get_broadcast,
    list_broadcasts,
    update_broadcast,
    delete_broadcast,
    send_now,
    get_target,
    put_target,
    list_deliveries,
)

router = APIRouter(prefix="/broadcasts", tags=["broadcasts"])
logger = logging.getLogger(__name__)


@router.post("", response_model=BroadcastRead, status_code=201)
async def create(payload: BroadcastCreate, session: AsyncSession = Depends(get_session)):
    try:
        logger.info(
            "[POST /broadcasts] Создание рассылки: "
            f"title={payload.title!r}, kind={payload.kind!r}, status={payload.status!r}, "
            f"scheduled_at={payload.scheduled_at}, schedule={payload.schedule!r}, enabled={payload.enabled}"
        )
        obj = await create_broadcast(session, payload)
        logger.info(f"[{obj.id}] - [POST /broadcasts] Рассылка создана")
        return obj
    except Exception as e:
        logger.error(f"[POST /broadcasts] Ошибка при создании рассылки: {e}")
        raise HTTPException(status_code=500, detail="Ошибка при создании рассылки")


@router.get("/{broadcast_id}", response_model=BroadcastRead)
async def get(broadcast_id: int, session: AsyncSession = Depends(get_session)):
    try:
        obj = await get_broadcast(session, broadcast_id)
        if not obj:
            raise HTTPException(status_code=404, detail="Broadcast not found")
        logger.info(f"[{broadcast_id}] - [GET /broadcasts/{broadcast_id}] Ок")
        return obj
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[{broadcast_id}] - [GET /broadcasts/{broadcast_id}] Ошибка: {e}")
        raise HTTPException(status_code=500, detail="Ошибка при получении рассылки")


@router.get("", response_model=List[BroadcastRead])
async def list_(
    session: AsyncSession = Depends(get_session),
    status: Optional[str] = Query(default=None, description="Фильтр по статусу"),
    enabled: Optional[bool] = Query(default=None, description="Фильтр по флагу активности"),
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
):
    try:
        res = await list_broadcasts(session, status=status, enabled=enabled, limit=limit, offset=offset)
        logger.info(
            f"[GET /broadcasts] total={len(res)}, status={status!r}, enabled={enabled!r}, limit={limit}, offset={offset}"
        )
        return res
    except Exception as e:
        logger.error(f"[GET /broadcasts] Ошибка: {e}")
        raise HTTPException(status_code=500, detail="Ошибка при получении списка рассылок")


@router.patch("/{broadcast_id}", response_model=BroadcastRead)
async def patch(broadcast_id: int, patch: BroadcastUpdate, session: AsyncSession = Depends(get_session)):
    try:
        changes = patch.model_dump(exclude_unset=True)
        logger.info(f"[{broadcast_id}] - [PATCH /broadcasts/{broadcast_id}] {changes}")
        obj = await update_broadcast(session, broadcast_id, patch)
        if not obj:
            raise HTTPException(status_code=404, detail="Broadcast not found")
        logger.info(f"[{broadcast_id}] - [PATCH /broadcasts/{broadcast_id}] Ок")
        return obj
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[{broadcast_id}] - [PATCH /broadcasts/{broadcast_id}] Ошибка: {e}")
        raise HTTPException(status_code=500, detail="Ошибка при обновлении рассылки")


@router.delete("/{broadcast_id}", status_code=204)
async def delete(broadcast_id: int, session: AsyncSession = Depends(get_session)):
    try:
        ok = await delete_broadcast(session, broadcast_id)
        if not ok:
            raise HTTPException(status_code=404, detail="Broadcast not found")
        logger.info(f"[{broadcast_id}] - [DELETE /broadcasts/{broadcast_id}] Удалено")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[{broadcast_id}] - [DELETE /broadcasts/{broadcast_id}] Ошибка: {e}")
        raise HTTPException(status_code=500, detail="Ошибка при удалении рассылки")


@router.post("/{broadcast_id}/send_now", response_model=BroadcastRead)
async def send_now_route(broadcast_id: int, session: AsyncSession = Depends(get_session)):
    try:
        logger.info(f"[{broadcast_id}] - [POST /broadcasts/{broadcast_id}/send_now] Немедленная отправка")
        obj = await send_now(session, broadcast_id)
        if not obj:
            raise HTTPException(status_code=404, detail="Broadcast not found")
        logger.info(f"[{broadcast_id}] - [POST /broadcasts/{broadcast_id}/send_now] Ок")
        return obj
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[{broadcast_id}] - [POST /broadcasts/{broadcast_id}/send_now] Ошибка: {e}")
        raise HTTPException(status_code=500, detail="Ошибка при переводе в отправку")


@router.get("/{broadcast_id}/target", response_model=BroadcastTargetRead)
async def read_target(broadcast_id: int, session: AsyncSession = Depends(get_session)):
    try:
        if not await get_broadcast(session, broadcast_id):
            raise HTTPException(status_code=404, detail="Broadcast not found")
        obj = await get_target(session, broadcast_id)
        if not obj:
            raise HTTPException(status_code=404, detail="Target not set")
        out = {
            "id": obj.id,
            "broadcast_id": obj.broadcast_id,
            "type": obj.type,
            "user_ids": obj.user_ids_json,
            "sql": obj.sql_text,
            "kind": obj.kind,
            "created_at": obj.created_at,
        }
        logger.info(f"[{broadcast_id}] - [GET /broadcasts/{broadcast_id}/target] type={obj.type}")
        return out
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[{broadcast_id}] - [GET /broadcasts/{broadcast_id}/target] Ошибка: {e}")
        raise HTTPException(status_code=500, detail="Ошибка при получении таргета")


@router.put("/{broadcast_id}/target", response_model=BroadcastTargetRead, status_code=201)
async def upsert_target(broadcast_id: int, payload: BroadcastTargetCreate, session: AsyncSession = Depends(get_session)):
    try:
        if not await get_broadcast(session, broadcast_id):
            raise HTTPException(status_code=404, detail="Broadcast not found")
        logger.info(f"[{broadcast_id}] - [PUT /broadcasts/{broadcast_id}/target] type={payload.type}")
        obj = await put_target(session, broadcast_id, payload)
        out = {
            "id": obj.id,
            "broadcast_id": obj.broadcast_id,
            "type": obj.type,
            "user_ids": obj.user_ids_json,
            "sql": obj.sql_text,
            "kind": obj.kind,
            "created_at": obj.created_at,
        }
        logger.info(f"[{broadcast_id}] - [PUT /broadcasts/{broadcast_id}/target] Ок")
        return out
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[{broadcast_id}] - [PUT /broadcasts/{broadcast_id}/target] Ошибка: {e}")
        raise HTTPException(status_code=500, detail="Ошибка при сохранении таргета")


@router.get("/{broadcast_id}/deliveries", response_model=List[BroadcastDeliveryRead])
async def deliveries(
    broadcast_id: int,
    status: Optional[str] = Query(default=None),
    limit: int = Query(default=200, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    session: AsyncSession = Depends(get_session),
):
    try:
        if not await get_broadcast(session, broadcast_id):
            raise HTTPException(status_code=404, detail="Broadcast not found")
        items = await list_deliveries(session, broadcast_id, status=status, limit=limit, offset=offset)
        logger.info(
            f"[{broadcast_id}] - [GET /broadcasts/{broadcast_id}/deliveries] total={len(items)}, status={status!r}"
        )
        return items
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[{broadcast_id}] - [GET /broadcasts/{broadcast_id}/deliveries] Ошибка: {e}")
        raise HTTPException(status_code=500, detail="Ошибка при получении доставок")
