# src/routers/users.py
# commit: вариант A — убрана ручная сериализация, response_model переведён на UserOut, upsert_with_membership возвращает пользователя

import logging

from fastapi import APIRouter, Body, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src import crud
from src.dependencies import get_session
from src.schemas import UserModel, UserOut, UserUpdate

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/users", tags=["users"])


@router.put("/{user_id}/upsert", response_model=UserOut)
async def upsert_user(
    user_id: int,
    user: UserModel = Body(...),
    session: AsyncSession = Depends(get_session),
):
    try:
        logger.info(
            f"[{user_id}] - [PUT /users/{user_id}/upsert] "
            f"Создание/обновление пользователя: "
            f"username={user.username!r}, full_name={user.full_name!r}, terms_accepted={user.terms_accepted}"
        )
        return await crud.upsert_user(
            session,
            id=user_id,
            username=user.username,
            full_name=user.full_name,
            terms_accepted=user.terms_accepted,
        )
    except Exception as e:
        logger.error(f"[{user_id}] - [PUT /users/{user_id}/upsert] Ошибка: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Ошибка при сохранении пользователя")


@router.put("/{user_id}/upsert_with_membership", response_model=UserOut)
async def upsert_user_and_membership(
    user_id: str,
    user: UserModel = Body(...),
    chat_id: int = Body(...),
    session: AsyncSession = Depends(get_session),
):
    try:
        cleaned = user_id.strip().lstrip("\ufeff")
        uid = int(cleaned)

        logger.info(
            f"[{uid}] - [PUT /users/{user_id}/upsert_with_membership] "
            f"Upsert user + membership: username={user.username!r}, full_name={user.full_name!r}, "
            f"chat_id={chat_id}, terms_accepted={user.terms_accepted}"
        )

        return await crud.upsert_user_and_membership(
            session,
            user_id=uid,
            username=user.username,
            full_name=user.full_name,
            chat_id=chat_id,
            terms_accepted=user.terms_accepted,
        )
    except ValueError:
        raise HTTPException(status_code=422, detail="Некорректный user_id")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[{user_id}] - [PUT /users/{user_id}/upsert_with_membership] Ошибка: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Ошибка при сохранении пользователя и добавлении в чат")


@router.put("/{user_id}", response_model=dict)
async def update_user(
    user_id: int,
    user: UserUpdate = Body(...),
    session: AsyncSession = Depends(get_session),
):
    try:
        payload = user.model_dump(exclude_none=True)
        logger.info(f"[{user_id}] - [PUT /users/{user_id}] Обновление пользователя: {payload}")
        await crud.update_user(session, id=user_id, **payload)
        return {"ok": True}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[{user_id}] - [PUT /users/{user_id}] Ошибка: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Ошибка при обновлении пользователя")


@router.get("/{user_id}", response_model=UserOut)
async def get_user(
    user_id: int,
    session: AsyncSession = Depends(get_session),
):
    try:
        user_obj = await crud.get_user(session, id=user_id)
        if not user_obj:
            raise HTTPException(status_code=404, detail="Пользователь не найден")

        logger.info(f"[{user_id}] - [GET /users/{user_id}] Пользователь найден")
        return user_obj
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[{user_id}] - [GET /users/{user_id}] Ошибка: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Ошибка при получении пользователя")


@router.patch("/{user_id}", status_code=204)
async def patch_user(
    user_id: int,
    user: UserUpdate = Body(...),
    session: AsyncSession = Depends(get_session),
):
    try:
        data = user.model_dump(exclude_none=True)
        if not data:
            raise HTTPException(status_code=400, detail="Нет полей для обновления")
        logger.info(f"[{user_id}] - [PATCH /users/{user_id}] Частичное обновление: {data}")
        await crud.update_user(session, id=user_id, **data)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[{user_id}] - [PATCH /users/{user_id}] Ошибка: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Ошибка при частичном обновлении пользователя")


@router.delete("/{user_id}", response_model=dict)
async def delete_user(
    user_id: int,
    session: AsyncSession = Depends(get_session),
):
    try:
        await crud.delete_user(session, id=user_id)
        logger.info(f"[{user_id}] - [DELETE /users/{user_id}] Пользователь удалён")
        return {"ok": True}
    except Exception as e:
        logger.error(f"[{user_id}] - [DELETE /users/{user_id}] Ошибка: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Ошибка при удалении пользователя")
