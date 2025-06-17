from fastapi.responses import JSONResponse
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
from fastapi.responses import PlainTextResponse
from starlette.middleware.base import BaseHTTPMiddleware

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

@app.get("/")
async def root():
    return {"status": "ok"}

async def get_session() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session

# Chats endpoints
@app.post("/chats/", response_model=ChatModel)
async def upsert_chat(chat: ChatModel, session: AsyncSession = Depends(get_session)):
    res = await crud.upsert_chat(session, chat.id, chat.title, chat.type)
    return ChatModel(id=res.id, title=res.title, type=res.type)

@app.get("/chats/", response_model=List[int])
async def get_chats(session: AsyncSession = Depends(get_session)):
    return await crud.get_all_chats(session)

@app.delete("/chats/{chat_id}")
async def delete_chat(chat_id: int, session: AsyncSession = Depends(get_session)):
    await crud.delete_chat(session, chat_id)
    return {"status": "deleted"}

# Users endpoints
@app.put("/users/{user_id}/upsert", response_model=UserModel)
async def upsert_user(user_id: int, user: UserModel, session: AsyncSession = Depends(get_session)):
    res = await crud.upsert_user(session, user_id, user.username, user.full_name)
    return UserModel(id=res.id, username=res.username, full_name=res.full_name)

@app.get("/users/{user_id}", response_model=UserModel)
async def get_user(user_id: int, session: AsyncSession = Depends(get_session)):
    res = await crud.get_user(session, user_id)
    if not res:
        raise HTTPException(status_code=404, detail="User not found")
    return UserModel(id=res.id, username=res.username, full_name=res.full_name)

@app.put("/users/{user_id}", response_model=UserModel)
async def update_user(user_id: int, user: UserModel, session: AsyncSession = Depends(get_session)):
    await crud.update_user(session, user_id, username=user.username, full_name=user.full_name)
    res = await crud.get_user(session, user_id)
    return UserModel(id=res.id, username=res.username, full_name=res.full_name)

@app.delete("/users/{user_id}")
async def delete_user(user_id: int, session: AsyncSession = Depends(get_session)):
    await crud.delete_user(session, user_id)
    return {"status": "deleted"}

# Memberships endpoints — теперь upsert!
@app.post("/memberships/", status_code=200)
async def upsert_membership(user_id: int, chat_id: int, session: AsyncSession = Depends(get_session)):
    await crud.upsert_user_to_chat(session, user_id, chat_id)
    return {"status": "ok"}

@app.delete("/memberships/")
async def remove_membership(user_id: int, chat_id: int, session: AsyncSession = Depends(get_session)):
    await crud.remove_user_from_chat(session, user_id, chat_id)
    return {"status": "removed"}

# Invite links endpoints
@app.post("/invite_links/", response_model=InviteLinkModel)
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

@app.get("/invite_links/{user_id}", response_model=List[InviteLinkModel])
async def get_invite_links(user_id: int, session: AsyncSession = Depends(get_session)):
    res = await crud.get_valid_invite_links(session, user_id)
    return [
        InviteLinkModel(
            id=item.id, user_id=item.user_id, chat_id=item.chat_id,
            invite_link=item.invite_link, created_at=str(item.created_at), expires_at=str(item.expires_at)
        ) for item in res
    ]

@app.delete("/invite_links/{user_id}")
async def delete_invite_links(user_id: int, session: AsyncSession = Depends(get_session)):
    await crud.delete_invite_links(session, user_id)
    return {"status": "deleted"}

# Algorithm progress endpoints
@app.get("/algo/{user_id}", response_model=AlgorithmProgressModel)
async def get_progress(user_id: int, session: AsyncSession = Depends(get_session)):
    step = await crud.get_user_step(session, user_id)
    basic = await crud.get_basic_completed(session, user_id)
    adv = await crud.get_advanced_completed(session, user_id)
    return AlgorithmProgressModel(user_id=user_id, current_step=step or 0, basic_completed=basic or False, advanced_completed=adv or False)

@app.put("/algo/{user_id}/step")
async def set_progress(user_id: int, step: int, session: AsyncSession = Depends(get_session)):
    res = await crud.set_user_step(session, user_id, step)
    return {"status": "set", "current_step": res.current_step}

@app.put("/algo/{user_id}/basic")
async def set_basic(user_id: int, completed: bool, session: AsyncSession = Depends(get_session)):
    res = await crud.set_basic_completed(session, user_id, completed)
    return {"status": "set", "basic_completed": res.basic_completed}

@app.put("/algo/{user_id}/advanced")
async def set_advanced(user_id: int, completed: bool, session: AsyncSession = Depends(get_session)):
    res = await crud.set_advanced_completed(session, user_id, completed)
    return {"status": "set", "advanced_completed": res.advanced_completed}

@app.delete("/algo/{user_id}")
async def clear_progress(user_id: int, session: AsyncSession = Depends(get_session)):
    await crud.clear_user_data(session, user_id)
    return {"status": "cleared"}

# Health check with database verification
@app.get("/health")
async def health():
    try:
        async with AsyncSessionLocal() as session:
            await session.execute("SELECT 1")
        return {"status": "ok"}
    except Exception:
        raise HTTPException(status_code=503, detail="Database unavailable")

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
