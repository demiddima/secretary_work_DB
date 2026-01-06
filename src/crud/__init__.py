# src/crud/__init__.py
# commit: восстановлен верхнеуровневый API пакета crud (экспорт функций), добавлен links.increment_link_visit

from .base import retry_db

from .users import (
    upsert_user,
    get_user,
    update_user,
    delete_user,
    upsert_user_to_chat,
    remove_user_from_chat,
    is_user_in_chat,
    list_memberships_by_chat,
    upsert_user_and_membership,
)

from .chats import (
    upsert_chat,
    delete_chat,
    get_all_chat_ids,
)

from .invite_links import (
    save_invite_link,
    get_valid_invite_links,
    get_invite_links,
    delete_invite_links,
)

from .algorithm_progress import (
    get_progress,
    set_user_step,
    set_basic_completed,
    set_advanced_completed,
    clear_user_data,
)

from .links import (
    increment_link_visit,
)

__all__ = [
    "retry_db",
    # users
    "upsert_user",
    "get_user",
    "update_user",
    "delete_user",
    "upsert_user_to_chat",
    "remove_user_from_chat",
    "is_user_in_chat",
    "list_memberships_by_chat",
    "upsert_user_and_membership",
    # chats
    "upsert_chat",
    "delete_chat",
    "get_all_chat_ids",
    # invite links
    "save_invite_link",
    "get_valid_invite_links",
    "get_invite_links",
    "delete_invite_links",
    # algorithm progress
    "get_progress",
    "set_user_step",
    "set_basic_completed",
    "set_advanced_completed",
    "clear_user_data",
    # links
    "increment_link_visit",
]
