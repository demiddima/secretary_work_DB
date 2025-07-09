# src/routers/notifications.py
# commit: добавлены полные CRUD-эндпоинты для notifications

import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from .. import schemas, crud
from ..dependencies import get_session

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/notifications", tags=["notifications"])

@router.get("/", response_model=List[schemas.NotificationModel], summary="Список уведомлений")
async def list_notifications(
    session: AsyncSession = Depends(get_session)
):
    try:
        return await crud.get_all_notifications(session)
    except Exception:
        logger.exception("Не удалось получить список уведомлений")
        raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера")

@router.get("/{notification_id}", response_model=schemas.NotificationModel, summary="Получить уведомление")
async def get_notification(
    notification_id: int,
    session: AsyncSession = Depends(get_session)
):
    try:
        return await crud.get_notification_by_id(session, notification_id)
    except HTTPException:
        raise
    except Exception:
        logger.exception(f"Не удалось получить уведомление id={notification_id}")
        raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера")

@router.post("/upsert", response_model=schemas.NotificationModel, summary="Создать уведомление")
async def upsert_notification(
    data: schemas.NotificationCreate,
    session: AsyncSession = Depends(get_session)
):
    try:
        return await crud.create_notification(session, data)
    except HTTPException:
        raise
    except Exception:
        logger.exception(f"Не удалось создать уведомление для request_id={data.request_id}")
        raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера")

@router.put("/{notification_id}", response_model=schemas.NotificationModel, summary="Полное обновление уведомления")
async def update_notification(
    notification_id: int,
    data: schemas.NotificationUpdate,
    session: AsyncSession = Depends(get_session)
):
    try:
        return await crud.update_notification(session, notification_id, data)
    except HTTPException:
        raise
    except Exception:
        logger.exception(f"Не удалось полностью обновить уведомление id={notification_id}")
        raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера")

@router.patch("/{notification_id}", response_model=schemas.NotificationModel, summary="Частичное обновление уведомления")
async def patch_notification(
    notification_id: int,
    data: schemas.NotificationPatch,
    session: AsyncSession = Depends(get_session)
):
    try:
        return await crud.patch_notification(session, notification_id, data)
    except HTTPException:
        raise
    except Exception:
        logger.exception(f"Не удалось частично обновить уведомление id={notification_id}")
        raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера")

@router.delete("/{notification_id}", status_code=204, summary="Удалить уведомление")
async def delete_notification(
    notification_id: int,
    session: AsyncSession = Depends(get_session)
):
    try:
        await crud.delete_notification(session, notification_id)
    except HTTPException:
        raise
    except Exception:
        logger.exception(f"Не удалось удалить уведомление id={notification_id}")
        raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера")
