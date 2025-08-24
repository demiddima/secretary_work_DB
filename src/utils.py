# src/utils.py
from sqlalchemy.inspection import inspect
from datetime import datetime


# Функция для преобразования SQLAlchemy модели в словарь
def model_to_dict(model):
    if model is None:
        return {}
    return {column: getattr(model, column) for column in inspect(model).attrs.keys()}

def chat_to_dict(chat):
    return {
        "id": chat.id,
        "title": chat.title,
        "type": chat.type,
        "added_at": chat.added_at
    }

def user_to_dict(user):
    return {
        "id": user.id,
        "username": user.username,
        "full_name": user.full_name,
        "terms_accepted": user.terms_accepted
    }

def algorithm_progress_to_dict(algorithm_progress):
    return {
        "user_id": algorithm_progress.user_id,
        "current_step": algorithm_progress.current_step,
        "basic_completed": algorithm_progress.basic_completed,
        "advanced_completed": algorithm_progress.advanced_completed,
        "updated_at": algorithm_progress.updated_at
    }

def invite_link_to_dict(invite_link):
    return {
        "id": invite_link.id,
        "user_id": invite_link.user_id,
        "chat_id": invite_link.chat_id,
        "invite_link": invite_link.invite_link,
        "created_at": invite_link.created_at,
        "expires_at": invite_link.expires_at
    }

def link_visit_to_dict(link_visit):
    return {"link_key": link_visit.link_key}

def scheduled_announcement_to_dict(announcement):
    return {
        "id": announcement.id,
        "name": announcement.name,
        "chat_id": announcement.chat_id,
        "thread_id": announcement.thread_id,
        "schedule": announcement.schedule,
        "last_message_id": announcement.last_message_id
    }

# --- NEW: подписки ---
def user_subscription_to_dict(s):
    if s is None:
        return {}
    return {
        "user_id": s.user_id,
        "news_enabled": bool(s.news_enabled),
        "meetings_enabled": bool(s.meetings_enabled),
        "important_enabled": bool(s.important_enabled),
        "created_at": s.created_at,
        "updated_at": s.updated_at,
    }

# --- NEW: broadcasts (шапка) ---
def broadcast_to_dict(b):
    if b is None:
        return {}
    return {
        "id": b.id,
        "kind": b.kind,
        "title": b.title,
        "content": b.content,
        "status": b.status,
        "scheduled_at": b.scheduled_at,
        "created_by": b.created_by,
        "created_at": b.created_at,
        "updated_at": b.updated_at,
    }

# --- NEW: broadcast target/media/delivery ---
def broadcast_target_to_dict(t):
    if t is None:
        return {}
    return {
        "id": t.id,
        "broadcast_id": t.broadcast_id,
        "type": t.type,                # 'ids' | 'sql' | 'kind'
        "user_ids": t.user_ids_json,   # list[int] | None
        "sql": t.sql_text,             # str | None
        "kind": t.kind,                # 'news' | 'meetings' | 'important' | None
        "created_at": t.created_at,
    }

def broadcast_media_to_dict(m):
    if m is None:
        return {}
    return {
        "id": m.id,
        "broadcast_id": m.broadcast_id,
        "type": m.type,              # 'html' | 'photo' | 'video' | 'document' | 'album'
        "payload": m.payload_json,   # dict
        "position": m.position,
        "created_at": m.created_at,
    }

def broadcast_delivery_to_dict(d):
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

BROADCAST_KINDS = ("news", "meetings", "important")
BROADCAST_STATUSES = ("draft", "scheduled", "sending", "sent", "failed")
