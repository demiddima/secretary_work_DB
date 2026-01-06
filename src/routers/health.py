# src/routers/health.py
# commit: упрощение и стабилизация health-эндпоинтов; контракты ответов без изменений

import logging

from fastapi import APIRouter, HTTPException

router = APIRouter(tags=["health"])
logger = logging.getLogger(__name__)


@router.get("/", tags=["health"])
async def root():
    try:
        response = {"status": "ok"}
        logger.info(f"[GET /] Статус сервиса: {response}")
        return response
    except Exception as e:
        logger.error(f"[GET /] Ошибка: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Ошибка при проверке статуса сервиса")


@router.get("/health", tags=["health"])
async def health():
    try:
        response = {"status": "healthy"}
        logger.info(f"[GET /health] Статус здоровья: {response}")
        return response
    except Exception as e:
        logger.error(f"[GET /health] Ошибка: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Ошибка при проверке состояния системы")


@router.get("/panic")
async def panic():
    try:
        raise RuntimeError("🔥 Это тестовый RuntimeError")
    except RuntimeError as e:
        logger.error(f"[GET /panic] Ошибка: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера")
