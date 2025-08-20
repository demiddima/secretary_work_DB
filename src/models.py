import sqlalchemy as sa
from sqlalchemy.orm import relationship
from sqlalchemy import (
    Column, BigInteger, String, DateTime, Boolean,
    SmallInteger, ForeignKey, UniqueConstraint, func, Integer,
    Text, Float  
)
from sqlalchemy.ext.hybrid import hybrid_property
from .database import Base
from sqlalchemy import Boolean, BigInteger, Column, text
from sqlalchemy.dialects.mysql import DATETIME as MySQLDateTime

class Chat(Base):
    __tablename__ = 'chats'

    id = Column(BigInteger, primary_key=True)
    title = Column(String(256), nullable=False)
    type = Column(String(50), nullable=False)
    added_at = Column(DateTime, server_default=func.now(), nullable=False)

class User(Base):
    __tablename__ = 'users'

    id = Column(BigInteger, primary_key=True)
    username = Column(String(255))
    full_name = Column(String(255))
    terms_accepted = Column(Boolean, nullable=False, default=False)

    memberships = relationship(
        "UserMembership",
        backref="user",
        cascade="all, delete-orphan",
        passive_deletes=True,
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

# Рекламные

class ScheduledAnnouncement(Base):
    __tablename__ = "scheduled_announcements"

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    chat_id = Column(BigInteger, nullable=False)
    thread_id = Column(Integer, nullable=False)  # message_thread_id
    last_message_id = Column(Integer, nullable=True)
    schedule = Column(String(255), nullable=False)
    
# Рассылки    

class UserSubscription(Base):
    __tablename__ = "user_subscriptions"

    user_id = Column(BigInteger, primary_key=True)  # FK → users.id (логически)
    news_enabled = Column(Boolean, nullable=False, server_default=text("0"))
    meetings_enabled = Column(Boolean, nullable=False, server_default=text("1"))
    important_enabled = Column(Boolean, nullable=False, server_default=text("1"))

    # Используем MySQL DATETIME(6) и server defaults с микросекундами
    created_at = Column(
        MySQLDateTime(fsp=6),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP(6)"),
    )
    updated_at = Column(
        MySQLDateTime(fsp=6),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP(6)"),
        # Для ON UPDATE CURRENT_TIMESTAMP(6) лучше применить в миграции через ALTER (см. ниже)
    )