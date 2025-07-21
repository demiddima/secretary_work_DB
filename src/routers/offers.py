# src/routers/offers.py
import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from .. import schemas, crud
from ..dependencies import get_session
from ..utils import offer_to_dict  # Импортируем функцию для преобразования данных

# Настроим логгер
logger = logging.getLogger()

router = APIRouter(prefix="/offers", tags=["offers"])

# Список всех офферов
@router.get("/", response_model=List[schemas.OfferModel], summary="Список офферов")
async def list_offers(
    session: AsyncSession = Depends(get_session)
):
    logger.info("[GET /offers/] Входящий запрос для получения списка офферов")
    
    try:
        result = await crud.get_all_offers(session)

        # Логируем исходящий ответ
        logger.info(f"[GET /offers/] Исходящий ответ: {result}")
        return result
    except Exception:
        logger.exception("Не удалось получить список офферов")
        raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера")

# Получить оффер по ID
@router.get("/{offer_id}", response_model=schemas.OfferModel, summary="Получить оффер")
async def get_offer(
    offer_id: int,
    session: AsyncSession = Depends(get_session)
):
    logger.info(f"[GET /offers/{offer_id}] Входящий запрос для получения оффера с id={offer_id}")

    try:
        result = await crud.get_offer_by_id(session, offer_id)

        # Логируем исходящий ответ
        logger.info(f"[GET /offers/{offer_id}] Исходящий ответ: {offer_to_dict(result)}")
        return result
    except HTTPException:
        raise
    except Exception:
        logger.exception(f"Не удалось получить оффер с id={offer_id}")
        raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера")

# Создать или обновить оффер
@router.post("/upsert", response_model=schemas.OfferModel, summary="Создать или обновить оффер")
async def upsert_offer(
    data: schemas.OfferCreate,
    session: AsyncSession = Depends(get_session)
):
    logger.info(f"[POST /offers/upsert] Входящий запрос для создания или обновления оффера: {data.dict()}")

    try:
        result = await crud.create_offer(session, data)

        # Логируем исходящий ответ
        logger.info(f"[POST /offers/upsert] Исходящий ответ: {offer_to_dict(result)}")
        return result
    except HTTPException:
        raise
    except Exception:
        logger.exception(f"Не удалось создать или обновить оффер с name={data.name}")
        raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера")

# Полное обновление оффера
@router.put("/{offer_id}", response_model=schemas.OfferModel, summary="Полное обновление оффера")
async def update_offer(
    offer_id: int,
    data: schemas.OfferUpdate,
    session: AsyncSession = Depends(get_session)
):
    logger.info(f"[PUT /offers/{offer_id}] Входящий запрос для полного обновления оффера с id={offer_id}")

    try:
        result = await crud.update_offer(session, offer_id, data)

        # Логируем исходящий ответ
        logger.info(f"[PUT /offers/{offer_id}] Исходящий ответ: {offer_to_dict(result)}")
        return result
    except HTTPException:
        raise
    except Exception:
        logger.exception(f"Не удалось полностью обновить оффер с id={offer_id}")
        raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера")

# Частичное обновление оффера
@router.patch("/{offer_id}", response_model=schemas.OfferModel, summary="Частичное обновление оффера")
async def patch_offer(
    offer_id: int,
    data: schemas.OfferPatch,
    session: AsyncSession = Depends(get_session)
):
    logger.info(f"[PATCH /offers/{offer_id}] Входящий запрос для частичного обновления оффера с id={offer_id}")

    try:
        result = await crud.patch_offer(session, offer_id, data)

        # Логируем исходящий ответ
        logger.info(f"[PATCH /offers/{offer_id}] Исходящий ответ: {offer_to_dict(result)}")
        return result
    except HTTPException:
        raise
    except Exception:
        logger.exception(f"Не удалось частично обновить оффер с id={offer_id}")
        raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера")

# Удалить оффер по ID
@router.delete("/{offer_id}", status_code=204, summary="Удалить оффер")
async def delete_offer(
    offer_id: int,
    session: AsyncSession = Depends(get_session)
):
    logger.info(f"[DELETE /offers/{offer_id}] Входящий запрос для удаления оффера с id={offer_id}")

    try:
        await crud.delete_offer(session, offer_id)

        # Логируем исходящий ответ
        logger.info(f"[DELETE /offers/{offer_id}] Исходящий ответ: {{'ok': True}}")
        return {"ok": True}
    except HTTPException:
        raise
    except Exception:
        logger.exception(f"Не удалось удалить оффер с id={offer_id}")
        raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера")
