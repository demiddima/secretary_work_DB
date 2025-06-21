from sqlalchemy import (
    Column, BigInteger, String, DateTime, Boolean,
    SmallInteger, ForeignKey, UniqueConstraint, func, Integer
)
from .database import Base

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
    resource = Column(String(255), nullable=True)
    visits     = Column(Integer, nullable=False, server_default='0')
    created_at = Column(DateTime, server_default=func.now(), nullable=False)


class UserAlgorithmProgress(Base):
    __tablename__ = 'user_algorithm_progress'

    user_id = Column(BigInteger, ForeignKey('users.id'), primary_key=True)
    current_step = Column(SmallInteger, default=0, nullable=False)
    basic_completed = Column(Boolean, default=False, nullable=False)
    advanced_completed = Column(Boolean, default=False, nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
    
class Setting(Base):
    __tablename__ = 'settings'
    id = Column(BigInteger, primary_key=True)
    cleanup_cron = Column(String(100), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())