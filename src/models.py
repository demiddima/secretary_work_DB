import sqlalchemy as sa
from sqlalchemy.orm import relationship
from sqlalchemy import (
    Column, BigInteger, String, DateTime, Boolean,
    SmallInteger, ForeignKey, UniqueConstraint, func, Integer,
    Text, Float  
)
from sqlalchemy.ext.hybrid import hybrid_property
from .database import Base

class Chat(Base):
    __tablename__ = 'chats'

    id = Column(BigInteger, primary_key=True)
    title = Column(String(256), nullable=False)
    type = Column(String(50), nullable=False)
    added_at = Column(DateTime, server_default=func.now(), nullable=False)

class User(Base):
    __tablename__ = 'users'

    id             = Column(BigInteger, primary_key=True)
    username       = Column(String(255))
    full_name      = Column(String(255))
    terms_accepted = Column(Boolean, nullable=False, default=False)

    memberships = relationship(
        "UserMembership",
        backref="user",
        cascade="all, delete-orphan",
    )

    invite_links = relationship(
        "InviteLink",
        primaryjoin="User.id == foreign(InviteLink.user_id)",
        backref="user",
        cascade="all, delete-orphan",
    )

    progress = relationship(
        "UserAlgorithmProgress",
        backref="user",
        cascade="all, delete-orphan",
    )

    requests = relationship(
        "Request",
        backref="user",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

class UserMembership(Base):
    __tablename__ = 'user_memberships'

    user_id = Column(BigInteger, ForeignKey('users.id'), primary_key=True)
    chat_id = Column(BigInteger, ForeignKey('chats.id'), primary_key=True)
    joined_at = Column(DateTime, server_default=func.now(), nullable=False)

class InviteLink(Base):
    __tablename__ = 'invite_links_chats'

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger)
    chat_id = Column(BigInteger)
    invite_link = Column(String(512), nullable=False)
    created_at = Column(DateTime, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    __table_args__ = (
        UniqueConstraint('user_id', 'chat_id', name='uq_invite_user_chat'),
    )
    
class Link(Base):
    __tablename__ = 'links'

    id         = Column(BigInteger, primary_key=True, autoincrement=True)
    link_key   = Column(String(512), nullable=False, unique=True)
    resource   = Column(String(255), nullable=True)
    visits     = Column(Integer, nullable=False, server_default='0')
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

class UserAlgorithmProgress(Base):
    __tablename__ = 'user_algorithm_progress'

    user_id           = Column(BigInteger, ForeignKey('users.id'), primary_key=True)
    current_step      = Column(SmallInteger, default=0, nullable=False)
    basic_completed   = Column(Boolean, default=False, nullable=False)
    advanced_completed= Column(Boolean, default=False, nullable=False)
    updated_at        = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
    
class Setting(Base):
    __tablename__ = 'settings'
    id         = Column(BigInteger, primary_key=True)
    value      = Column(String(100), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

# Модели для Узнавайка


class Request(Base):
    __tablename__ = 'requests'

    id           = Column(Integer, primary_key=True, autoincrement=True)
    user_id      = Column(BigInteger, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    offer_id     = Column(Integer, ForeignKey('offers.id', ondelete='CASCADE'), nullable=False)
    is_completed = Column(Boolean, nullable=False, server_default=sa.text('0'))
    created_at   = Column(DateTime, server_default=func.now(), nullable=False)

    reminders = relationship(
        "ReminderSetting",
        backref="request",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    notifications = relationship(
        "Notification",
        backref="request",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

class ReminderSetting(Base):
    __tablename__ = 'reminder_settings'

    id = Column(Integer, primary_key=True, autoincrement=True)  # Добавляем поле id
    request_id = Column(Integer, ForeignKey('requests.id', ondelete='CASCADE'), nullable=False)
    first_notification_at = Column(DateTime, nullable=False)
    frequency_hours = Column(Integer, nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)


class Notification(Base):
    __tablename__ = 'notifications'

    id = Column(Integer, primary_key=True, autoincrement=True)  # Добавляем поле id
    request_id = Column(Integer, ForeignKey('requests.id', ondelete='CASCADE'), nullable=False)
    notification_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)


class Offer(Base):
    __tablename__ = 'offers'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(128), nullable=False)
    total_sum = Column(Float, nullable=False)  # Общая сумма
    turnover = Column(Float, nullable=False)   # Оборот (переименовано с income)
    expense = Column(Float, nullable=False)    # Расход

    payout = Column(Float, nullable=False)     # Выплата
    to_you = Column(Float, nullable=False)     # Вам
    to_ludochat = Column(Float, nullable=False)  # Лудочат
    to_manager = Column(Float, nullable=False)  # Менеджер
    tax = Column(Float, nullable=False)        # Налог

    created_at = Column(DateTime, server_default=func.now(), nullable=False)

