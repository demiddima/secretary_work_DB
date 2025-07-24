# src/routers/algorithm.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from src.schemas import AlgorithmProgressModel
from src.database import get_session
from src import crud
from src.utils import algorithm_progress_to_dict

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/algo",
    tags=["algorithm"]
)

@router.get("/{user_id}", response_model=AlgorithmProgressModel)
async def get_user_progress(user_id: int, session: AsyncSession = Depends(get_session)):
    try:
        # Логируем только важный выход: прогресс пользователя
        progress = await crud.get_user_progress(session, user_id)
        data = algorithm_progress_to_dict(progress)
        logger.info(f"[{user_id}] - [GET /algo/{user_id}] Прогресс пользователя: {data}")
        return data
    except Exception as e:
        logger.error(f"[{user_id}] - [GET /algo/{user_id}] Ошибка при получении прогресса: {e}")
        raise HTTPException(status_code=500, detail="Ошибка при получении прогресса пользователя")


@router.put("/{user_id}/step", response_model=None)
async def set_user_step(
    user_id: int,
    step: int,
    session: AsyncSession = Depends(get_session)
):
    try:
        # Логируем только важный вход: установка шага
        logger.info(f"[{user_id}] - [PUT /algo/{user_id}/step] Установка шага: {step}")
        await crud.set_user_step(session, user_id=user_id, step=step)
        return {"ok": True}
    except Exception as e:
        logger.error(f"[{user_id}] - [PUT /algo/{user_id}/step] Ошибка при установке шага: {e}")
        raise HTTPException(status_code=500, detail="Ошибка при обновлении шага пользователя")


@router.put("/{user_id}/basic", response_model=None)
async def set_basic_completed(
    user_id: int,
    completed: bool,
    session: AsyncSession = Depends(get_session)
):
    try:
        # Логируем только важный вход: флаг basic_completed
        logger.info(f"[{user_id}] - [PUT /algo/{user_id}/basic] Установка basic_completed={completed}")
        await crud.set_basic_completed(session, user_id=user_id, completed=completed)
        return {"ok": True}
    except Exception as e:
        logger.error(f"[{user_id}] - [PUT /algo/{user_id}/basic] Ошибка при обновлении basic_completed: {e}")
        raise HTTPException(status_code=500, detail="Ошибка при обновлении статуса basic")


@router.put("/{user_id}/advanced", response_model=None)
async def set_advanced_completed(
    user_id: int,
    completed: bool,
    session: AsyncSession = Depends(get_session)
):
    try:
        # Логируем только важный вход: флаг advanced_completed
        logger.info(f"[{user_id}] - [PUT /algo/{user_id}/advanced] Установка advanced_completed={completed}")
        await crud.set_advanced_completed(session, user_id=user_id, completed=completed)
        return {"ok": True}
    except Exception as e:
        logger.error(f"[{user_id}] - [PUT /algo/{user_id}/advanced] Ошибка при обновлении advanced_completed: {e}")
        raise HTTPException(status_code=500, detail="Ошибка при обновлении статуса advanced")


@router.delete("/{user_id}", response_model=None)
async def clear_user_data(
    user_id: int,
    session: AsyncSession = Depends(get_session)
):
    try:
        await crud.clear_user_data(session, user_id=user_id)
        # Логируем только важный выход: факт очистки данных
        logger.info(f"[{user_id}] - [DELETE /algo/{user_id}] Данные пользователя очищены")
        return {"ok": True}
    except Exception as e:
        logger.error(f"[{user_id}] - [DELETE /algo/{user_id}] Ошибка при очистке данных: {e}")
        raise HTTPException(status_code=500, detail="Ошибка при очистке данных пользователя")
