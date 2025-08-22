# src/schemas.py
# commit: обновлены схемы для Request, ReminderSetting, Notification; удалены старые Reminder и Notification

from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, Literal, List
from src.utils import BROADCAST_KINDS, BROADCAST_STATUSES

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
Kind = Literal["news", "meetings", "important"]
Status = Literal["draft", "scheduled", "sending", "sent", "failed"]
TargetType = Literal["ids", "sql", "kind"]
MediaType = Literal["html", "photo", "video", "document", "album"]
DeliveryStatus = Literal["pending", "sent", "failed", "skipped"]

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
    
    
class BroadcastBase(BaseModel):
    kind: Kind = Field(description="Тип рассылки", examples=[BROADCAST_KINDS[0]])
    title: str = Field(max_length=255, description="Заголовок")
    content_html: str = Field(description="HTML-содержимое")
    status: Status = Field(default="draft", description="Статус")
    scheduled_at: Optional[datetime] = Field(default=None, description="Когда отправлять (UTC)")
    created_by: Optional[int] = Field(default=None, description="Инициатор (user_id)")

class BroadcastCreate(BroadcastBase):
    # Для создания достаточно kind, title, content_html; остальное опционально
    pass

class BroadcastUpdate(BaseModel):
    kind: Optional[Kind] = None
    title: Optional[str] = Field(default=None, max_length=255)
    content_html: Optional[str] = None
    status: Optional[Status] = None
    scheduled_at: Optional[datetime] = None
    created_by: Optional[int] = None

class BroadcastRead(BroadcastBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
    
class BroadcastTargetBase(BaseModel):
    type: TargetType

class BroadcastTargetIds(BroadcastTargetBase):
    type: Literal["ids"]
    user_ids: List[int] = Field(default_factory=list)

class BroadcastTargetSql(BroadcastTargetBase):
    type: Literal["sql"]
    sql: str

class BroadcastTargetKind(BroadcastTargetBase):
    type: Literal["kind"]
    kind: Kind

BroadcastTargetCreate = BroadcastTargetIds | BroadcastTargetSql | BroadcastTargetKind

class BroadcastTargetRead(BaseModel):
    id: int
    broadcast_id: int
    type: TargetType
    user_ids: Optional[List[int]] = None
    sql: Optional[str] = None
    kind: Optional[Kind] = None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

# --- BroadcastMedia ---
class BroadcastMediaItem(BaseModel):
    type: MediaType
    payload: dict
    position: int = 0

class BroadcastMediaPut(BaseModel):
    items: List[BroadcastMediaItem] = Field(default_factory=list)

class BroadcastMediaReadItem(BroadcastMediaItem):
    id: int
    broadcast_id: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

# --- BroadcastDelivery ---
class BroadcastDeliveryRead(BaseModel):
    id: int
    broadcast_id: int
    user_id: int
    status: DeliveryStatus
    attempts: int
    error_code: Optional[str]
    error_message: Optional[str]
    message_id: Optional[int]
    sent_at: Optional[datetime]
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

# --- Audience preview ---
class AudiencePreviewRequest(BaseModel):
    # Любой из трёх таргетов для превью
    target: BroadcastTargetCreate
    limit: int = Field(default=10000, ge=1, le=100000)  # safety cap

class AudiencePreviewResponse(BaseModel):
    total: int
    sample: List[int] = Field(default_factory=list)  # первые N id