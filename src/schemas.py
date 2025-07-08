# src/schemas.py
# commit: replaced string timestamps with datetime types for proper serialization

from datetime import datetime
from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from uuid import UUID

class ChatModel(BaseModel):
    id: int
    title: str
    type: str
    added_at: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)

class UserModel(BaseModel):
    username: Optional[str] = None
    full_name: Optional[str] = None
    terms_accepted: Optional[bool] = None  # теперь тоже опционально

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
    updated_at: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)

class LinkVisitIn(BaseModel):
    link_key: str

    model_config = ConfigDict(from_attributes=True)
    
class SettingModel(BaseModel):
    id: int
    value: str
    updated_at: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)


class ReminderCreate(BaseModel):
    internal_request_id: UUID
    telegram_user_id: int
    first_notification_at: datetime
    frequency_hours: int
    offer_name: str
    is_offer_completed: bool = False
    offer_payout: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class ReminderModel(ReminderCreate):
    created_at: datetime


class NotificationCreate(BaseModel):
    internal_request_id: UUID
    telegram_user_id: int

    model_config = ConfigDict(from_attributes=True)


class NotificationModel(NotificationCreate):
    id: int
    created_at: datetime
