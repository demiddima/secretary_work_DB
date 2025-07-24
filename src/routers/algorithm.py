# commit: уточнены тексты логов — теперь они поясняют, что именно произошло

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
import logging
from datetime import datetime

from src.schemas import AlgorithmProgressModel
from src.database import get_session
from src import crud

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/algo", tags=["algorithm"])

@router.get("/{user_id}", response_model=AlgorithmProgressModel)
async def get_user_progress(user_id: int, session: AsyncSession = Depends(get_session)):
    try:
        step = await crud.get_user_step(session, user_id=user_id)
        basic = await crud.get_basic_completed(session, user_id=user_id)
        advanced = await crud.get_advanced_completed(session, user_id=user_id)
        updated_at = None  # можно добавить через отдельный CRUD-метод

        response = AlgorithmProgressModel(
            user_id=user_id,
            current_step=step or 0,
            basic_completed=basic or False,
            advanced_completed=advanced or False,
            updated_at=updated_at
        )
        logger.info(
            f"[{user_id}] GET /algo/{user_id} — возвращаем прогресс пользователя: "
            f"текущий шаг={response.current_step}, basic_completed={response.basic_completed}, "
            f"advanced_completed={response.advanced_completed}, updated_at={response.updated_at}"
        )
        return response

    except Exception as e:
        logger.error(
            f"[{user_id}] GET /algo/{user_id} — не удалось получить прогресс пользователя: {e}",
            exc_info=True
        )
        raise HTTPException(status_code=500, detail="Ошибка при получении прогресса пользователя")


@router.put("/{user_id}/step", response_model=None)
async def set_user_step(user_id: int, step: int, session: AsyncSession = Depends(get_session)):
    try:
        await crud.set_user_step(session, user_id=user_id, step=step)
        logger.info(f"[{user_id}] PUT /algo/{user_id}/step — установлен текущий шаг пользователя: {step}")
        return {"ok": True}

    except Exception as e:
        logger.error(
            f"[{user_id}] PUT /algo/{user_id}/step — не удалось установить шаг пользователя: {e}",
            exc_info=True
        )
        raise HTTPException(status_code=500, detail="Ошибка при обновлении шага пользователя")


@router.put("/{user_id}/basic", response_model=None)
async def set_basic_completed(user_id: int, completed: bool, session: AsyncSession = Depends(get_session)):
    try:
        await crud.set_basic_completed(session, user_id=user_id, completed=completed)
        logger.info(
            f"[{user_id}] PUT /algo/{user_id}/basic — флаг basic_completed "
            f"{'установлен' if completed else 'снят'}"
        )
        return {"ok": True}

    except Exception as e:
        logger.error(
            f"[{user_id}] PUT /algo/{user_id}/basic — не удалось обновить статус basic: {e}",
            exc_info=True
        )
        raise HTTPException(status_code=500, detail="Ошибка при обновлении статуса basic пользователя")


@router.put("/{user_id}/advanced", response_model=None)
async def set_advanced_completed(user_id: int, completed: bool, session: AsyncSession = Depends(get_session)):
    try:
        await crud.set_advanced_completed(session, user_id=user_id, completed=completed)
        logger.info(
            f"[{user_id}] PUT /algo/{user_id}/advanced — флаг advanced_completed "
            f"{'установлен' if completed else 'снят'}"
        )
        return {"ok": True}

    except Exception as e:
        logger.error(
            f"[{user_id}] PUT /algo/{user_id}/advanced — не удалось обновить статус advanced: {e}",
            exc_info=True
        )
        raise HTTPException(status_code=500, detail="Ошибка при обновлении статуса advanced пользователя")


@router.delete("/{user_id}", response_model=None)
async def clear_user_data(user_id: int, session: AsyncSession = Depends(get_session)):
    try:
        await crud.clear_user_data(session, user_id=user_id)
        logger.info(
            f"[{user_id}] DELETE /algo/{user_id} — очищен прогресс пользователя: "
            f"удалены текущий шаг, basic_completed, advanced_completed"
        )
        return {"ok": True}

    except Exception as e:
        logger.error(
            f"[{user_id}] DELETE /algo/{user_id} — не удалось очистить данные пользователя: {e}",
            exc_info=True
        )
        raise HTTPException(status_code=500, detail="Ошибка при очистке данных пользователя")
