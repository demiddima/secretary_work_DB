import sqlalchemy as sa
from sqlalchemy.orm import relationship
from sqlalchemy import (
    Column, BigInteger, String, DateTime, Boolean,
    SmallInteger, ForeignKey, UniqueConstraint, func, Integer,
    Text, Float, Enum, Index  
)
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy import Boolean, BigInteger, Column, text
from sqlalchemy.dialects.mysql import DATETIME as MySQLDateTime
from sqlalchemy.schema import Index
from sqlalchemy import JSON

from src.utils import BROADCAST_KINDS, BROADCAST_STATUSES
from src.database import Base


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
    
class Broadcast(Base):
    __tablename__ = "broadcasts"

    id = Column(Integer, primary_key=True, autoincrement=True)

    kind = Column(Enum(*BROADCAST_KINDS, name="broadcast_kind"), nullable=False)
    title = Column(String(255), nullable=False)
    content_html = Column(Text, nullable=False)

    status = Column(
        Enum(*BROADCAST_STATUSES, name="broadcast_status"),
        nullable=False,
        server_default="draft",
    )
    scheduled_at = Column(DateTime(timezone=False), nullable=True)
    created_by = Column(BigInteger, nullable=True)

    created_at = Column(DateTime(timezone=False), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=False), nullable=False, server_default=func.now(), onupdate=func.now())
    
    
class BroadcastTarget(Base):
    __tablename__ = "broadcast_targets"

    id = Column(Integer, primary_key=True, autoincrement=True)
    broadcast_id = Column(Integer, ForeignKey("broadcasts.id", ondelete="CASCADE"), nullable=False)
    type = Column(Enum("ids", "sql", "kind", name="broadcast_target_type"), nullable=False)
    user_ids_json = Column(JSON, nullable=True)
    sql_text = Column(Text, nullable=True)
    kind = Column(Enum(*BROADCAST_KINDS, name="broadcast_kind_target"), nullable=True)
    created_at = Column(DateTime(timezone=False), nullable=False, server_default=func.now())

    broadcast = relationship("Broadcast", backref="targets")


class BroadcastMedia(Base):
    __tablename__ = "broadcast_media"

    id = Column(Integer, primary_key=True, autoincrement=True)
    broadcast_id = Column(
        Integer,
        ForeignKey("broadcasts.id", ondelete="CASCADE"),
        nullable=False,
    )
    type = Column(
        Enum("html", "photo", "video", "document", "album", name="broadcast_media_type"),
        nullable=False,
    )
    payload_json = Column(JSON, nullable=False)
    position = Column(SmallInteger, nullable=False, server_default="0")
    created_at = Column(DateTime(timezone=False), nullable=False, server_default=func.now())

    broadcast = relationship("Broadcast", backref="media_items")

    # ✅ alias для Pydantic-схем
    @hybrid_property
    def payload(self):
        return self.payload_json


class BroadcastDelivery(Base):
    __tablename__ = "broadcast_deliveries"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    broadcast_id = Column(Integer, ForeignKey("broadcasts.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(BigInteger, nullable=False)
    status = Column(Enum("pending", "sent", "failed", "skipped", name="delivery_status"), nullable=False, server_default="pending")
    attempts = Column(SmallInteger, nullable=False, server_default="0")
    error_code = Column(String(64), nullable=True)
    error_message = Column(String(255), nullable=True)
    message_id = Column(BigInteger, nullable=True)
    sent_at = Column(DateTime(timezone=False), nullable=True)
    created_at = Column(DateTime(timezone=False), nullable=False, server_default=func.now())

    broadcast = relationship("Broadcast", backref="deliveries")

# Индексы (под выборки и сортировку)
Index("ix_broadcasts_status", Broadcast.status)
Index("ix_broadcasts_scheduled_at", Broadcast.scheduled_at)
Index("ix_btarget_broadcast_id", BroadcastTarget.broadcast_id)
Index("ix_bmedia_broadcast_id", BroadcastMedia.broadcast_id)
Index("ix_bdeliveries_broadcast_id", BroadcastDelivery.broadcast_id)
Index("ix_bdeliveries_broadcast_status", BroadcastDelivery.broadcast_id, BroadcastDelivery.status, mysql_length={"status": 10})