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
    kind: Kind


# --- Broadcast content (JSON) ---
class BroadcastContent(BaseModel):
    """
    Храним единый JSON:
      {
        "text": "<HTML-разметка>",
        "files": "file_id1,file_id2"   # через запятую
      }
    """
    text: str = Field(default="")
    files: str = Field(default="")

    @field_validator("text")
    @classmethod
    def _normalize_text(cls, v: str) -> str:
        # Пусть всегда строка; дальше парсится как HTML на стороне отправки
        return v or ""

    @field_validator("files")
    @classmethod
    def _normalize_files(cls, v: str) -> str:
        # Пустая строка, если None; пробелы подрежем
        return (v or "").strip()


# --- Broadcast ---
class BroadcastBase(BaseModel):
    kind: Kind
    title: str = Field(max_length=255)
    content: BroadcastContent
    status: Status = Field(default="draft")

    # Только расписание и флаг активности
    schedule: Optional[str] = Field(
        default=None,
        description="Формат как в scheduled_announcements: cron или 'DD.MM.YYYY,period_days,HH:MM'.",
        examples=["0 12 * * 1", "27.08.2025,3,15:00"],
    )
    enabled: bool = Field(default=True, description="Флаг активности повторяющейся рассылки.")

    created_by: Optional[int] = Field(default=None)

class BroadcastCreate(BroadcastBase):
    pass

class BroadcastUpdate(BaseModel):
    kind: Optional[Kind] = None
    title: Optional[str] = Field(default=None, max_length=255)
    content: Optional[BroadcastContent] = None
    status: Optional[Status] = None
    schedule: Optional[str] = None
    enabled: Optional[bool] = None
    created_by: Optional[int] = None

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


# --- Audience: PREVIEW ---
class AudiencePreviewRequest(BaseModel):
    target: BroadcastTargetCreate
    limit: int = Field(default=10000, ge=1, le=100000)

class AudiencePreviewResponse(BaseModel):
    total: int
    sample: List[int] = Field(default_factory=list)


# --- Audience: RESOLVE ---
class AudienceResolveRequest(BaseModel):
    target: BroadcastTargetCreate
    # None = без лимита
    limit: Optional[int] = Field(default=None)

class AudienceResolveResponse(BaseModel):
    total: int
    ids: List[int] = Field(default_factory=list)


# --- Delivery materialize/report ---
class DeliveryMaterializeRequest(BaseModel):
    # Явный список id…
    ids: Optional[List[int]] = None
    # …или target (ids|kind|sql)
    target: Optional[BroadcastTargetCreate] = None
    # None = без лимита (берём все id)
    limit: Optional[int] = Field(default=None)

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
