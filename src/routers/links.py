# src/routers/links.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from src.schemas import LinkVisitIn
from src.database import get_session
from src import crud

# Настроим логгер
logger = logging.getLogger()

router = APIRouter(
    prefix="/links",
    tags=["links"]
)

# Увеличиваем количество посещений для ссылки
@router.post("/visit", response_model=None)
async def increment_link_visit(
    visit: LinkVisitIn,
    session: AsyncSession = Depends(get_session)
):
    try:
        logger.info(f"[{visit.link_key}] - [POST /links/visit] Входящий запрос для увеличения посещений ссылки: {visit.link_key}")

        # Инкрементируем количество посещений для указанной ссылки
        await crud.increment_link_visit(session, link_key=visit.link_key)

        logger.info(f"[{visit.link_key}] - [POST /links/visit] Исходящий ответ: {{'ok': True}}")
        return {"ok": True}
    except HTTPException as exc:
        logger.error(f"[{visit.link_key}] - [POST /links/visit] Ошибка при увеличении посещений ссылки: {str(exc.detail)}")
        raise exc
    except Exception as e:
        logger.error(f"[{visit.link_key}] - [POST /links/visit] Неизвестная ошибка при увеличении посещений: {str(e)}")
        raise HTTPException(status_code=500, detail="Ошибка при увеличении посещений для ссылки.")
