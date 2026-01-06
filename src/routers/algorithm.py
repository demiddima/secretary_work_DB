# src/routers/algorithm.py
# commit: вариант A — роутер переведён на CRUD.get_progress (ORM) вместо разрозненных get_user_step/get_basic...; response_model = AlgorithmProgressModel

import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src import crud
from src.dependencies import get_session
from src.schemas import AlgorithmProgressModel

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/algo", tags=["algorithm"])


@router.get("/{user_id}", response_model=AlgorithmProgressModel)
async def get_user_progress(user_id: int, session: AsyncSession = Depends(get_session)):
    try:
        obj = await crud.get_progress(session, user_id=user_id)
        if obj is None:
            response = AlgorithmProgressModel(
                user_id=user_id,
                current_step=0,
                basic_completed=False,
                advanced_completed=False,
                updated_at=None,
            )
            logger.info(f"[{user_id}] GET /algo/{user_id} — прогресс отсутствует, отдаём дефолт")
            return response

        logger.info(f"[{user_id}] GET /algo/{user_id} — прогресс найден")
        return obj
    except Exception as e:
        logger.error(f"[{user_id}] GET /algo/{user_id} — ошибка: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Ошибка при получении прогресса пользователя")


@router.put("/{user_id}/step", response_model=dict)
async def set_user_step(user_id: int, step: int, session: AsyncSession = Depends(get_session)):
    try:
        await crud.set_user_step(session, user_id=user_id, step=step)
        logger.info(f"[{user_id}] PUT /algo/{user_id}/step — step={step}")
        return {"ok": True}
    except Exception as e:
        logger.error(f"[{user_id}] PUT /algo/{user_id}/step — ошибка: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Ошибка при обновлении шага пользователя")


@router.put("/{user_id}/basic", response_model=dict)
async def set_basic_completed(user_id: int, completed: bool, session: AsyncSession = Depends(get_session)):
    try:
        await crud.set_basic_completed(session, user_id=user_id, completed=completed)
        logger.info(f"[{user_id}] PUT /algo/{user_id}/basic — completed={completed}")
        return {"ok": True}
    except Exception as e:
        logger.error(f"[{user_id}] PUT /algo/{user_id}/basic — ошибка: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Ошибка при обновлении статуса basic пользователя")


@router.put("/{user_id}/advanced", response_model=dict)
async def set_advanced_completed(user_id: int, completed: bool, session: AsyncSession = Depends(get_session)):
    try:
        await crud.set_advanced_completed(session, user_id=user_id, completed=completed)
        logger.info(f"[{user_id}] PUT /algo/{user_id}/advanced — completed={completed}")
        return {"ok": True}
    except Exception as e:
        logger.error(f"[{user_id}] PUT /algo/{user_id}/advanced — ошибка: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Ошибка при обновлении статуса advanced пользователя")


@router.delete("/{user_id}", response_model=dict)
async def clear_user_data(user_id: int, session: AsyncSession = Depends(get_session)):
    try:
        await crud.clear_user_data(session, user_id=user_id)
        logger.info(f"[{user_id}] DELETE /algo/{user_id} — прогресс очищен")
        return {"ok": True}
    except Exception as e:
        logger.error(f"[{user_id}] DELETE /algo/{user_id} — ошибка: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Ошибка при очистке данных пользователя")
