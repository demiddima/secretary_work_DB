# src/routers/reminder_settings.py
import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from .. import schemas, crud
from ..dependencies import get_session
from ..utils import reminder_settings_to_dict  # Импортируем функцию для преобразования данных

# Настроим логгер
logger = logging.getLogger()

router = APIRouter(prefix="/reminder_settings", tags=["reminder_settings"])

# Получить все настройки напоминаний
@router.get("/", response_model=List[schemas.ReminderSettingsModel], summary="Список настроек напоминаний")
async def list_reminder_settings(
    session: AsyncSession = Depends(get_session)
):
    logger.info("[GET /reminder_settings/] Входящий запрос для получения списка настроек напоминаний")
    
    try:
        result = await crud.get_all_reminder_settings(session)
        logger.info(f"[GET /reminder_settings/] Исходящий ответ: {result}")
        return result
    except Exception:
        logger.exception("Не удалось получить список настроек напоминаний")
        raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера")

# Получить настройку напоминания по ID
@router.get("/{setting_id}", response_model=schemas.ReminderSettingsModel, summary="Получить настройку напоминания")
async def get_reminder_setting(
    setting_id: int,
    session: AsyncSession = Depends(get_session)
):
    logger.info(f"[GET /reminder_settings/{setting_id}] Входящий запрос для получения настройки с id={setting_id}")

    try:
        result = await crud.get_reminder_setting_by_id(session, setting_id)
        logger.info(f"[GET /reminder_settings/{setting_id}] Исходящий ответ: {reminder_settings_to_dict(result)}")
        return result
    except HTTPException:
        raise
    except Exception:
        logger.exception(f"Не удалось получить настройку напоминания с id={setting_id}")
        raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера")

# Создать или обновить настройку напоминания
@router.post("/upsert", response_model=schemas.ReminderSettingsModel, summary="Создать или обновить настройку напоминания")
async def upsert_reminder_setting(
    data: schemas.ReminderSettingsCreate,
    session: AsyncSession = Depends(get_session)
):
    logger.info(f"[POST /reminder_settings/upsert] Входящий запрос для создания или обновления настройки: {data.dict()}")

    try:
        result = await crud.create_reminder_setting(session, data)
        logger.info(f"[POST /reminder_settings/upsert] Исходящий ответ: {reminder_settings_to_dict(result)}")
        return result
    except Exception as e:
        logger.exception(f"Не удалось создать или обновить настройку напоминания для request_id={data.request_id}")
        raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера")

# Полное обновление настройки напоминания
@router.put("/{setting_id}", response_model=schemas.ReminderSettingsModel, summary="Полное обновление настройки напоминания")
async def update_reminder_setting(
    setting_id: int,
    data: schemas.ReminderSettingsUpdate,
    session: AsyncSession = Depends(get_session)
):
    logger.info(f"[PUT /reminder_settings/{setting_id}] Входящий запрос для полного обновления настройки с id={setting_id}")

    try:
        result = await crud.update_reminder_setting(session, setting_id, data)
        logger.info(f"[PUT /reminder_settings/{setting_id}] Исходящий ответ: {reminder_settings_to_dict(result)}")
        return result
    except Exception:
        logger.exception(f"Не удалось полностью обновить настройку с id={setting_id}")
        raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера")

# Частичное обновление настройки напоминания
@router.patch("/{setting_id}", response_model=schemas.ReminderSettingsModel, summary="Частичное обновление настройки напоминания")
async def patch_reminder_setting(
    setting_id: int,
    data: schemas.ReminderSettingsPatch,
    session: AsyncSession = Depends(get_session)
):
    logger.info(f"[PATCH /reminder_settings/{setting_id}] Входящий запрос для частичного обновления настройки с id={setting_id}")

    try:
        result = await crud.patch_reminder_setting(session, setting_id, data)
        logger.info(f"[PATCH /reminder_settings/{setting_id}] Исходящий ответ: {reminder_settings_to_dict(result)}")
        return result
    except Exception:
        logger.exception(f"Не удалось частично обновить настройку с id={setting_id}")
        raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера")

# Удалить настройку напоминания по ID
@router.delete("/{setting_id}", status_code=204, summary="Удалить настройку напоминания")
async def delete_reminder_setting(
    setting_id: int,
    session: AsyncSession = Depends(get_session)
):
    logger.info(f"[DELETE /reminder_settings/{setting_id}] Входящий запрос для удаления настройки с id={setting_id}")

    try:
        await crud.delete_reminder_setting(session, setting_id)
        logger.info(f"[DELETE /reminder_settings/{setting_id}] Исходящий ответ: {{'ok': True}}")
        return {"ok": True}
    except Exception:
        logger.exception(f"Не удалось удалить настройку напоминания с id={setting_id}")
        raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера")
