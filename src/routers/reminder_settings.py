# src/routers/reminder_settings.py

import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from .. import schemas, crud
from ..dependencies import get_session
from ..utils import reminder_settings_to_dict

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/reminder_settings", tags=["reminder_settings"])


@router.get("/", response_model=List[schemas.ReminderSettingsModel], summary="Список настроек напоминаний")
async def list_reminder_settings(session: AsyncSession = Depends(get_session)):
    try:
        result = await crud.get_all_reminder_settings(session)
        # Логируем только важный выход: полный список настроек
        data = [reminder_settings_to_dict(r) for r in result]
        logger.info(f"[GET /reminder_settings/] Возвращены настройки: {data}")
        return result
    except Exception as e:
        logger.error(f"[GET /reminder_settings/] Ошибка при получении списка настроек: {e}")
        raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера")


@router.get("/{setting_id}", response_model=schemas.ReminderSettingsModel, summary="Получить настройку напоминания")
async def get_reminder_setting(setting_id: int, session: AsyncSession = Depends(get_session)):
    try:
        result = await crud.get_reminder_setting_by_id(session, setting_id)
        # Логируем только важный выход: данные конкретной настройки
        data = reminder_settings_to_dict(result)
        logger.info(f"[GET /reminder_settings/{setting_id}] Настройка: {data}")
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[GET /reminder_settings/{setting_id}] Ошибка при получении настройки: {e}")
        raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера")


@router.post("/upsert", response_model=schemas.ReminderSettingsModel, summary="Создать или обновить настройку напоминания")
async def upsert_reminder_setting(
    data: schemas.ReminderSettingsCreate,
    session: AsyncSession = Depends(get_session)
):
    try:
        # Логируем только важный вход: параметры создания или обновления
        logger.info(f"[POST /reminder_settings/upsert] Параметры: {data.dict()}")
        result = await crud.create_reminder_setting(session, data)
        return result
    except Exception as e:
        logger.error(f"[POST /reminder_settings/upsert] Ошибка при сохранении настройки: {e}")
        raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера")


@router.put("/{setting_id}", response_model=schemas.ReminderSettingsModel, summary="Полное обновление настройки напоминания")
async def update_reminder_setting(
    setting_id: int,
    data: schemas.ReminderSettingsUpdate,
    session: AsyncSession = Depends(get_session)
):
    try:
        # Логируем только важный вход: параметры обновления
        logger.info(f"[PUT /reminder_settings/{setting_id}] Параметры обновления: {data.dict()}")
        result = await crud.update_reminder_setting(session, setting_id, data)
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[PUT /reminder_settings/{setting_id}] Ошибка при полном обновлении: {e}")
        raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера")


@router.patch("/{setting_id}", response_model=schemas.ReminderSettingsModel, summary="Частичное обновление настройки напоминания")
async def patch_reminder_setting(
    setting_id: int,
    data: schemas.ReminderSettingsPatch,
    session: AsyncSession = Depends(get_session)
):
    try:
        # Логируем только важный вход: параметры частичного обновления
        logger.info(f"[PATCH /reminder_settings/{setting_id}] Параметры патча: {data.dict()}")
        result = await crud.patch_reminder_setting(session, setting_id, data)
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[PATCH /reminder_settings/{setting_id}] Ошибка при частичном обновлении: {e}")
        raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера")


@router.delete("/{setting_id}", status_code=204, summary="Удалить настройку напоминания")
async def delete_reminder_setting(setting_id: int, session: AsyncSession = Depends(get_session)):
    try:
        await crud.delete_reminder_setting(session, setting_id)
        # Логируем только важный выход: факт удаления настройки
        logger.info(f"[DELETE /reminder_settings/{setting_id}] Настройка удалена")
        return {"ok": True}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[DELETE /reminder_settings/{setting_id}] Ошибка при удалении настройки: {e}")
        raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера")
