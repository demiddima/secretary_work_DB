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
    total_sum: float
    turnover: float  # Переименовано с income
    expense: float

    model_config = ConfigDict(from_attributes=True)


class OfferModel(BaseModel):
    id: int
    name: str
    turnover: float  # Переименовано с income
    expense: float
    payout: float
    to_you: float
    to_ludochat: float
    to_manager: float
    tax: float
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class OfferUpdate(BaseModel):
    name: str
    turnover: float  # Переименовано с income
    expense: float
    payout: float
    to_you: float
    to_ludochat: float
    to_manager: float
    tax: float

    model_config = ConfigDict(from_attributes=True)


class OfferPatch(BaseModel):
    name: Optional[str] = None
    turnover: Optional[float] = None  # Переименовано с income
    expense: Optional[float] = None
    payout: Optional[float] = None
    to_you: Optional[float] = None
    to_ludochat: Optional[float] = None
    to_manager: Optional[float] = None
    tax: Optional[float] = None

    model_config = ConfigDict(from_attributes=True)



class OfferPatch(BaseModel):
    name: Optional[str] = None
    income: Optional[float] = None
    expense: Optional[float] = None
    payout: Optional[float] = None
    to_you: Optional[float] = None
    to_ludochat: Optional[float] = None
    to_manager: Optional[float] = None
    tax: Optional[float] = None

    model_config = ConfigDict(from_attributes=True)


# -------------------- REQUEST --------------------

class RequestCreate(BaseModel):
    user_id: int
    offer_id: int

    class Config:
        from_attributes = True


class RequestModel(BaseModel):
    id: int
    user_id: int
    offer_id: int
    is_completed: bool
    created_at: datetime

    class Config:
        from_attributes = True


class RequestUpdate(BaseModel):
    user_id: int
    offer_id: int
    is_completed: bool

    class Config:
        from_attributes = True


class RequestPatch(BaseModel):
    user_id: Optional[int] = None
    offer_id: Optional[int] = None
    is_completed: Optional[bool] = None

    class Config:
        from_attributes = True


# -------------------- REMINDER SETTINGS --------------------

class ReminderSettingsCreate(BaseModel):
    request_id: int
    first_notification_at: datetime
    frequency_hours: int

    class Config:
        from_attributes = True  # Для правильной работы с SQLAlchemy объектами


class ReminderSettingsModel(BaseModel):
    id: int
    request_id: int
    first_notification_at: datetime
    frequency_hours: int
    created_at: datetime

    class Config:
        from_attributes = True


class ReminderSettingsUpdate(BaseModel):
    request_id: int
    first_notification_at: datetime
    frequency_hours: int

    class Config:
        from_attributes = True


class ReminderSettingsPatch(BaseModel):
    request_id: Optional[int] = None
    first_notification_at: Optional[datetime] = None
    frequency_hours: Optional[int] = None

    class Config:
        from_attributes = True


# -------------------- NOTIFICATION --------------------

class NotificationCreate(BaseModel):
    request_id: int
    notification_at: Optional[datetime] = None

    class Config:
        from_attributes = True  # Для правильной работы с SQLAlchemy объектами


class NotificationModel(BaseModel):
    id: int
    request_id: int
    notification_at: datetime
    created_at: datetime

    class Config:
        from_attributes = True


class NotificationUpdate(BaseModel):
    request_id: int
    notification_at: datetime

    class Config:
        from_attributes = True


class NotificationPatch(BaseModel):
    request_id: Optional[int] = None
    notification_at: Optional[datetime] = None

    class Config:
        from_attributes = True