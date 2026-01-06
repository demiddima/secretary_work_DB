# src/schemas.py
# commit: подготовка к варианту A: добавлены Out-схемы с id, сохранена совместимость с текущими In-схемами

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


# ─────────────────────────────
# Base / common
# ─────────────────────────────

class ORMBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)


# ─────────────────────────────
# Chats
# ─────────────────────────────

class ChatOut(ORMBase):
    id: int
    title: str
    type: str
    added_at: Optional[datetime] = None


# Backward-compatible name (если где-то уже импортируется ChatModel)
class ChatModel(ChatOut):
    pass


# ─────────────────────────────
# Users
# ─────────────────────────────

class UserIn(BaseModel):
    username: Optional[str] = None
    full_name: Optional[str] = None
    terms_accepted: Optional[bool] = None


# Backward-compatible name (в проекте часто UserModel используют как input)
class UserModel(UserIn):
    pass


class UserUpdate(UserIn):
    pass


class UserOut(ORMBase):
    id: int
    username: Optional[str] = None
    full_name: Optional[str] = None
    terms_accepted: bool


# ─────────────────────────────
# Invite links
# ─────────────────────────────

class InviteLinkIn(ORMBase):
    user_id: int
    chat_id: int
    invite_link: str
    created_at: datetime
    expires_at: datetime


class InviteLinkOut(ORMBase):
    id: int
    user_id: int
    chat_id: int
    invite_link: str
    created_at: datetime
    expires_at: datetime


# Backward-compatible name
class InviteLinkModel(InviteLinkOut):
    pass


# ─────────────────────────────
# Algorithm progress
# ─────────────────────────────

class AlgorithmProgressOut(ORMBase):
    user_id: int
    current_step: int
    basic_completed: bool
    advanced_completed: bool
    updated_at: Optional[datetime] = None


# Backward-compatible name
class AlgorithmProgressModel(AlgorithmProgressOut):
    pass


# ─────────────────────────────
# Links
# ─────────────────────────────

class LinkVisitIn(BaseModel):
    link_key: str


class LinkOut(ORMBase):
    id: int
    link_key: str
    resource: Optional[str] = None
    visits: int
    created_at: datetime


# ─────────────────────────────
# Mixed
# ─────────────────────────────

class UserWithChatModel(ORMBase):
    username: Optional[str] = None
    full_name: Optional[str] = None
    terms_accepted: Optional[bool] = None
    chat_id: int
