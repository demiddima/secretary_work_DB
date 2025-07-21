# src/routers/health.py
from fastapi import APIRouter, HTTPException
import logging

# Настроим логгер (используем корневой логгер)
logger = logging.getLogger()

router = APIRouter(
    tags=["health"]
)

@router.get("/", tags=["health"])
async def root():
    logger.info(f"[GET /] Входящий запрос для проверки статуса сервиса.")
    
    response = {"status": "ok"}
    
    logger.info(f"[GET /] Исходящий ответ: {response}")
    return response

@router.get("/health", tags=["health"])
async def health():
    logger.info(f"[GET /health] Входящий запрос для проверки здоровья системы.")
    
    response = {"status": "healthy"}
    
    logger.info(f"[GET /health] Исходящий ответ: {response}")
    return response

@router.get("/panic")
async def panic():
    logger.info(f"[GET /panic] Входящий запрос для имитации ошибки.")

    # В данном случае просто генерируем RuntimeError для теста
    try:
        raise RuntimeError("🔥 Это тестовый RuntimeError")
    except RuntimeError as e:
        logger.error(f"[GET /panic] Ошибка: {str(e)}")
        raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера")
