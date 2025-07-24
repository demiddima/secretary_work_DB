# src/routers/users.py

import logging
from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.ext.asyncio import AsyncSession

from src.schemas import UserModel, UserUpdate
from src.database import get_session
from src import crud
from src.utils import user_to_dict

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/users", tags=["users"])


@router.put("/{user_id}/upsert", response_model=UserModel)
async def upsert_user(
    user_id: int,
    user: UserModel = Body(...),
    session: AsyncSession = Depends(get_session),
):
    try:
        # Логируем подробности входных данных для создания или обновления пользователя
        logger.info(
            f"[{user_id}] - [PUT /users/{user_id}/upsert] "
            f"Создать/обновить пользователя с параметрами: "
            f"id={user_id}, username={user.username!r}, full_name={user.full_name!r}, terms_accepted={user.terms_accepted}"
        )
        return await crud.upsert_user(
            session,
            id=user_id,
            username=user.username,
            full_name=user.full_name,
            terms_accepted=user.terms_accepted,
        )
    except Exception as e:
        logger.error(f"[{user_id}] - [PUT /users/{user_id}/upsert] Ошибка при сохранении пользователя: {e}")
        raise HTTPException(status_code=500, detail="Ошибка при сохранении пользователя")


@router.put("/{user_id}", response_model=None)
async def update_user(
    user_id: int,
    user: UserUpdate = Body(...),
    session: AsyncSession = Depends(get_session),
):
    try:
        payload = user.dict(exclude_none=True)
        # Логируем подробности входных данных для обновления пользователя
        logger.info(
            f"[{user_id}] - [PUT /users/{user_id}] "
            f"Обновление полей пользователя: {payload}"
        )
        await crud.update_user(session, id=user_id, **payload)
        return {"ok": True}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[{user_id}] - [PUT /users/{user_id}] Ошибка при обновлении пользователя: {e}")
        raise HTTPException(status_code=500, detail="Ошибка при обновлении пользователя")


@router.get("/{user_id}", response_model=UserModel)
async def get_user(
    user_id: int,
    session: AsyncSession = Depends(get_session)
):
    try:
        user_obj = await crud.get_user(session, id=user_id)
        if not user_obj:
            raise HTTPException(status_code=404, detail="Пользователь не найден")
        data = user_to_dict(user_obj)
        # Логируем подробности выходных данных: сведения о пользователе
        logger.info(
            f"[{user_id}] - [GET /users/{user_id}] "
            f"Получены данные пользователя: {data}"
        )
        return user_obj
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[{user_id}] - [GET /users/{user_id}] Ошибка при получении пользователя: {e}")
        raise HTTPException(status_code=500, detail="Ошибка при получении пользователя")


@router.patch("/{user_id}", status_code=204)
async def patch_user(
    user_id: int,
    user: UserUpdate = Body(...),
    session: AsyncSession = Depends(get_session)
):
    try:
        data = user.dict(exclude_none=True)
        if not data:
            raise HTTPException(status_code=400, detail="Нет полей для обновления")
        # Логируем подробности входных данных для частичного обновления
        logger.info(
            f"[{user_id}] - [PATCH /users/{user_id}] "
            f"Частичное обновление полей пользователя: {data}"
        )
        await crud.update_user(session, id=user_id, **data)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[{user_id}] - [PATCH /users/{user_id}] Ошибка при частичном обновлении пользователя: {e}")
        raise HTTPException(status_code=500, detail="Ошибка при частичном обновлении пользователя")


@router.delete("/{user_id}", response_model=None)
async def delete_user(
    user_id: int,
    session: AsyncSession = Depends(get_session)
):
    try:
        await crud.delete_user(session, id=user_id)
        # Логируем факт успешного удаления пользователя
        logger.info(
            f"[{user_id}] - [DELETE /users/{user_id}] "
            f"Пользователь с id={user_id} успешно удалён"
        )
        return {"ok": True}
    except Exception as e:
        logger.error(f"[{user_id}] - [DELETE /users/{user_id}] Ошибка при удалении пользователя: {e}")
        raise HTTPException(status_code=500, detail="Ошибка при удалении пользователя")
