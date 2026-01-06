# src/schemas.py
# commit: удалены все схемы для legacy-моделей (settings/subscriptions/broadcasts/ads/audiences/deliveries/scheduled_announcements/random branches)

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class ChatModel(BaseModel):
    id: int
    title: str
    type: str
    added_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class UserModel(BaseModel):
    username: Optional[str] = None
    full_name: Optional[str] = None
    terms_accepted: Optional[bool] = None

    model_config = ConfigDict(from_attributes=True)


class UserUpdate(BaseModel):
    username: Optional[str] = None
    full_name: Optional[str] = None
    terms_accepted: Optional[bool] = None

    model_config = ConfigDict(from_attributes=True)


class InviteLinkIn(BaseModel):
    user_id: int
    chat_id: int
    invite_link: str
    created_at: datetime
    expires_at: datetime

    model_config = ConfigDict(from_attributes=True)


class InviteLinkModel(BaseModel):
    id: int
    user_id: int
    chat_id: int
    invite_link: str
    created_at: datetime
    expires_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AlgorithmProgressModel(BaseModel):
    user_id: int
    current_step: int
    basic_completed: bool
    advanced_completed: bool
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class LinkVisitIn(BaseModel):
    link_key: str

    model_config = ConfigDict(from_attributes=True)


class UserWithChatModel(BaseModel):
    username: Optional[str] = None
    full_name: Optional[str] = None
    terms_accepted: Optional[bool] = None
    chat_id: int

    model_config = ConfigDict(from_attributes=True)
