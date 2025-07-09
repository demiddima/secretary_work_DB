# src/routers/offers.py
# commit: добавлен полный CRUD-эндпоинты для offers

import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from .. import schemas, crud
from ..dependencies import get_session

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/offers", tags=["offers"])

@router.get("/", response_model=List[schemas.OfferModel], summary="Список офферов")
async def list_offers(
    session: AsyncSession = Depends(get_session)
):
    try:
        return await crud.get_all_offers(session)
    except Exception:
        logger.exception("Не удалось получить список офферов")
        raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера")

@router.get("/{offer_id}", response_model=schemas.OfferModel, summary="Получить оффер")
async def get_offer(
    offer_id: int,
    session: AsyncSession = Depends(get_session)
):
    try:
        return await crud.get_offer_by_id(session, offer_id)
    except HTTPException:
        raise
    except Exception:
        logger.exception(f"Не удалось получить оффер id={offer_id}")
        raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера")

@router.post("/upsert", response_model=schemas.OfferModel, summary="Создать или обновить оффер")
async def upsert_offer(
    data: schemas.OfferCreate,
    session: AsyncSession = Depends(get_session)
):
    try:
        return await crud.create_offer(session, data)
    except HTTPException:
        raise
    except Exception:
        logger.exception(f"Не удалось создать оффер name={data.name}")
        raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера")

@router.put("/{offer_id}", response_model=schemas.OfferModel, summary="Полное обновление оффера")
async def update_offer(
    offer_id: int,
    data: schemas.OfferUpdate,
    session: AsyncSession = Depends(get_session)
):
    try:
        return await crud.update_offer(session, offer_id, data)
    except HTTPException:
        raise
    except Exception:
        logger.exception(f"Не удалось полностью обновить оффер id={offer_id}")
        raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера")

@router.patch("/{offer_id}", response_model=schemas.OfferModel, summary="Частичное обновление оффера")
async def patch_offer(
    offer_id: int,
    data: schemas.OfferPatch,
    session: AsyncSession = Depends(get_session)
):
    try:
        return await crud.patch_offer(session, offer_id, data)
    except HTTPException:
        raise
    except Exception:
        logger.exception(f"Не удалось частично обновить оффер id={offer_id}")
        raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера")

@router.delete("/{offer_id}", status_code=204, summary="Удалить оффер")
async def delete_offer(
    offer_id: int,
    session: AsyncSession = Depends(get_session)
):
    try:
        await crud.delete_offer(session, offer_id)
    except HTTPException:
        raise
    except Exception:
        logger.exception(f"Не удалось удалить оффер id={offer_id}")
        raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера")
