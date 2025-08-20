# src/crud/__init__.py

from .base import retry_db  # утилиты/декораторы

# Экспорт существующих CRUD-модулей (оставь как у тебя было)
from .users import *
from .chats import *
from .invite_links import *
from .algorithm_progress import *
from .settings import *
from .scheduled_announcements import *

# NEW: обязательно экспортируем подписки,
# иначе в роутере `from src import crud` не увидит функций
from .subscriptions import *
