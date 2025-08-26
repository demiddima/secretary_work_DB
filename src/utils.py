# src/utils.py
"""
Утилиты сериализации и общие константы.
Важно: здесь определены перечисления BROADCAST_KINDS/BROADCAST_STATUSES,
которые используются моделями и схемами.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Optional, List

from sqlalchemy.inspection import inspect


# --- Enums -------------------------------------------------------------------

BROADCAST_KINDS = ("news", "meetings", "important")
BROADCAST_STATUSES = ("draft", "scheduled", "sending", "sent", "failed")


# --- Generic -----------------------------------------------------------------

def model_to_dict(model: Any) -> Dict[str, Any]:
    """
    Универсальный дамп SQLAlchemy-модели в dict через инспекцию.
    Подходит для простых случаев, где не нужна тонкая настройка.
    """
    if model is None:
        return {}
    return {attr.key: getattr(model, attr.key) for attr in inspect(model).mapper.column_attrs}


# --- Specific mappers --------------------------------------------------------

def chat_to_dict(chat) -> Dict[str, Any]:
    return {
        "id": chat.id,
        "title": chat.title,
        "type": chat.type,
        "added_at": chat.added_at,
    }


def user_to_dict(u) -> Dict[str, Any]:
    return {
        "id": u.id,
        "username": u.username,
        "full_name": u.full_name,
        "terms_accepted": bool(u.terms_accepted),
    }


def invite_link_to_dict(link) -> Dict[str, Any]:
    return {
        "id": link.id,
        "user_id": link.user_id,
        "chat_id": link.chat_id,
        "invite_link": link.invite_link,
        "created_at": link.created_at,
        "expires_at": link.expires_at,
    }


def algorithm_progress_to_dict(p) -> Dict[str, Any]:
    return {
        "user_id": p.user_id,
        "current_step": p.current_step,
        "basic_completed": bool(p.basic_completed),
        "advanced_completed": bool(p.advanced_completed),
        "updated_at": p.updated_at,
    }


def setting_to_dict(s) -> Dict[str, Any]:
    return {
        "id": s.id,
        "value": s.value,
        "updated_at": s.updated_at,
    }


def link_to_dict(l) -> Dict[str, Any]:
    return {
        "id": l.id,
        "link_key": l.link_key,
        "resource": l.resource,
        "visits": l.visits,
        "created_at": l.created_at,
    }


def scheduled_announcement_to_dict(announcement) -> Dict[str, Any]:
    return {
        "id": announcement.id,
        "name": announcement.name,
        "chat_id": announcement.chat_id,
        "thread_id": announcement.thread_id,
        "schedule": announcement.schedule,
        "last_message_id": announcement.last_message_id,
    }


def user_subscription_to_dict(s) -> Dict[str, Any]:
    if s is None:
        return {}
    return {
        "user_id": s.user_id,
        "news_enabled": bool(s.news_enabled),
        "meetings_enabled": bool(s.meetings_enabled),
        "important_enabled": bool(s.important_enabled),
        "created_at": getattr(s, "created_at", None),
        "updated_at": getattr(s, "updated_at", None),
    }


def broadcast_to_dict(b) -> Dict[str, Any]:
    if b is None:
        return {}
    return {
        "id": b.id,
        "kind": b.kind,
        "title": b.title,
        "content": b.content,
        "status": b.status,
        "schedule": getattr(b, "schedule", None),
        "enabled": bool(getattr(b, "enabled", True)),
        "created_by": b.created_by,
        "created_at": b.created_at,
        "updated_at": b.updated_at,
    }


def broadcast_target_to_dict(t) -> Dict[str, Any]:
    if t is None:
        return {}
    return {
        "id": t.id,
        "broadcast_id": t.broadcast_id,
        "type": t.type,  # 'ids' | 'sql' | 'kind'
        "user_ids": t.user_ids_json,
        "sql": t.sql_text,
        "kind": t.kind,
        "created_at": t.created_at,
    }


def delivery_to_dict(d) -> Dict[str, Any]:
    if d is None:
        return {}
    return {
        "id": d.id,
        "broadcast_id": d.broadcast_id,
        "user_id": d.user_id,
        "status": d.status,          # 'pending' | 'sent' | 'failed' | 'skipped'
        "attempts": d.attempts,
        "error_code": d.error_code,
        "error_message": d.error_message,
        "message_id": d.message_id,
        "sent_at": d.sent_at,
        "created_at": d.created_at,
    }
