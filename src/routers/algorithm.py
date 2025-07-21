# src/routers/algorithm.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from src.schemas import AlgorithmProgressModel
from src.database import get_session
from src import crud
from src.utils import algorithm_progress_to_dict  # Импортируем функцию преобразования

logger = logging.getLogger()

router = APIRouter(
    prefix="/algo",
    tags=["algorithm"]
)

# Получаем прогресс пользователя
@router.get("/{user_id}", response_model=AlgorithmProgressModel)
async def get_user_progress(
    user_id: int,
    session: AsyncSession = Depends(get_session)
):
    try:
        logger.info(f"[{user_id}] - [GET /algo/{user_id}] Входящий запрос для получения прогресса пользователя.")
        
        # Получаем шаг пользователя
        step = await crud.get_user_step(session, user_id=user_id)
        
        # Получаем информацию о статусах "basic" и "advanced"
        basic = await crud.get_basic_completed(session, user_id=user_id)
        advanced = await crud.get_advanced_completed(session, user_id=user_id)
        
        updated_at = None

        # Формируем объект с прогрессом пользователя
        response_data = AlgorithmProgressModel(
            user_id=user_id,
            current_step=step or 0,
            basic_completed=basic or False,
            advanced_completed=advanced or False,
            updated_at=updated_at
        )

        logger.info(f"[{user_id}] - [GET /algo/{user_id}] Исходящий ответ: {algorithm_progress_to_dict(response_data)}")
        return response_data
    except Exception as e:
        logger.error(f"[{user_id}] - [GET /algo/{user_id}] Ошибка при получении прогресса пользователя: {str(e)}")
        raise HTTPException(status_code=500, detail="Ошибка при получении прогресса пользователя")

# Обновляем шаг пользователя в базе данных
@router.put("/{user_id}/step", response_model=None)
async def set_user_step(
    user_id: int,
    step: int,
    session: AsyncSession = Depends(get_session)
):
    try:
        logger.info(f"[{user_id}] - [PUT /algo/{user_id}/step] Входящий запрос для обновления шага пользователя на {step}")

        # Обновляем шаг пользователя
        await crud.set_user_step(session, user_id=user_id, step=step)

        logger.info(f"[{user_id}] - [PUT /algo/{user_id}/step] Исходящий ответ: {{'ok': True}}")
        return {"ok": True}
    except Exception as e:
        logger.error(f"[{user_id}] - [PUT /algo/{user_id}/step] Ошибка при обновлении шага пользователя: {str(e)}")
        raise HTTPException(status_code=500, detail="Ошибка при обновлении шага пользователя")

# Обновляем статус "basic" в базе данных
@router.put("/{user_id}/basic", response_model=None)
async def set_basic_completed(
    user_id: int,
    completed: bool,
    session: AsyncSession = Depends(get_session)
):
    try:
        logger.info(f"[{user_id}] - [PUT /algo/{user_id}/basic] Входящий запрос для обновления статуса 'basic' пользователя на {completed}")

        # Обновляем статус "basic"
        await crud.set_basic_completed(session, user_id=user_id, completed=completed)

        logger.info(f"[{user_id}] - [PUT /algo/{user_id}/basic] Исходящий ответ: {{'ok': True}}")
        return {"ok": True}
    except Exception as e:
        logger.error(f"[{user_id}] - [PUT /algo/{user_id}/basic] Ошибка при обновлении статуса 'basic': {str(e)}")
        raise HTTPException(status_code=500, detail="Ошибка при обновлении статуса basic пользователя")

# Обновляем статус "advanced" в базе данных
@router.put("/{user_id}/advanced", response_model=None)
async def set_advanced_completed(
    user_id: int,
    completed: bool,
    session: AsyncSession = Depends(get_session)
):
    try:
        logger.info(f"[{user_id}] - [PUT /algo/{user_id}/advanced] Входящий запрос для обновления статуса 'advanced' пользователя на {completed}")

        # Обновляем статус "advanced"
        await crud.set_advanced_completed(session, user_id=user_id, completed=completed)

        logger.info(f"[{user_id}] - [PUT /algo/{user_id}/advanced] Исходящий ответ: {{'ok': True}}")
        return {"ok": True}
    except Exception as e:
        logger.error(f"[{user_id}] - [PUT /algo/{user_id}/advanced] Ошибка при обновлении статуса 'advanced': {str(e)}")
        raise HTTPException(status_code=500, detail="Ошибка при обновлении статуса advanced пользователя")

# Очищаем данные пользователя
@router.delete("/{user_id}", response_model=None)
async def clear_user_data(
    user_id: int,
    session: AsyncSession = Depends(get_session)
):
    try:
        logger.info(f"[{user_id}] - [DELETE /algo/{user_id}] Входящий запрос для очистки данных пользователя")

        # Очищаем все данные пользователя
        await crud.clear_user_data(session, user_id=user_id)

        logger.info(f"[{user_id}] - [DELETE /algo/{user_id}] Исходящий ответ: {{'ok': True}}")
        return {"ok": True}
    except Exception as e:
        logger.error(f"[{user_id}] - [DELETE /algo/{user_id}] Ошибка при очистке данных пользователя: {str(e)}")
        raise HTTPException(status_code=500, detail="Ошибка при очистке данных пользователя")
