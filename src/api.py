from fastapi.responses import JSONResponse, PlainTextResponse
from fastapi import Request, FastAPI, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from .database import init_db, AsyncSessionLocal
from . import crud
from .config import settings
from pydantic import BaseModel
from typing import Optional, List
import logging
import traceback
import httpx
import asyncio
from starlette.middleware.base import BaseHTTPMiddleware
from sqlalchemy.exc import IntegrityError

# NEW: APScheduler для фоновых задач
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
import pytz

# === ДОБАВЛЕНО: импорт защиты API-ключа ===
from .security import get_api_key

# ---- Middleware для отключения access log на "/" ----
class SuppressRootAccessLogMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        if request.url.path == "/":
            # Заглушка для "/" — без логов, но с ответом
            return PlainTextResponse("OK", status_code=200)
        return await call_next(request)

app = FastAPI(title="DB Service API")
app.add_middleware(SuppressRootAccessLogMiddleware)

# Configure logging
logging.basicConfig(
    level=settings.LOG_LEVEL,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# APScheduler (глобальный объект)
scheduler = AsyncIOScheduler()

# Перехват IntegrityError для централизованной обработки
@app.exception_handler(IntegrityError)
async def handle_integrity_error(request: Request, exc: IntegrityError):
    logging.getLogger("db_service").warning(f"IntegrityError: {exc.orig}")
    return JSONResponse(
        status_code=400,
        content={"detail": "Ошибка целостности данных: проверьте параметры"}
    )

# Pydantic schemas
class ChatModel(BaseModel):
    id: int
    title: str
    type: str

class UserModel(BaseModel):
    id: int
    username: Optional[str]
    full_name: Optional[str]

class InviteLinkModel(BaseModel):
    id: int
    user_id: int
    chat_id: int
    invite_link: str
    created_at: str
    expires_at: str

class AlgorithmProgressModel(BaseModel):
    user_id: int
    current_step: int
    basic_completed: bool
    advanced_completed: bool

class InviteLinkIn(BaseModel):
    user_id: int
    chat_id: int
    invite_link: str
    created_at: str
    expires_at: str

@app.on_event("startup")
async def on_startup():
    await init_db()

    # ------ APScheduler: запуск очистки по расписанию ------
    async with AsyncSessionLocal() as session:
        cron_str = await crud.get_cleanup_cron(session)
    trigger = CronTrigger.from_crontab(cron_str, timezone=pytz.timezone('Europe/Moscow'))

    async def scheduled_cleanup():
        async with AsyncSessionLocal() as session:
            deleted = await crud.cleanup_orphan_users(session)
            if deleted:
                logging.info(f"[CLEANUP] Deleted orphan users: {deleted}")
            else:
                logging.info("[CLEANUP] No orphan users found.")

    scheduler.add_job(scheduled_cleanup, trigger)
    scheduler.start()
    logging.info(f"[CLEANUP] Orphan cleanup scheduled: {cron_str} (Europe/Moscow)")

# === ЗАЩИЩЁННЫЙ endpoint (требует API-ключ) ===
@app.get("/", dependencies=[Depends(get_api_key)])
async def root():
    return {"status": "ok"}

async def get_session() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session

# Chats endpoints (требуют API-ключ)
@app.post("/chats/", response_model=ChatModel, dependencies=[Depends(get_api_key)])
async def upsert_chat(chat: ChatModel, session: AsyncSession = Depends(get_session)):
    res = await crud.upsert_chat(session, chat.id, chat.title, chat.type)
    return ChatModel(id=res.id, title=res.title, type=res.type)

@app.get("/chats/", response_model=List[int], dependencies=[Depends(get_api_key)])
async def get_chats(session: AsyncSession = Depends(get_session)):
    return await crud.get_all_chats(session)

@app.delete("/chats/{chat_id}", dependencies=[Depends(get_api_key)])
async def delete_chat(chat_id: int, session: AsyncSession = Depends(get_session)):
    await crud.delete_chat(session, chat_id)
    return {"status": "deleted"}

# Users endpoints (требуют API-ключ)
@app.put("/users/{user_id}/upsert", response_model=UserModel, dependencies=[Depends(get_api_key)])
async def upsert_user(user_id: int, user: UserModel, session: AsyncSession = Depends(get_session)):
    res = await crud.upsert_user(session, user_id, user.username, user.full_name)
    return UserModel(id=res.id, username=res.username, full_name=res.full_name)

@app.get("/users/{user_id}", response_model=UserModel, dependencies=[Depends(get_api_key)])
async def get_user(user_id: int, session: AsyncSession = Depends(get_session)):
    res = await crud.get_user(session, user_id)
    if not res:
        raise HTTPException(status_code=404, detail="User not found")
    return UserModel(id=res.id, username=res.username, full_name=res.full_name)

@app.put("/users/{user_id}", response_model=UserModel, dependencies=[Depends(get_api_key)])
async def update_user(user_id: int, user: UserModel, session: AsyncSession = Depends(get_session)):
    await crud.update_user(session, user_id, username=user.username, full_name=user.full_name)
    res = await crud.get_user(session, user_id)
    return UserModel(id=res.id, username=res.username, full_name=res.full_name)

@app.delete("/users/{user_id}", dependencies=[Depends(get_api_key)])
async def delete_user(user_id: int, session: AsyncSession = Depends(get_session)):
    await crud.delete_user(session, user_id)
    return {"status": "deleted"}

# Memberships endpoints (требуют API-ключ)
@app.post("/memberships/", status_code=200, dependencies=[Depends(get_api_key)])
async def upsert_membership(user_id: int, chat_id: int, session: AsyncSession = Depends(get_session)):
    try:
        await crud.upsert_user_to_chat(session, user_id, chat_id)
    except IntegrityError as exc:
        logging.getLogger("db_service").warning(
            f"IntegrityError при upsert_user_to_chat(user={user_id}, chat={chat_id}): {exc.orig}"
        )
    return {"status": "ok"}

@app.delete("/memberships/", dependencies=[Depends(get_api_key)])
async def remove_membership(user_id: int, chat_id: int, session: AsyncSession = Depends(get_session)):
    await crud.remove_user_from_chat(session, user_id, chat_id)
    return {"status": "removed"}

# Invite links endpoints (требуют API-ключ)
@app.post("/invite_links/", response_model=InviteLinkModel, dependencies=[Depends(get_api_key)])
async def save_invite_link(invite_link: InviteLinkIn, session: AsyncSession = Depends(get_session)):
    res = await crud.save_invite_link(
        session,
        invite_link.user_id,
        invite_link.chat_id,
        invite_link.invite_link,
        invite_link.created_at,
        invite_link.expires_at,
    )
    return InviteLinkModel(
        id=res.id, user_id=res.user_id, chat_id=res.chat_id,
        invite_link=res.invite_link, created_at=str(res.created_at), expires_at=str(res.expires_at)
    )

@app.get("/invite_links/{user_id}", response_model=List[InviteLinkModel], dependencies=[Depends(get_api_key)])
async def get_invite_links(user_id: int, session: AsyncSession = Depends(get_session)):
    res = await crud.get_valid_invite_links(session, user_id)
    return [
        InviteLinkModel(
            id=item.id, user_id=item.user_id, chat_id=item.chat_id,
            invite_link=item.invite_link, created_at=str(item.created_at), expires_at=str(item.expires_at)
        ) for item in res
    ]

@app.delete("/invite_links/{user_id}", dependencies=[Depends(get_api_key)])
async def delete_invite_links(user_id: int, session: AsyncSession = Depends(get_session)):
    await crud.delete_invite_links(session, user_id)
    return {"status": "deleted"}

# Algorithm progress endpoints (требуют API-ключ)
@app.get("/algo/{user_id}", response_model=AlgorithmProgressModel, dependencies=[Depends(get_api_key)])
async def get_progress(user_id: int, session: AsyncSession = Depends(get_session)):
    step = await crud.get_user_step(session, user_id)
    basic = await crud.get_basic_completed(session, user_id)
    adv = await crud.get_advanced_completed(session, user_id)
    return AlgorithmProgressModel(user_id=user_id, current_step=step or 0, basic_completed=basic or False, advanced_completed=adv or False)

@app.put("/algo/{user_id}/step", dependencies=[Depends(get_api_key)])
async def set_progress(user_id: int, step: int, session: AsyncSession = Depends(get_session)):
    res = await crud.set_user_step(session, user_id, step)
    return {"status": "set", "current_step": res.current_step}

@app.put("/algo/{user_id}/basic", dependencies=[Depends(get_api_key)])
async def set_basic(user_id: int, completed: bool, session: AsyncSession = Depends(get_session)):
    res = await crud.set_basic_completed(session, user_id, completed)
    return {"status": "set", "basic_completed": res.basic_completed}

@app.put("/algo/{user_id}/advanced", dependencies=[Depends(get_api_key)])
async def set_advanced(user_id: int, completed: bool, session: AsyncSession = Depends(get_session)):
    res = await crud.set_advanced_completed(session, user_id, completed)
    return {"status": "set", "advanced_completed": res.advanced_completed}

@app.delete("/algo/{user_id}", dependencies=[Depends(get_api_key)])
async def clear_progress(user_id: int, session: AsyncSession = Depends(get_session)):
    await crud.clear_user_data(session, user_id)
    return {"status": "cleared"}

# Endpoint здоровья (healthcheck) — можно оставить открытым
@app.get("/health")
async def health():
    return {"status": "ok"}

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc):
    """
    Handle uncaught exceptions, log and notify via Telegram
    """
    logger = logging.getLogger('db_service')
    tb = ''.join(traceback.format_exception(type(exc), exc, exc.__traceback__))
    msg = f"Exception in request {request.method} {request.url}\n\n{tb}"
    # Log the error
    logger.error(msg)
    # Send to Telegram channel
    token = settings.TELEGRAM_BOT_TOKEN
    chat_id = settings.LOG_CHANNEL_ID
    async with httpx.AsyncClient() as client:
        await client.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            json={"chat_id": chat_id, "text": msg}
        )
    return JSONResponse(status_code=500, content={"detail": "Internal Server Error"})
