# src/schemas.py
# commit: обновлены схемы для Request, ReminderSetting, Notification; удалены старые Reminder и Notification
# + МСК: scheduled_at теперь явно описано как «МСК, naive», и нормализуется в МСК через валидаторы

from datetime import datetime, date, time
from pydantic import BaseModel, ConfigDict, Field, field_validator
from typing import Optional, Literal, List

ScheduleType = Literal["cron", "n_days", "random"]

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

class AdButton(BaseModel):
    enabled: bool = False
    label: Optional[str] = None
    url: Optional[str] = None

    @field_validator("label")
    @classmethod
    def _label_if_enabled(cls, v, info):
        if info.data.get("enabled") and not v:
            raise ValueError("label обязателен при enabled=true")
        return v

    @field_validator("url")
    @classmethod
    def _url_if_enabled(cls, v, info):
        if info.data.get("enabled") and not v:
            raise ValueError("url обязателен при enabled=true")
        return v

    model_config = ConfigDict(from_attributes=True)


class AdButton(BaseModel):
    enabled: bool = False
    label: Optional[str] = None
    url: Optional[str] = None

    @field_validator("label")
    @classmethod
    def _label_if_enabled(cls, v, info):
        if info.data.get("enabled") and not v:
            raise ValueError("label обязателен при enabled=true")
        return v

    @field_validator("url")
    @classmethod
    def _url_if_enabled(cls, v, info):
        if info.data.get("enabled") and not v:
            raise ValueError("url обязателен при enabled=true")
        return v

    model_config = ConfigDict(from_attributes=True)


class AdContent(BaseModel):
    text: str = Field(default="")
    files: str = Field(default="")
    button: AdButton = Field(default_factory=AdButton)
    link_preview: bool = False

    @field_validator("files")
    @classmethod
    def _normalize_files(cls, v: str) -> str:
        return (v or "").strip()

    model_config = ConfigDict(from_attributes=True)


class AdBase(BaseModel):
    title: str = Field(max_length=255)

    chat_id: int
    thread_id: Optional[int] = None

    # ВАЖНО: теперь только content_json
    content_json: AdContent

    schedule_type: ScheduleType
    schedule_cron: Optional[str] = Field(default=None, description="Cron для schedule_type=cron (5 полей)")

    n_days_start_date: Optional[date] = None
    n_days_time: Optional[time] = None
    n_days_interval: Optional[int] = Field(default=None, ge=1, le=365)

    enabled: bool = True
    delete_previous: bool = True
    dedupe_minute: bool = True

    auto_delete_ttl_hours: Optional[int] = Field(default=None, ge=1, le=168)
    auto_delete_cron: Optional[str] = Field(default=None, description="Cron для автоудаления")

    created_by: Optional[int] = None
    last_message_id: Optional[int] = None

    # --- мягкий парсинг дат/времени для N-дней ---
    @field_validator("n_days_start_date", mode="before")
    @classmethod
    def _parse_start_date(cls, v):
        if v is None:
            return v
        if isinstance(v, date):
            return v
        if isinstance(v, str):
            s = v.strip()
            # поддержим и ISO, и ДД.ММ.ГГГГ
            for fmt in ("%Y-%m-%d", "%d.%m.%Y"):
                try:
                    return datetime.strptime(s, fmt).date()
                except ValueError:
                    pass
        raise ValueError("n_days_start_date: ожидается дата в формате YYYY-MM-DD или ДД.ММ.ГГГГ")

    @field_validator("n_days_time", mode="before")
    @classmethod
    def _parse_time(cls, v):
        if v is None:
            return v
        if isinstance(v, time):
            return v
        if isinstance(v, str):
            s = v.strip()
            # поддержим HH:MM и HH:MM:SS
            for fmt in ("%H:%M", "%H:%M:%S"):
                try:
                    return datetime.strptime(s, fmt).time()
                except ValueError:
                    pass
        raise ValueError("n_days_time: ожидается время в формате HH:MM или HH:MM:SS")

    model_config = ConfigDict(from_attributes=True)


class AdCreate(AdBase):
    model_config = ConfigDict(from_attributes=True)


class AdUpdate(BaseModel):
    title: Optional[str] = None

    chat_id: Optional[int] = None
    thread_id: Optional[int] = None

    content_json: Optional[AdContent] = None

    schedule_type: Optional[ScheduleType] = None
    schedule_cron: Optional[str] = None

    n_days_start_date: Optional[date] = None
    n_days_time: Optional[time] = None
    n_days_interval: Optional[int] = Field(default=None, ge=1, le=365)

    enabled: Optional[bool] = None
    delete_previous: Optional[bool] = None
    dedupe_minute: Optional[bool] = None

    auto_delete_ttl_hours: Optional[int] = Field(default=None, ge=1, le=168)
    auto_delete_cron: Optional[str] = None

    created_by: Optional[bool] = None
    last_message_id: Optional[int] = None

    # те же валидаторы для частичного апдейта
    @field_validator("n_days_start_date", mode="before")
    @classmethod
    def _parse_start_date_update(cls, v):
        return AdBase._parse_start_date(v)

    @field_validator("n_days_time", mode="before")
    @classmethod
    def _parse_time_update(cls, v):
        return AdBase._parse_time(v)

    model_config = ConfigDict(from_attributes=True)


class AdRead(AdBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# --- Random branch ---

class RandomBranchBase(BaseModel):
    chat_id: int
    thread_id: Optional[int] = None
    window_from: time
    window_to: time
    rebuild_time: time
    enabled: bool = True

    model_config = ConfigDict(from_attributes=True)


class RandomBranchCreate(RandomBranchBase):
    pass


class RandomBranchUpdate(BaseModel):
    window_from: Optional[time] = None
    window_to: Optional[time] = None
    rebuild_time: Optional[time] = None
    enabled: Optional[bool] = None

    model_config = ConfigDict(from_attributes=True)


class RandomBranchRead(RandomBranchBase):
    id: int