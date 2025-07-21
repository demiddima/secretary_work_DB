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

# Преобразование Offer в словарь
def offer_to_dict(offer):
    return {
        "id": offer.id,
        "name": offer.name,
        "total_sum": offer.total_sum,
        "turnover": offer.turnover,
        "expense": offer.expense,
        "payout": offer.payout,
        "to_you": offer.to_you,
        "to_ludochat": offer.to_ludochat,
        "to_manager": offer.to_manager,
        "tax": offer.tax,
        "created_at": offer.created_at
    }

# Преобразование Request в словарь
def request_to_dict(request):
    """Преобразует SQLAlchemy объект запроса в словарь"""
    return {
        "id": request.id,
        "user_id": request.user_id,
        "offer_id": request.offer_id,
        "is_completed": request.is_completed,
        "created_at": request.created_at
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

def notification_to_dict(notification):
    """Преобразует SQLAlchemy объект уведомления в словарь"""
    return {
        "id": notification.id,
        "request_id": notification.request_id,
        "message": notification.message,
        "created_at": notification.created_at,
        "updated_at": notification.updated_at
    }

def reminder_settings_to_dict(reminder_settings):
    """Преобразует SQLAlchemy объект настройки напоминания в словарь"""
    return {
        "id": reminder_settings.id,
        "user_id": reminder_settings.user_id,
        "message": reminder_settings.message,
        "created_at": reminder_settings.created_at,
        "updated_at": reminder_settings.updated_at
    }
