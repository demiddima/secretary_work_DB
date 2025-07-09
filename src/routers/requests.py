# src/routers/requests.py
# commit: добавлены полные CRUD-эндпоинты для requests

import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from .. import schemas, crud
from ..dependencies import get_session

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/requests", tags=["requests"])

@router.get("/", response_model=List[schemas.RequestModel], summary="Список заявок")
async def list_requests(
    session: AsyncSession = Depends(get_session)
):
    try:
        return await crud.get_all_requests(session)
    except Exception:
        logger.exception("Не удалось получить список заявок")
        raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера")

@router.get("/{request_id}", response_model=schemas.RequestModel, summary="Получить заявку")
async def get_request(
    request_id: int,
    session: AsyncSession = Depends(get_session)
):
    try:
        return await crud.get_request_by_id(session, request_id)
    except HTTPException:
        raise
    except Exception:
        logger.exception(f"Не удалось получить заявку id={request_id}")
        raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера")

@router.post("/upsert", response_model=schemas.RequestModel, summary="Создать или обновить заявку")
async def upsert_request(
    data: schemas.RequestCreate,
    session: AsyncSession = Depends(get_session)
):
    try:
        return await crud.create_request(session, data)
    except HTTPException:
        raise
    except Exception:
        logger.exception(f"Не удалось создать заявку для user_id={data.user_id}, offer_id={data.offer_id}")
        raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера")

@router.put("/{request_id}", response_model=schemas.RequestModel, summary="Полное обновление заявки")
async def update_request(
    request_id: int,
    data: schemas.RequestUpdate,
    session: AsyncSession = Depends(get_session)
):
    try:
        return await crud.update_request(session, request_id, data)
    except HTTPException:
        raise
    except Exception:
        logger.exception(f"Не удалось полностью обновить заявку id={request_id}")
        raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера")

@router.patch("/{request_id}", response_model=schemas.RequestModel, summary="Частичное обновление заявки")
async def patch_request(
    request_id: int,
    data: schemas.RequestPatch,
    session: AsyncSession = Depends(get_session)
):
    try:
        return await crud.patch_request(session, request_id, data)
    except HTTPException:
        raise
    except Exception:
        logger.exception(f"Не удалось частично обновить заявку id={request_id}")
        raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера")

@router.delete("/{request_id}", status_code=204, summary="Удалить заявку")
async def delete_request(
    request_id: int,
    session: AsyncSession = Depends(get_session)
):
    try:
        await crud.delete_request(session, request_id)
    except HTTPException:
        raise
    except Exception:
        logger.exception(f"Не удалось удалить заявку id={request_id}")
        raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера")
