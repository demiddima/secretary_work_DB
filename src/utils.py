# src/utils.py
from sqlalchemy.inspection import inspect

# Функция для преобразования SQLAlchemy модели в словарь
def model_to_dict(model):
    if model is None:
        return {}
    # Получаем все атрибуты объекта через inspect
    return {column: getattr(model, column) for column in inspect(model).attrs.keys()}

# Преобразование Chat в словарь
def chat_to_dict(chat):
    return {
        "id": chat.id,
        "title": chat.title,
        "type": chat.type,
        "added_at": chat.added_at
    }

# Преобразование User в словарь
def user_to_dict(user):
    return {
        "id": user.id,
        "username": user.username,
        "full_name": user.full_name,
        "terms_accepted": user.terms_accepted
    }

# Преобразование AlgorithmProgress в словарь
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

# Преобразование LinkVisitIn в словарь
def link_visit_to_dict(link_visit):
    return {
        "link_key": link_visit.link_key
    }


# Рекламный
def scheduled_announcement_to_dict(announcement):
    return {
        "id": announcement.id,
        "name": announcement.name,
        "chat_id": announcement.chat_id,
        "thread_id": announcement.thread_id,
        "schedule": announcement.schedule,
        "last_message_id": announcement.last_message_id
    }
    
# --- NEW: утилита для подписок ---
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