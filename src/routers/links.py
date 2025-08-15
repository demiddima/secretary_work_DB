# src/routers/links.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from src.schemas import LinkVisitIn
from src.dependencies import get_session
from src import crud

logger = logging.getLogger(__name__)
router = APIRouter(
    prefix="/links",
    tags=["links"]
)

@router.post("/visit", response_model=None)
async def increment_link_visit(
    visit: LinkVisitIn,
    session: AsyncSession = Depends(get_session)
):
    try:
        # Логируем только важный вход: ключ ссылки для инкремента посещений
        logger.info(f"[{visit.link_key}] - [POST /links/visit] Увеличение посещений для ссылки: {visit.link_key}")
        await crud.increment_link_visit(session, link_key=visit.link_key)
        return {"ok": True}
    except HTTPException as exc:
        logger.error(f"[{visit.link_key}] - [POST /links/visit] Ошибка при увеличении посещений ссылки: {exc.detail}")
        raise
    except Exception as e:
        logger.error(f"[{visit.link_key}] - [POST /links/visit] Неизвестная ошибка при увеличении посещений: {e}")
        raise HTTPException(status_code=500, detail="Ошибка при увеличении посещений для ссылки.")
