# src/routers/health.py

from fastapi import APIRouter, HTTPException
import logging

router = APIRouter(tags=["health"])
logger = logging.getLogger(__name__)


@router.get("/", tags=["health"])
async def root():
    try:
        response = {"status": "ok"}
        # Логируем только важный выход: статус сервиса
        logger.info(f"[GET /] Статус сервиса: {response}")
        return response
    except Exception as e:
        logger.error(f"[GET /] Ошибка при проверке статуса сервиса: {e}")
        raise HTTPException(status_code=500, detail="Ошибка при проверке статуса сервиса")


@router.get("/health", tags=["health"])
async def health():
    try:
        response = {"status": "healthy"}
        # Логируем только важный выход: статус здоровья системы
        logger.info(f"[GET /health] Статус здоровья: {response}")
        return response
    except Exception as e:
        logger.error(f"[GET /health] Ошибка при проверке состояния: {e}")
        raise HTTPException(status_code=500, detail="Ошибка при проверке состояния системы")


@router.get("/panic")
async def panic():
    try:
        # Здесь намеренно генерируем ошибку для теста
        raise RuntimeError("🔥 Это тестовый RuntimeError")
    except RuntimeError as e:
        # Логируем только ошибку
        logger.error(f"[GET /panic] Ошибка: {e}")
        raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера")
