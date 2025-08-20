# src/schemas.py
# commit: обновлены схемы для Request, ReminderSetting, Notification; удалены старые Reminder и Notification

from datetime import datetime
from pydantic import BaseModel, ConfigDict
from typing import Optional, Literal

# Существующие модели (не изменялись)

class ChatModel(BaseModel):
    id: int
    title: str
    type: str
    added_at: Optional[datetime]

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

# Рекламные
class ScheduledAnnouncementBase(BaseModel):
    name: str
    chat_id: int
    thread_id: int
    schedule: str
    model_config = ConfigDict(from_attributes=True)

class ScheduledAnnouncementCreate(ScheduledAnnouncementBase):
    pass

class ScheduledAnnouncementUpdate(BaseModel):
    name: str | None = None
    chat_id: int | None = None
    thread_id: int | None = None
    schedule: str | None = None
    last_message_id: int | None = None

    model_config = ConfigDict(from_attributes=True)

class ScheduledAnnouncementRead(ScheduledAnnouncementBase):
    id: int
    last_message_id: int | None = None

    model_config = ConfigDict(from_attributes=True)
    
    
# --- NEW: схемы для подписок ---
class UserSubscriptionModel(BaseModel):
    user_id: int
    news_enabled: bool
    meetings_enabled: bool
    important_enabled: bool

    model_config = ConfigDict(from_attributes=True)

class UserSubscriptionPut(BaseModel):
    news_enabled: bool
    meetings_enabled: bool
    important_enabled: bool

class UserSubscriptionUpdate(BaseModel):
    news_enabled: Optional[bool] = None
    meetings_enabled: Optional[bool] = None
    important_enabled: Optional[bool] = None

class ToggleKind(BaseModel):
    kind: Literal["news", "meetings", "important"]