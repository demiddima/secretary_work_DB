# Commit: Сбор прогресса в роутере через существующие CRUD-функции без изменения src/crud.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from src.schemas import AlgorithmProgressModel
from src.database import get_session
from src import crud

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/algo",
    tags=["algorithm"]
)

@router.get("/{user_id}", response_model=AlgorithmProgressModel)
async def get_user_progress(user_id: int, session: AsyncSession = Depends(get_session)):
    """
    Собирает прогресс пользователя: текущий шаг, статус базового и расширенного завершения.
    """
    try:
        step = await crud.get_user_step(session, user_id)
        basic = await crud.get_basic_completed(session, user_id)
        advanced = await crud.get_advanced_completed(session, user_id)
        progress = {
            "current_step": step or 0,
            "basic_completed": basic or False,
            "advanced_completed": advanced or False
        }
        logger.info(f"[{user_id}] – [GET /algo/{user_id}] Прогресс пользователя: {progress}")
        return progress
    except Exception as e:
        logger.error(f"[{user_id}] – [GET /algo/{user_id}] Ошибка при получении прогресса: {e}")
        raise HTTPException(status_code=500, detail="Ошибка при получении прогресса пользователя")


@router.put("/{user_id}/step", response_model=None)
async def set_user_step(
    user_id: int,
    step: int,
    session: AsyncSession = Depends(get_session)
):
    """
    Устанавливает текущий шаг алгоритма для пользователя.
    """
    try:
        logger.info(f"[{user_id}] – [PUT /algo/{user_id}/step] Установка шага: {step}")
        await crud.set_user_step(session, user_id=user_id, step=step)
        return {"ok": True}
    except Exception as e:
        logger.error(f"[{user_id}] – [PUT /algo/{user_id}/step] Ошибка при установке шага: {e}")
        raise HTTPException(status_code=500, detail="Ошибка при обновлении шага пользователя")


@router.put("/{user_id}/basic", response_model=None)
async def set_basic_completed(
    user_id: int,
    completed: bool,
    session: AsyncSession = Depends(get_session)
):
    """
    Устанавливает признак завершения базового алгоритма.
    """
    try:
        logger.info(f"[{user_id}] – [PUT /algo/{user_id}/basic] Установка basic_completed={completed}")
        await crud.set_basic_completed(session, user_id=user_id, completed=completed)
        return {"ok": True}
    except Exception as e:
        logger.error(f"[{user_id}] – [PUT /algo/{user_id}/basic] Ошибка при обновлении basic_completed: {e}")
        raise HTTPException(status_code=500, detail="Ошибка при обновлении статуса basic")


@router.put("/{user_id}/advanced", response_model=None)
async def set_advanced_completed(
    user_id: int,
    completed: bool,
    session: AsyncSession = Depends(get_session)
):
    """
    Устанавливает признак завершения расширенного алгоритма.
    """
    try:
        logger.info(f"[{user_id}] – [PUT /algo/{user_id}/advanced] Установка advanced_completed={completed}")
        await crud.set_advanced_completed(session, user_id=user_id, completed=completed)
        return {"ok": True}
    except Exception as e:
        logger.error(f"[{user_id}] – [PUT /algo/{user_id}/advanced] Ошибка при обновлении advanced_completed: {e}")
        raise HTTPException(status_code=500, detail="Ошибка при обновлении статуса advanced")


@router.delete("/{user_id}", response_model=None)
async def clear_user_data(
    user_id: int,
    session: AsyncSession = Depends(get_session)
):
    """
    Полностью очищает все данные пользователя из алгоритма.
    """
    try:
        await crud.clear_user_data(session, user_id=user_id)
        logger.info(f"[{user_id}] – [DELETE /algo/{user_id}] Данные пользователя очищены")
        return {"ok": True}
    except Exception as e:
        logger.error(f"[{user_id}] – [DELETE /algo/{user_id}] Ошибка при очистке данных: {e}")
        raise HTTPException(status_code=500, detail="Ошибка при очистке данных пользователя")
