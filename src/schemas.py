# src/schemas.py
# commit: обновлены схемы для Request, ReminderSetting, Notification; удалены старые Reminder и Notification
# + МСК: scheduled_at теперь явно описано как «МСК, naive», и нормализуется в МСК через валидаторы

from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field, field_validator
from typing import Optional, Literal, List
from src.utils import BROADCAST_KINDS, BROADCAST_STATUSES
from src.time_msk import to_msk_naive  # нормализация в МСК (naive)

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

# --- Подписки ---
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


# --- Broadcast (сокращено) ---
class BroadcastBase(BaseModel):
    kind: Kind
    title: str = Field(max_length=255)
    content_html: str
    status: Status = Field(default="draft")
    scheduled_at: Optional[datetime] = Field(
        default=None,
        description="Когда отправлять (МСК, Europe/Moscow). Наивное время без TZ.",
        examples=["2025-08-23 14:30:00"],
    )
    created_by: Optional[int] = Field(default=None)

    @field_validator("scheduled_at")
    @classmethod
    def _normalize_scheduled_at(cls, v: Optional[datetime]) -> Optional[datetime]:
        if v is None:
            return v
        return to_msk_naive(v)

class BroadcastCreate(BroadcastBase):
    pass

class BroadcastUpdate(BaseModel):
    kind: Optional[Kind] = None
    title: Optional[str] = Field(default=None, max_length=255)
    content_html: Optional[str] = None
    status: Optional[Status] = None
    scheduled_at: Optional[datetime] = None
    created_by: Optional[int] = None

    @field_validator("scheduled_at")
    @classmethod
    def _normalize_scheduled_at(cls, v: Optional[datetime]) -> Optional[datetime]:
        if v is None:
            return v
        return to_msk_naive(v)

class BroadcastRead(BroadcastBase):
    id: int
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)

# --- Targets ---
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

# --- Media (сокращено) ---
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

# --- Delivery (сокращено) ---
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

# --- Audience: PREVIEW (как было) ---
class AudiencePreviewRequest(BaseModel):
    target: BroadcastTargetCreate
    limit: int = Field(default=10000, ge=1, le=100000)

class AudiencePreviewResponse(BaseModel):
    total: int
    sample: List[int] = Field(default_factory=list)

# --- Audience: RESOLVE (новое) ---
class AudienceResolveRequest(BaseModel):
    target: BroadcastTargetCreate
    # общий верх: 500k, чтобы исключить «бесконечную» выборку
    limit: int = Field(default=200_000, ge=1, le=500_000)

class AudienceResolveResponse(BaseModel):
    total: int
    ids: List[int] = Field(default_factory=list)
# --- Delivery ---
class DeliveryMaterializeRequest(BaseModel):
    # Любой из источников:
    # 1) ids — прямой список
    ids: Optional[List[int]] = None
    # 2) target — ids|kind|sql (как в BroadcastTargetCreate)
    target: Optional[BroadcastTargetCreate] = None
    # 3) limit — защитный верх (<= 500k)
    limit: int = Field(default=200_000, ge=1, le=500_000)

class DeliveryMaterializeResponse(BaseModel):
    total: int = 0      # сколько user_id было в источнике (после uniq/limit)
    created: int = 0    # сколько реально вставили
    existed: int = 0    # сколько уже было

class DeliveryReportItem(BaseModel):
    user_id: int
    status: DeliveryStatus
    message_id: Optional[int] = None
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    sent_at: Optional[datetime] = None
    attempt_inc: int = Field(default=1, ge=0, le=100)

class DeliveryReportRequest(BaseModel):
    items: List[DeliveryReportItem] = Field(default_factory=list)

class DeliveryReportResponse(BaseModel):
    processed: int = 0
    updated: int = 0
    inserted: int = 0