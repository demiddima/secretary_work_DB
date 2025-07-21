# src/routers/notifications.py
import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from .. import schemas, crud
from ..dependencies import get_session
from ..utils import notification_to_dict  # Импортируем функцию для преобразования данных

# Настроим логгер
logger = logging.getLogger()

router = APIRouter(prefix="/notifications", tags=["notifications"])

# Получаем список уведомлений
@router.get("/", response_model=List[schemas.NotificationModel], summary="Список уведомлений")
async def list_notifications(
    session: AsyncSession = Depends(get_session)
):
    logger.info("[GET /notifications/] Входящий запрос для получения списка уведомлений")

    try:
        result = await crud.get_all_notifications(session)

        # Логируем исходящий ответ
        logger.info(f"[GET /notifications/] Исходящий ответ: {result}")
        return result
    except Exception:
        logger.exception("Не удалось получить список уведомлений")
        raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера")

# Получаем уведомление по ID
@router.get("/{notification_id}", response_model=schemas.NotificationModel, summary="Получить уведомление")
async def get_notification(
    notification_id: int,
    session: AsyncSession = Depends(get_session)
):
    logger.info(f"[GET /notifications/{notification_id}] Входящий запрос для получения уведомления с id={notification_id}")

    try:
        result = await crud.get_notification_by_id(session, notification_id)

        # Логируем исходящий ответ
        logger.info(f"[GET /notifications/{notification_id}] Исходящий ответ: {notification_to_dict(result)}")
        return result
    except HTTPException:
        raise
    except Exception:
        logger.exception(f"Не удалось получить уведомление с id={notification_id}")
        raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера")

# Создаем или обновляем уведомление
@router.post("/upsert", response_model=schemas.NotificationModel, summary="Создать уведомление")
async def upsert_notification(
    data: schemas.NotificationCreate,
    session: AsyncSession = Depends(get_session)
):
    logger.info(f"[POST /notifications/upsert] Входящий запрос для создания уведомления: {data.dict()}")

    try:
        result = await crud.create_notification(session, data)

        # Логируем исходящий ответ
        logger.info(f"[POST /notifications/upsert] Исходящий ответ: {notification_to_dict(result)}")
        return result
    except HTTPException:
        raise
    except Exception:
        logger.exception(f"Не удалось создать уведомление для request_id={data.request_id}")
        raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера")

# Полное обновление уведомления
@router.put("/{notification_id}", response_model=schemas.NotificationModel, summary="Полное обновление уведомления")
async def update_notification(
    notification_id: int,
    data: schemas.NotificationUpdate,
    session: AsyncSession = Depends(get_session)
):
    logger.info(f"[PUT /notifications/{notification_id}] Входящий запрос для обновления уведомления с id={notification_id}")

    try:
        result = await crud.update_notification(session, notification_id, data)

        # Логируем исходящий ответ
        logger.info(f"[PUT /notifications/{notification_id}] Исходящий ответ: {notification_to_dict(result)}")
        return result
    except HTTPException:
        raise
    except Exception:
        logger.exception(f"Не удалось обновить уведомление с id={notification_id}")
        raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера")

# Частичное обновление уведомления
@router.patch("/{notification_id}", response_model=schemas.NotificationModel, summary="Частичное обновление уведомления")
async def patch_notification(
    notification_id: int,
    data: schemas.NotificationPatch,
    session: AsyncSession = Depends(get_session)
):
    logger.info(f"[PATCH /notifications/{notification_id}] Входящий запрос для частичного обновления уведомления с id={notification_id}")

    try:
        result = await crud.patch_notification(session, notification_id, data)

        # Логируем исходящий ответ
        logger.info(f"[PATCH /notifications/{notification_id}] Исходящий ответ: {notification_to_dict(result)}")
        return result
    except HTTPException:
        raise
    except Exception:
        logger.exception(f"Не удалось частично обновить уведомление с id={notification_id}")
        raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера")

# Удаляем уведомление по ID
@router.delete("/{notification_id}", status_code=204, summary="Удалить уведомление")
async def delete_notification(
    notification_id: int,
    session: AsyncSession = Depends(get_session)
):
    logger.info(f"[DELETE /notifications/{notification_id}] Входящий запрос для удаления уведомления с id={notification_id}")

    try:
        await crud.delete_notification(session, notification_id)

        # Логируем исходящий ответ
        logger.info(f"[DELETE /notifications/{notification_id}] Исходящий ответ: {{'ok': True}}")
        return {"ok": True}
    except HTTPException:
        raise
    except Exception:
        logger.exception(f"Не удалось удалить уведомление с id={notification_id}")
        raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера")
