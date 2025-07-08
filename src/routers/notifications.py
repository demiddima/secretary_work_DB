import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from .. import schemas, crud
from ..dependencies import get_session

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.post("/", response_model=schemas.NotificationModel, summary="Создать оповещение")
async def create_notification(
    data: schemas.NotificationCreate,
    session: AsyncSession = Depends(get_async_session)
):
    try:
        return await crud.create_notification(session, data)
    except HTTPException:
        raise
    except Exception:
        logger.exception(f"Не удалось создать оповещение для request_id={data.request_id}")
        raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера")
