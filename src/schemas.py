# src/schemas.py
# commit: обновлены схемы для Request, ReminderSetting, Notification; удалены старые Reminder и Notification

from datetime import datetime
from pydantic import BaseModel, ConfigDict
from typing import Optional

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


# -------------------- OFFER --------------------

class OfferCreate(BaseModel):
    name: str
    income: float
    expense: float

    model_config = ConfigDict(from_attributes=True)


class OfferModel(BaseModel):
    id: int
    name: str
    income: float       # Оборот
    expense: float      # Расход
    payout: float       # Выплата
    to_you: float       # Вам
    to_ludochat: float  # Лудочат
    to_manager: float   # Менеджер
    tax: float          # Налог
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# Модель для вывода — с расчётами
class OfferModelOut(OfferModel):
    payout: float
    to_you: float
    to_ludochat: float
    to_manager: float
    tax: float


# -------------------- REQUEST --------------------

class RequestCreate(BaseModel):
    user_id: int
    offer_id: int

    model_config = ConfigDict(from_attributes=True)


class RequestModel(RequestCreate):
    id: int
    is_completed: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class RequestStatusUpdate(BaseModel):
    is_completed: bool

    model_config = ConfigDict(from_attributes=True)


# -------------------- REMINDER --------------------

class ReminderSettingsCreate(BaseModel):
    request_id: int
    first_notification_at: datetime
    frequency_hours: int

    model_config = ConfigDict(from_attributes=True)


class ReminderSettingsModel(ReminderSettingsCreate):
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# -------------------- NOTIFICATION --------------------

class NotificationCreate(BaseModel):
    request_id: int
    notification_at: Optional[datetime] = None  # если None — ставим текущую дату

    model_config = ConfigDict(from_attributes=True)


class NotificationModel(BaseModel):
    request_id: int
    notification_at: datetime
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)