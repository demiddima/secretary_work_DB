# src/routers/requests.py
import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from .. import schemas, crud
from ..dependencies import get_session
from ..utils import request_to_dict  # Импортируем функцию для преобразования данных

# Настроим логгер
logger = logging.getLogger()

router = APIRouter(prefix="/requests", tags=["requests"])

# Список заявок
@router.get("/", response_model=List[schemas.RequestModel], summary="Список заявок")
async def list_requests(
    session: AsyncSession = Depends(get_session)
):
    logger.info("[GET /requests/] Входящий запрос для получения списка заявок")

    try:
        result = await crud.get_all_requests(session)
        logger.info(f"[GET /requests/] Исходящий ответ: {result}")
        return result
    except Exception:
        logger.exception("Не удалось получить список заявок")
        raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера")

# Получить заявку по ID
@router.get("/{request_id}", response_model=schemas.RequestModel, summary="Получить заявку")
async def get_request(
    request_id: int,
    session: AsyncSession = Depends(get_session)
):
    logger.info(f"[GET /requests/{request_id}] Входящий запрос для получения заявки с id={request_id}")

    try:
        result = await crud.get_request_by_id(session, request_id)
        logger.info(f"[GET /requests/{request_id}] Исходящий ответ: {request_to_dict(result)}")
        return result
    except HTTPException:
        raise
    except Exception:
        logger.exception(f"Не удалось получить заявку с id={request_id}")
        raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера")

# Создать или обновить заявку
@router.post("/upsert", response_model=schemas.RequestModel, summary="Создать или обновить заявку")
async def upsert_request(
    data: schemas.RequestCreate,
    session: AsyncSession = Depends(get_session)
):
    logger.info(f"[POST /requests/upsert] Входящий запрос для создания или обновления заявки: {data.dict()}")

    try:
        result = await crud.create_request(session, data)
        logger.info(f"[POST /requests/upsert] Исходящий ответ: {request_to_dict(result)}")
        return result
    except HTTPException:
        raise
    except Exception:
        logger.exception(f"Не удалось создать заявку для user_id={data.user_id}, offer_id={data.offer_id}")
        raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера")

# Полное обновление заявки
@router.put("/{request_id}", response_model=schemas.RequestModel, summary="Полное обновление заявки")
async def update_request(
    request_id: int,
    data: schemas.RequestUpdate,
    session: AsyncSession = Depends(get_session)
):
    logger.info(f"[PUT /requests/{request_id}] Входящий запрос для полного обновления заявки с id={request_id}")

    try:
        result = await crud.update_request(session, request_id, data)
        logger.info(f"[PUT /requests/{request_id}] Исходящий ответ: {request_to_dict(result)}")
        return result
    except HTTPException:
        raise
    except Exception:
        logger.exception(f"Не удалось полностью обновить заявку с id={request_id}")
        raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера")

# Частичное обновление заявки
@router.patch("/{request_id}", response_model=schemas.RequestModel, summary="Частичное обновление заявки")
async def patch_request(
    request_id: int,
    data: schemas.RequestPatch,
    session: AsyncSession = Depends(get_session)
):
    logger.info(f"[PATCH /requests/{request_id}] Входящий запрос для частичного обновления заявки с id={request_id}")

    try:
        result = await crud.patch_request(session, request_id, data)
        logger.info(f"[PATCH /requests/{request_id}] Исходящий ответ: {request_to_dict(result)}")
        return result
    except HTTPException:
        raise
    except Exception:
        logger.exception(f"Не удалось частично обновить заявку с id={request_id}")
        raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера")

# Удалить заявку по ID
@router.delete("/{request_id}", status_code=204, summary="Удалить заявку")
async def delete_request(
    request_id: int,
    session: AsyncSession = Depends(get_session)
):
    logger.info(f"[DELETE /requests/{request_id}] Входящий запрос для удаления заявки с id={request_id}")

    try:
        await crud.delete_request(session, request_id)
        logger.info(f"[DELETE /requests/{request_id}] Исходящий ответ: {{'ok': True}}")
        return {"ok": True}
    except HTTPException:
        raise
    except Exception:
        logger.exception(f"Не удалось удалить заявку с id={request_id}")
        raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера")
