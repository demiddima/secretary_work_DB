# src/routers/links.py
# commit: вариант A — без ручной сериализации; ok-ответ сохранён

import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src import crud
from src.dependencies import get_session
from src.schemas import LinkVisitIn

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/links", tags=["links"])


@router.post("/visit", response_model=dict)
async def increment_link_visit(
    visit: LinkVisitIn,
    session: AsyncSession = Depends(get_session),
):
    try:
        logger.info(f"[{visit.link_key}] - [POST /links/visit] increment")
        await crud.increment_link_visit(session, link_key=visit.link_key)
        return {"ok": True}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[{visit.link_key}] - [POST /links/visit] Ошибка: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Ошибка при увеличении посещений для ссылки.")
