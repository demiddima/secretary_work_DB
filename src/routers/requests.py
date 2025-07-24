# src/routers/requests.py

import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from .. import schemas, crud
from ..dependencies import get_session
from ..utils import request_to_dict

router = APIRouter(prefix="/requests", tags=["requests"])
logger = logging.getLogger(__name__)


@router.get("/", response_model=List[schemas.RequestModel], summary="Список заявок")
async def list_requests(session: AsyncSession = Depends(get_session)):
    try:
        result = await crud.get_all_requests(session)
        data = [request_to_dict(r) for r in result]
        # Логируем только важный выход: полный список заявок
        logger.info(f"[GET /requests/] Возвращены заявки: {data}")
        return result
    except Exception as e:
        logger.error(f"[GET /requests/] Ошибка при получении списка заявок: {e}")
        raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера")


@router.get("/{request_id}", response_model=schemas.RequestModel, summary="Получить заявку")
async def get_request(request_id: int, session: AsyncSession = Depends(get_session)):
    try:
        result = await crud.get_request_by_id(session, request_id)
        data = request_to_dict(result)
        # Логируем только важный выход: данные конкретной заявки
        logger.info(f"[{request_id}] - [GET /requests/{request_id}] Заявка: {data}")
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[{request_id}] - [GET /requests/{request_id}] Ошибка при получении заявки: {e}")
        raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера")


@router.post("/upsert", response_model=schemas.RequestModel, summary="Создать или обновить заявку")
async def upsert_request(data: schemas.RequestCreate, session: AsyncSession = Depends(get_session)):
    try:
        # Логируем только важный вход: данные для создания/обновления заявки
        logger.info(f"[POST /requests/upsert] Данные заявки: {data.dict()}")
        return await crud.create_request(session, data)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[POST /requests/upsert] Ошибка при создании или обновлении заявки: {e}")
        raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера")


@router.put("/{request_id}", response_model=schemas.RequestModel, summary="Полное обновление заявки")
async def update_request(
    request_id: int,
    data: schemas.RequestUpdate,
    session: AsyncSession = Depends(get_session)
):
    try:
        # Логируем только важный вход: параметры полного обновления заявки
        logger.info(f"[{request_id}] - [PUT /requests/{request_id}] Данные полного обновления: {data.dict()}")
        return await crud.update_request(session, request_id, data)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[{request_id}] - [PUT /requests/{request_id}] Ошибка при полном обновлении заявки: {e}")
        raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера")


@router.patch("/{request_id}", response_model=schemas.RequestModel, summary="Частичное обновление заявки")
async def patch_request(
    request_id: int,
    data: schemas.RequestPatch,
    session: AsyncSession = Depends(get_session)
):
    try:
        # Логируем только важный вход: параметры частичного обновления заявки
        logger.info(f"[{request_id}] - [PATCH /requests/{request_id}] Данные частичного обновления: {data.dict()}")
        return await crud.patch_request(session, request_id, data)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[{request_id}] - [PATCH /requests/{request_id}] Ошибка при частичном обновлении заявки: {e}")
        raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера")


@router.delete("/{request_id}", status_code=204, summary="Удалить заявку")
async def delete_request(request_id: int, session: AsyncSession = Depends(get_session)):
    try:
        await crud.delete_request(session, request_id)
        # Логируем только важный выход: факт удаления заявки
        logger.info(f"[{request_id}] - [DELETE /requests/{request_id}] Заявка удалена")
        return {"ok": True}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[{request_id}] - [DELETE /requests/{request_id}] Ошибка при удалении заявки: {e}")
        raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера")
