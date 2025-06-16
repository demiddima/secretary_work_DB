from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from .database import init_db, AsyncSessionLocal
from . import crud
from pydantic import BaseModel
from typing import Optional, List

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

app = FastAPI(title="DB Service API")

@app.on_event("startup")
async def on_startup():
    await init_db()

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
@app.post("/users/", response_model=UserModel)
async def create_user(user: UserModel, session: AsyncSession = Depends(get_session)):
    res = await crud.create_user(session, user.id, user.username, user.full_name)
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

# Memberships endpoints
@app.post("/memberships/")
async def add_membership(user_id: int, chat_id: int, session: AsyncSession = Depends(get_session)):
    await crud.add_user_to_chat(session, user_id, chat_id)
    return {"status": "added"}

@app.delete("/memberships/")
async def remove_membership(user_id: int, chat_id: int, session: AsyncSession = Depends(get_session)):
    await crud.remove_user_from_chat(session, user_id, chat_id)
    return {"status": "removed"}

# Invite links endpoints
@app.post("/invite_links/", response_model=InviteLinkModel)
async def save_invite_link(user_id: int, chat_id: int, invite_link: str, created_at: str, expires_at: str, session: AsyncSession = Depends(get_session)):
    res = await crud.save_invite_link(session, user_id, chat_id, invite_link, created_at, expires_at)
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
