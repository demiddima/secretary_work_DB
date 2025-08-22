# src/routers/broadcasts.py
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.dependencies import get_session

from src.schemas import (
    BroadcastCreate,
    BroadcastUpdate,
    BroadcastRead,
    BroadcastTargetCreate,
    BroadcastTargetRead,
    BroadcastMediaPut,
    BroadcastMediaReadItem,
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
    get_media,
    put_media,
    list_deliveries,
)

router = APIRouter(prefix="/broadcasts", tags=["broadcasts"])

@router.post("", response_model=BroadcastRead, status_code=201)
async def create(payload: BroadcastCreate, session: AsyncSession = Depends(get_session)):
    obj = await create_broadcast(session, payload)
    return obj

@router.get("/{broadcast_id}", response_model=BroadcastRead)
async def get(broadcast_id: int, session: AsyncSession = Depends(get_session)):
    obj = await get_broadcast(session, broadcast_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Broadcast not found")
    return obj

@router.get("", response_model=List[BroadcastRead])
async def list_(
    session: AsyncSession = Depends(get_session),
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
):
    return await list_broadcasts(session, limit=limit, offset=offset)

@router.patch("/{broadcast_id}", response_model=BroadcastRead)
async def patch(broadcast_id: int, patch: BroadcastUpdate, session: AsyncSession = Depends(get_session)):
    obj = await update_broadcast(session, broadcast_id, patch)
    if not obj:
        raise HTTPException(status_code=404, detail="Broadcast not found")
    return obj

@router.delete("/{broadcast_id}", status_code=204)
async def delete(broadcast_id: int, session: AsyncSession = Depends(get_session)):
    ok = await delete_broadcast(session, broadcast_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Broadcast not found")
    return

@router.post("/{broadcast_id}/send_now", response_model=BroadcastRead)
async def send_now_route(broadcast_id: int, session: AsyncSession = Depends(get_session)):
    obj = await send_now(session, broadcast_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Broadcast not found")
    return obj

@router.get("/{broadcast_id}/target", response_model=BroadcastTargetRead)
async def read_target(broadcast_id: int, session: AsyncSession = Depends(get_session)):
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
    return out

@router.put("/{broadcast_id}/target", response_model=BroadcastTargetRead, status_code=201)
async def upsert_target(broadcast_id: int, payload: BroadcastTargetCreate, session: AsyncSession = Depends(get_session)):
    if not await get_broadcast(session, broadcast_id):
        raise HTTPException(status_code=404, detail="Broadcast not found")
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
    return out

@router.get("/{broadcast_id}/media", response_model=List[BroadcastMediaReadItem])
async def read_media(broadcast_id: int, session: AsyncSession = Depends(get_session)):
    if not await get_broadcast(session, broadcast_id):
        raise HTTPException(status_code=404, detail="Broadcast not found")
    items = await get_media(session, broadcast_id)
    return items

@router.put("/{broadcast_id}/media", response_model=List[BroadcastMediaReadItem], status_code=201)
async def replace_media(broadcast_id: int, payload: BroadcastMediaPut, session: AsyncSession = Depends(get_session)):
    if not await get_broadcast(session, broadcast_id):
        raise HTTPException(status_code=404, detail="Broadcast not found")
    items = await put_media(session, broadcast_id, payload)
    return items

@router.get("/{broadcast_id}/deliveries", response_model=List[BroadcastDeliveryRead])
async def deliveries(
    broadcast_id: int,
    status: Optional[str] = Query(default=None),
    limit: int = Query(default=200, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    session: AsyncSession = Depends(get_session),
):
    if not await get_broadcast(session, broadcast_id):
        raise HTTPException(status_code=404, detail="Broadcast not found")
    return await list_deliveries(session, broadcast_id, status=status, limit=limit, offset=offset)
