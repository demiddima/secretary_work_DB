# src/main.py
# commit: добавлен shutdown cleanup (engine.dispose) в lifespan

import logging
import src.logger  # конфиг логгера и TelegramHandler
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.exception_handlers import request_validation_exception_handler
from contextlib import asynccontextmanager
from builtins import BaseExceptionGroup
from sqlalchemy.exc import IntegrityError

from src.exceptions import (
    handle_integrity_error,
    handle_global_exception,
    register_exception_handlers,
)
from src.database import init_db, engine
from src.scheduler import setup_scheduler
from src.routers import (
    chats, users, memberships, scheduled_announcements,
    invite_links, algorithm, links, health,
    requests, reminder_settings, notifications, offers,
)
from src.middleware import SuppressRootAccessLogMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    # startup
    await init_db()
    await setup_scheduler()
    yield
    # shutdown — освобождаем соединения пула
    await engine.dispose()


app = FastAPI(title="DB Service API", lifespan=lifespan)

logger = logging.getLogger("uvicorn.error")


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


register_exception_handlers(app)
app.add_middleware(SuppressRootAccessLogMiddleware)

app.include_router(chats.router)
app.include_router(users.router)
app.include_router(memberships.router)
app.include_router(invite_links.router)
app.include_router(algorithm.router)
app.include_router(links.router)
app.include_router(health.router)
app.include_router(requests.router)
app.include_router(reminder_settings.router)
app.include_router(notifications.router)
app.include_router(offers.router)
app.include_router(scheduled_announcements.router)
