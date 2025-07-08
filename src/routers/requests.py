import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from .. import schemas, crud
from ..dependencies import get_session

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/requests", tags=["requests"])


@router.post("/", response_model=schemas.RequestModel, summary="Создать заявку")
async def create_request(
    data: schemas.RequestCreate,
    session: AsyncSession = Depends(get_async_session)
):
    try:
        return await crud.create_request(session, data)
    except HTTPException:
        # пробрасываем 404 и другие HTTPException как есть
        raise
    except Exception:
        logger.exception(
            f"Не удалось создать заявку: user_id={data.user_id}, offer_name={data.offer_name}"
        )
        raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера")


@router.patch("/{request_id}/status/", response_model=schemas.RequestModel, summary="Обновить статус заявки")
async def set_status(
    request_id: int,
    status: schemas.RequestStatusUpdate,
    session: AsyncSession = Depends(get_async_session)
):
    try:
        return await crud.update_request_status(session, request_id, status.is_completed)
    except HTTPException:
        raise
    except Exception:
        logger.exception(f"Не удалось обновить статус заявки id={request_id}")
        raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера")
