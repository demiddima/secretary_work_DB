# src/main.py
# commit: убраны scheduler и несуществующие роутеры; оставлен только актуальный роутинг + обработчики ошибок

import logging
from builtins import BaseExceptionGroup
from contextlib import asynccontextmanager

import src.logger  # noqa: F401  (конфиг логгера и TelegramHandler)
from fastapi import FastAPI, Request
from fastapi.exception_handlers import request_validation_exception_handler
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import IntegrityError

from src.database import engine, init_db
from src.exceptions import (
    handle_global_exception,
    handle_integrity_error,
    register_exception_handlers,
)
from src.middleware import SuppressRootAccessLogMiddleware
from src.routers import algorithm, chats, health, invite_links, links, memberships, users


logger = logging.getLogger("uvicorn.error")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # startup
    await init_db()
    yield
    # shutdown — освобождаем соединения пула
    await engine.dispose()


app = FastAPI(title="DB Service API", lifespan=lifespan)
app.add_middleware(SuppressRootAccessLogMiddleware)
register_exception_handlers(app)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    body = await request.body()
    logger.error(f"[ValidationError] body={body!r} errors={exc.errors()}")
    return await request_validation_exception_handler(request, exc)


@app.middleware("http")
async def catch_all_exceptions(request: Request, call_next):
    try:
        return await call_next(request)

    except BaseExceptionGroup as eg:
        sub = eg.exceptions[0]
        if isinstance(sub, IntegrityError):
            return await handle_integrity_error(request, sub)
        return await handle_global_exception(request, sub)

    except IntegrityError as exc:
        return await handle_integrity_error(request, exc)

    except Exception as exc:
        return await handle_global_exception(request, exc)


app.include_router(chats.router)
app.include_router(users.router)
app.include_router(memberships.router)
app.include_router(invite_links.router)
app.include_router(algorithm.router)
app.include_router(links.router)
app.include_router(health.router)
