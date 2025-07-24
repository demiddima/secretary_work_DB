# src/routers/offers.py

import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from .. import schemas, crud
from ..dependencies import get_session
from ..utils import offer_to_dict

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/offers", tags=["offers"])


@router.get("/", response_model=List[schemas.OfferModel], summary="Список офферов")
async def list_offers(session: AsyncSession = Depends(get_session)):
    try:
        result = await crud.get_all_offers(session)
        data = [offer_to_dict(o) for o in result]
        # Логируем только важный выход: список офферов
        logger.info(f"[GET /offers/] Список офферов: {data}")
        return result
    except Exception as e:
        logger.error(f"[GET /offers/] Ошибка при получении списка офферов: {e}")
        raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера")


@router.get("/{offer_id}", response_model=schemas.OfferModel, summary="Получить оффер")
async def get_offer(offer_id: int, session: AsyncSession = Depends(get_session)):
    try:
        result = await crud.get_offer_by_id(session, offer_id)
        # Логируем только важный выход: данные оффера
        logger.info(f"[GET /offers/{offer_id}] Оффер: {offer_to_dict(result)}")
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[GET /offers/{offer_id}] Ошибка при получении оффера: {e}")
        raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера")


@router.post("/upsert", response_model=schemas.OfferModel, summary="Создать или обновить оффер")
async def upsert_offer(data: schemas.OfferCreate, session: AsyncSession = Depends(get_session)):
    try:
        # Логируем только важный вход: параметры оффера для создания/обновления
        logger.info(f"[POST /offers/upsert] Данные оффера: {data.dict()}")
        return await crud.create_offer(session, data)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[POST /offers/upsert] Ошибка при создании или обновлении оффера: {e}")
        raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера")


@router.put("/{offer_id}", response_model=schemas.OfferModel, summary="Полное обновление оффера")
async def update_offer(offer_id: int, data: schemas.OfferUpdate, session: AsyncSession = Depends(get_session)):
    try:
        # Логируем только важный вход: параметры полного обновления
        logger.info(f"[PUT /offers/{offer_id}] Данные для полного обновления: {data.dict()}")
        return await crud.update_offer(session, offer_id, data)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[PUT /offers/{offer_id}] Ошибка при полном обновлении оффера: {e}")
        raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера")


@router.patch("/{offer_id}", response_model=schemas.OfferModel, summary="Частичное обновление оффера")
async def patch_offer(offer_id: int, data: schemas.OfferPatch, session: AsyncSession = Depends(get_session)):
    try:
        # Логируем только важный вход: параметры частичного обновления
        logger.info(f"[PATCH /offers/{offer_id}] Данные для частичного обновления: {data.dict()}")
        return await crud.patch_offer(session, offer_id, data)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[PATCH /offers/{offer_id}] Ошибка при частичном обновлении оффера: {e}")
        raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера")


@router.delete("/{offer_id}", status_code=204, summary="Удалить оффер")
async def delete_offer(offer_id: int, session: AsyncSession = Depends(get_session)):
    try:
        await crud.delete_offer(session, offer_id)
        # Логируем только важный выход: факт удаления оффера
        logger.info(f"[DELETE /offers/{offer_id}] Оффер удалён")
        return {"ok": True}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[DELETE /offers/{offer_id}] Ошибка при удалении оффера: {e}")
        raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера")
