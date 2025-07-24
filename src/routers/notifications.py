# src/routers/notifications.py

import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from .. import schemas, crud
from ..dependencies import get_session
from ..utils import notification_to_dict

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("/", response_model=List[schemas.NotificationModel], summary="Список уведомлений")
async def list_notifications(session: AsyncSession = Depends(get_session)):
    try:
        # Получаем все уведомления
        notifications = await crud.get_all_notifications(session)
        # Логируем только важный выход: список уведомлений
        data = [notification_to_dict(n) for n in notifications]
        logger.info(f"[GET /notifications/] Список уведомлений: {data}")
        return data
    except Exception as e:
        logger.error(f"[GET /notifications/] Ошибка при получении списка уведомлений: {e}")
        raise HTTPException(status_code=500, detail="Ошибка при получении списка уведомлений")


@router.get("/{notification_id}", response_model=schemas.NotificationModel, summary="Получить уведомление")
async def get_notification(
    notification_id: int,
    session: AsyncSession = Depends(get_session)
):
    try:
        # Читаем уведомление
        notification = await crud.get_notification_by_id(session, notification_id)
        # Логируем только важный выход: данные уведомления
        data = notification_to_dict(notification)
        logger.info(f"[GET /notifications/{notification_id}] Уведомление: {data}")
        return data
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[GET /notifications/{notification_id}] Ошибка при получении уведомления: {e}")
        raise HTTPException(status_code=500, detail="Ошибка при получении уведомления")


@router.post("/upsert", response_model=schemas.NotificationModel, summary="Создать уведомление")
async def upsert_notification(
    data: schemas.NotificationCreate,
    session: AsyncSession = Depends(get_session)
):
    try:
        # Логируем только важный вход: параметры создания
        logger.info(f"[POST /notifications/upsert] Создание уведомления: {data.dict()}")
        return await crud.create_notification(session, data)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[POST /notifications/upsert] Ошибка при создании уведомления: {e}")
        raise HTTPException(status_code=500, detail="Ошибка при создании уведомления")


@router.put("/{notification_id}", response_model=schemas.NotificationModel, summary="Полное обновление уведомления")
async def update_notification(
    notification_id: int,
    data: schemas.NotificationUpdate,
    session: AsyncSession = Depends(get_session)
):
    try:
        # Логируем только важный вход: параметры обновления
        logger.info(f"[PUT /notifications/{notification_id}] Обновление уведомления: {data.dict()}")
        return await crud.update_notification(session, notification_id, data)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[PUT /notifications/{notification_id}] Ошибка при обновлении уведомления: {e}")
        raise HTTPException(status_code=500, detail="Ошибка при обновлении уведомления")


@router.patch("/{notification_id}", response_model=schemas.NotificationModel, summary="Частичное обновление уведомления")
async def patch_notification(
    notification_id: int,
    data: schemas.NotificationPatch,
    session: AsyncSession = Depends(get_session)
):
    try:
        # Логируем только важный вход: параметры частичного обновления
        logger.info(f"[PATCH /notifications/{notification_id}] Частичное обновление: {data.dict()}")
        return await crud.patch_notification(session, notification_id, data)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[PATCH /notifications/{notification_id}] Ошибка при частичном обновлении уведомления: {e}")
        raise HTTPException(status_code=500, detail="Ошибка при частичном обновлении уведомления")


@router.delete("/{notification_id}", status_code=204, summary="Удалить уведомление")
async def delete_notification(
    notification_id: int,
    session: AsyncSession = Depends(get_session)
):
    try:
        await crud.delete_notification(session, notification_id)
        # Логируем только важный выход: факт удаления уведомления
        logger.info(f"[DELETE /notifications/{notification_id}] Уведомление удалено")
        return {"ok": True}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[DELETE /notifications/{notification_id}] Ошибка при удалении уведомления: {e}")
        raise HTTPException(status_code=500, detail="Ошибка при удалении уведомления")
