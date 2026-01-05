# src/routers/users.py

import logging
from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.ext.asyncio import AsyncSession

from src.schemas import UserModel, UserUpdate
from src.dependencies import get_session
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
        logger.info(
            f"[{user_id}] - [PUT /users/{user_id}/upsert] "
            f"Создание/обновление пользователя (вход): "
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


@router.put("/{user_id}/upsert_with_membership", response_model=UserModel)
async def upsert_user_and_membership(
    user_id: str,  # Передаем как строку, чтобы работать с символами
    user: UserModel = Body(...),
    chat_id: int = Body(...),  # Добавляем chat_id для добавления в чат
    session: AsyncSession = Depends(get_session),
):
    try:
        # Очистка значения user_id (убираем BOM и пробелы)
        user_id = user_id.strip().lstrip('\ufeff')  # Убираем BOM и лишние пробелы
        
        # Преобразуем в целое число
        user_id = int(user_id)

        logger.info(
            f"[{user_id}] - [PUT /users/{user_id}/upsert_with_membership] "
            f"Создание/обновление пользователя и добавление в чат (вход): "
            f"id={user_id}, username={user.username!r}, full_name={user.full_name!r}, chat_id={chat_id}, terms_accepted={user.terms_accepted}"
        )
        # Новый объединённый запрос
        await crud.upsert_user_and_membership(
            session,
            user_id=user_id,
            username=user.username,
            full_name=user.full_name,
            chat_id=chat_id,
            terms_accepted=user.terms_accepted,
        )
        return {"ok": True}
    except Exception as e:
        logger.error(f"[{user_id}] - [PUT /users/{user_id}/upsert_with_membership] Ошибка: {e}")
        raise HTTPException(status_code=500, detail="Ошибка при сохранении пользователя и добавлении в чат")


@router.put("/{user_id}", response_model=None)
async def update_user(
    user_id: int,
    user: UserUpdate = Body(...),
    session: AsyncSession = Depends(get_session),
):
    try:
        payload = user.dict(exclude_none=True)
        logger.info(
            f"[{user_id}] - [PUT /users/{user_id}] "
            f"Обновление пользователя (вход): {payload}"
        )
        await crud.update_user(session, id=user_id, **payload)
        logger.info(f"[{user_id}] - [PUT /users/{user_id}] Пользователь обновлён")
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
        logger.info(
            f"[{user_id}] - [GET /users/{user_id}] "
            f"Возвращены данные пользователя: {data}"
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
        logger.info(
            f"[{user_id}] - [PATCH /users/{user_id}] "
            f"Частичное обновление пользователя (вход): {data}"
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
        logger.info(f"[{user_id}] - [DELETE /users/{user_id}] Пользователь удалён")
        return {"ok": True}
    except Exception as e:
        logger.error(f"[{user_id}] - [DELETE /users/{user_id}] Ошибка при удалении пользователя: {e}")
        raise HTTPException(status_code=500, detail="Ошибка при удалении пользователя")
