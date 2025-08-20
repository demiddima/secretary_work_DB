# src/routers/subscriptions.py

import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

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
async def get_subscriptions(user_id: int, session: AsyncSession = Depends(get_session)):
    """
    Возвращает подписки пользователя.
    Если записи нет — создаёт с дефолтами и возвращает её.
    """
    try:
        sub = await crud.get_user_subscriptions(session, user_id)
        if sub is None:
            sub = await crud.ensure_user_subscriptions_defaults(session, user_id)
            logger.info(f"[{user_id}] - [GET /subscriptions/{user_id}] created defaults")
        else:
            logger.info(f"[{user_id}] - [GET /subscriptions/{user_id}] ok")
        return sub
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[{user_id}] - [GET /subscriptions/{user_id}] error: {e}")
        raise HTTPException(status_code=500, detail="Internal error")


@router.put("/{user_id}", response_model=UserSubscriptionModel)
async def put_subscriptions(
    user_id: int,
    payload: UserSubscriptionPut,
    session: AsyncSession = Depends(get_session),
):
    try:
        sub = await crud.put_user_subscriptions(
            session,
            user_id=user_id,
            news_enabled=payload.news_enabled,
            meetings_enabled=payload.meetings_enabled,
            important_enabled=payload.important_enabled,
        )
        logger.info(f"[{user_id}] - [PUT /subscriptions/{user_id}] upsert ok: {payload.model_dump()}")
        return sub
    except Exception as e:
        logger.error(f"[{user_id}] - [PUT /subscriptions/{user_id}] error: {e}")
        raise HTTPException(status_code=500, detail="Internal error")


@router.patch("/{user_id}", response_model=UserSubscriptionModel)
async def patch_subscriptions(
    user_id: int,
    payload: UserSubscriptionUpdate,
    session: AsyncSession = Depends(get_session),
):
    try:
        sub = await crud.update_user_subscriptions(
            session,
            user_id,
            **{k: v for k, v in payload.model_dump(exclude_none=True).items()}
        )
        logger.info(f"[{user_id}] - [PATCH /subscriptions/{user_id}] ok: {payload.model_dump(exclude_none=True)}")
        return sub
    except Exception as e:
        logger.error(f"[{user_id}] - [PATCH /subscriptions/{user_id}] error: {e}")
        raise HTTPException(status_code=500, detail="Internal error")


@router.post("/{user_id}/toggle", response_model=UserSubscriptionModel)
async def toggle_subscription(
    user_id: int,
    payload: ToggleKind,
    session: AsyncSession = Depends(get_session),
):
    try:
        sub = await crud.toggle_user_subscription(session, user_id, payload.kind)
        logger.info(f"[{user_id}] - [POST /subscriptions/{user_id}/toggle] ok: kind={payload.kind}")
        return sub
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid kind")
    except Exception as e:
        logger.error(f"[{user_id}] - [POST /subscriptions/{user_id}/toggle] error: {e}")
        raise HTTPException(status_code=500, detail="Internal error")


@router.delete("/{user_id}", response_model=None)
async def delete_subscriptions(user_id: int, session: AsyncSession = Depends(get_session)):
    try:
        await crud.delete_user_subscriptions(session, user_id)
        logger.info(f"[{user_id}] - [DELETE /subscriptions/{user_id}] ok")
        return {"ok": True}
    except Exception as e:
        logger.error(f"[{user_id}] - [DELETE /subscriptions/{user_id}] error: {e}")
        raise HTTPException(status_code=500, detail="Internal error")
