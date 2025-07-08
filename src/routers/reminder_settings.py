import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from .. import schemas, crud
from ..dependencies import get_session

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/reminder_settings", tags=["reminder_settings"])


@router.post("/", response_model=schemas.ReminderSettingsModel, summary="Создать настройку напоминания")
async def create_setting(
    data: schemas.ReminderSettingsCreate,
    session: AsyncSession = Depends(get_async_session)
):
    try:
        return await crud.create_reminder_setting(session, data)
    except HTTPException:
        raise
    except Exception:
        logger.exception(f"Не удалось создать настройку напоминания для request_id={data.request_id}")
        raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера")
