# src/routers/reminder_settings.py
# commit: добавлены полные CRUD-эндпоинты для reminder_settings

import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from .. import schemas, crud
from ..dependencies import get_session

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/reminder_settings", tags=["reminder_settings"])

@router.get("/", response_model=List[schemas.ReminderSettingsModel], summary="Список настроек напоминаний")
async def list_reminder_settings(
    session: AsyncSession = Depends(get_session)
):
    try:
        return await crud.get_all_reminder_settings(session)
    except Exception:
        logger.exception("Не удалось получить список настроек напоминаний")
        raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера")

@router.get("/{setting_id}", response_model=schemas.ReminderSettingsModel, summary="Получить настройку напоминания")
async def get_reminder_setting(
    setting_id: int,
    session: AsyncSession = Depends(get_session)
):
    try:
        return await crud.get_reminder_setting_by_id(session, setting_id)
    except HTTPException:
        raise
    except Exception:
        logger.exception(f"Не удалось получить настройку напоминания id={setting_id}")
        raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера")

@router.post("/upsert", response_model=schemas.ReminderSettingsModel, summary="Создать или обновить настройку напоминания")
async def upsert_reminder_setting(
    data: schemas.ReminderSettingsCreate,
    session: AsyncSession = Depends(get_session)
):
    try:
        # Попытаться создать или обновить настройку напоминания
        reminder = await crud.create_reminder_setting(session, data)
        await session.commit()
        return reminder
    except Exception as e:
        logger.exception(f"Не удалось создать/обновить настройку напоминания для request_id={data.request_id}")
        raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера")

@router.put("/{setting_id}", response_model=schemas.ReminderSettingsModel, summary="Полное обновление настройки напоминания")
async def update_reminder_setting(
    setting_id: int,
    data: schemas.ReminderSettingsUpdate,
    session: AsyncSession = Depends(get_session)
):
    try:
        return await crud.update_reminder_setting(session, setting_id, data)
    except HTTPException:
        raise
    except Exception:
        logger.exception(f"Не удалось полностью обновить настройку напоминания id={setting_id}")
        raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера")

@router.patch("/{setting_id}", response_model=schemas.ReminderSettingsModel, summary="Частичное обновление настройки напоминания")
async def patch_reminder_setting(
    setting_id: int,
    data: schemas.ReminderSettingsPatch,
    session: AsyncSession = Depends(get_session)
):
    try:
        return await crud.patch_reminder_setting(session, setting_id, data)
    except HTTPException:
        raise
    except Exception:
        logger.exception(f"Не удалось частично обновить настройку напоминания id={setting_id}")
        raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера")

@router.delete("/{setting_id}", status_code=204, summary="Удалить настройку напоминания")
async def delete_reminder_setting(
    setting_id: int,
    session: AsyncSession = Depends(get_session)
):
    try:
        await crud.delete_reminder_setting(session, setting_id)
    except HTTPException:
        raise
    except Exception:
        logger.exception(f"Не удалось удалить настройку напоминания id={setting_id}")
        raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера")
