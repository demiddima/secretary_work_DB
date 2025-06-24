import logging
import traceback
from fastapi import Request
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError

async def handle_integrity_error(request: Request, exc: IntegrityError):
    """
    Обработчик для ошибок целостности данных (IntegrityError).
    Возвращает 400 и пишет warning в консоль.
    """
    logger = logging.getLogger("db_service")
    logger.warning(f"IntegrityError: {exc.orig}")
    return JSONResponse(
        status_code=400,
        content={"detail": "Ошибка целостности данных: проверьте параметры"}
    )

async def handle_global_exception(request: Request, exc: Exception):
    """
    Универсальный обработчик всех исключений.
    Возвращает 500 и пишет полный стектрейс в лог.
    """
    logger = logging.getLogger("db_service")
    tb = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
    msg = f"Exception in request {request.method} {request.url}\n\n{tb}"
    logger.error(msg)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal Server Error"}
    )

def register_exception_handlers(app):
    """
    Регистрирует глобальные обработчики на FastAPI app:
      - IntegrityError → handle_integrity_error
      - Exception      → handle_global_exception
    """
    app.add_exception_handler(IntegrityError, handle_integrity_error)
    app.add_exception_handler(Exception, handle_global_exception)
