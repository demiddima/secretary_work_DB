# src/models.py
# commit: удалены следы broadcasts/subscriptions; оставлены только актуальные модели из нового models.py

from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    SmallInteger,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from src.database import Base
from src.time_msk import now_msk_naive


class Chat(Base):
    __tablename__ = "chats"

    id = Column(BigInteger, primary_key=True)
    title = Column(String(256), nullable=False)
    type = Column(String(50), nullable=False)
    added_at = Column(DateTime, nullable=False, default=now_msk_naive)


class User(Base):
    __tablename__ = "users"

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
    __tablename__ = "user_memberships"

    user_id = Column(BigInteger, ForeignKey("users.id"), primary_key=True)
    chat_id = Column(BigInteger, ForeignKey("chats.id"), primary_key=True)
    joined_at = Column(DateTime, nullable=False, default=now_msk_naive)


class InviteLink(Base):
    __tablename__ = "invite_links_chats"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger)
    chat_id = Column(BigInteger)
    invite_link = Column(String(512), nullable=False)
    created_at = Column(DateTime, nullable=False)
    expires_at = Column(DateTime, nullable=False)

    __table_args__ = (
        UniqueConstraint("user_id", "chat_id", name="uq_invite_user_chat"),
    )


class Link(Base):
    __tablename__ = "links"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    link_key = Column(String(512), nullable=False, unique=True)
    resource = Column(String(255), nullable=True)
    visits = Column(Integer, nullable=False, server_default="0")
    created_at = Column(DateTime, nullable=False, default=now_msk_naive)


class UserAlgorithmProgress(Base):
    __tablename__ = "user_algorithm_progress"

    user_id = Column(BigInteger, ForeignKey("users.id"), primary_key=True)
    current_step = Column(SmallInteger, default=0, nullable=False)
    basic_completed = Column(Boolean, default=False, nullable=False)
    advanced_completed = Column(Boolean, default=False, nullable=False)
    updated_at = Column(
        DateTime,
        nullable=False,
        default=now_msk_naive,
        onupdate=now_msk_naive,
    )
