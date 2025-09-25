# src/routers/subscriptions.py
from __future__ import annotations

import logging
from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import NoResultFound

from src.dependencies import get_session
from src.schemas import (
    UserSubscriptionModel,
    UserSubscriptionPut,
    UserSubscriptionUpdate,
    ToggleKind,
)
from src import crud

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/subscriptions", tags=["subscriptions"])


@router.get("/{user_id}", response_model=UserSubscriptionModel)
async def get_user_subscriptions(user_id: int, session: AsyncSession = Depends(get_session)):
    try:
        obj = await crud.get_user_subscriptions(session, user_id)
        if not obj:
            raise HTTPException(status_code=404, detail="Подписки не найдены")
        logger.info(f"[{user_id}] - [GET /subscriptions/{user_id}] Возвращены подписки")
        return obj
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[{user_id}] - [GET /subscriptions/{user_id}] Ошибка: {e}")
        raise HTTPException(status_code=500, detail="Ошибка при получении подписок")


@router.put("/{user_id}", response_model=UserSubscriptionModel)
async def put_subscriptions(
    user_id: int,
    payload: UserSubscriptionPut,
    session: AsyncSession = Depends(get_session),
):
    try:
        logger.info(
            f"[{user_id}] - [PUT /subscriptions/{user_id}] "
            f"Сохранение подписок (вход): {payload.model_dump(exclude_none=True)}"
        )
        sub = await crud.put_user_subscriptions(
            session,
            user_id=user_id,
            news_enabled=payload.news_enabled,
            meetings_enabled=payload.meetings_enabled,
            important_enabled=payload.important_enabled,
        )
        logger.info(f"[{user_id}] - [PUT /subscriptions/{user_id}] Подписки сохранены")
        return sub
    except ValueError as e:
        # FK/валидация
        logger.error(f"[{user_id}] - [PUT /subscriptions/{user_id}] FK/validation error: {e}")
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.error(f"[{user_id}] - [PUT /subscriptions/{user_id}] Ошибка при сохранении подписок: {e}")
        raise HTTPException(status_code=500, detail="Ошибка при сохранении подписок")


@router.patch("/{user_id}", response_model=UserSubscriptionModel)
async def patch_subscriptions(
    user_id: int,
    payload: UserSubscriptionUpdate,
    session: AsyncSession = Depends(get_session),
):
    try:
        data = payload.model_dump(exclude_none=True)
        sub = await crud.update_user_subscriptions(session, user_id, **data)
        logger.info(f"[{user_id}] - [PATCH /subscriptions/{user_id}] Подписки обновлены: {list(data.keys())}")
        return sub
    except NoResultFound:
        raise HTTPException(status_code=404, detail="Подписки не найдены")
    except Exception as e:
        logger.error(f"[{user_id}] - [PATCH /subscriptions/{user_id}] Ошибка при обновлении подписок: {e}")
        raise HTTPException(status_code=500, detail="Ошибка при обновлении подписок")


@router.post("/{user_id}/toggle", response_model=UserSubscriptionModel)
async def toggle_subscription(
    user_id: int,
    payload: ToggleKind = Body(...),
    session: AsyncSession = Depends(get_session),
):
    try:
        sub = await crud.toggle_user_subscription(session, user_id=user_id, kind=payload.kind)
        logger.info(f"[{user_id}] - [POST /subscriptions/{user_id}/toggle] Переключили {payload.kind}")
        return sub
    except NoResultFound:
        raise HTTPException(status_code=404, detail="Подписки не найдены")
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.error(f"[{user_id}] - [POST /subscriptions/{user_id}/toggle] Ошибка при переключении подписки: {e}")
        raise HTTPException(status_code=500, detail="Ошибка при переключении подписки")


@router.delete("/{user_id}", response_model=dict)
async def delete_subscriptions(user_id: int, session: AsyncSession = Depends(get_session)):
    try:
        await crud.delete_user_subscriptions(session, user_id)
        logger.info(f"[{user_id}] - [DELETE /subscriptions/{user_id}] Подписки удалены")
        return {"ok": True}
    except Exception as e:
        logger.error(f"[{user_id}] - [DELETE /subscriptions/{user_id}] Ошибка при удалении подписок: {e}")
        raise HTTPException(status_code=500, detail="Ошибка при удалении подписок")
