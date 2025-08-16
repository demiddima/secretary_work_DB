from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from sqlalchemy.exc import OperationalError, IntegrityError
from sqlalchemy import select, delete, func, update
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException

from datetime import datetime

from sqlalchemy.dialects.mysql import insert as mysql_insert

from .schemas import (
    OfferCreate, OfferUpdate, OfferPatch, RequestCreate, RequestUpdate, RequestPatch, ReminderSettingsCreate, ReminderSettingsUpdate, 
    ReminderSettingsPatch, NotificationCreate, NotificationUpdate, NotificationPatch, ScheduledAnnouncementCreate, ScheduledAnnouncementUpdate
)

from .models import (
    Chat, User, UserMembership, InviteLink, UserAlgorithmProgress, Setting, Link, 
    ScheduledAnnouncement, Request, ReminderSetting, Notification, Offer
)

# Retry configuration: up to 5 attempts, exponential backoff
retry_db = retry(
    reraise=True,
    retry=retry_if_exception_type(OperationalError),
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=1, min=1, max=10),
)

# ---- Chats ----
@retry_db
async def upsert_chat(
    session: AsyncSession,
    chat_id: int,
    title: str,
    type_: str,
    added_at: datetime,               # ← принимаем added_at из запроса
):
    async with session.begin():
        stmt = select(Chat).where(Chat.id == chat_id)
        res = await session.execute(stmt)
        chat = res.scalar_one_or_none()

        if chat:
            # при апдейте тоже обновляем added_at
            chat.title = title
            chat.type = type_
            chat.added_at = added_at
        else:
            # при создании сохраняем добавленное время
            chat = Chat(
                id=chat_id,
                title=title,
                type=type_,
                added_at=added_at
            )
            session.add(chat)

    return chat

@retry_db
async def delete_chat(session: AsyncSession, chat_id: int):
    async with session.begin():
        await session.execute(delete(Chat).where(Chat.id == chat_id))

@retry_db
async def get_all_chats(session: AsyncSession):
    stmt = select(Chat.id)
    res = await session.execute(stmt)
    return [row[0] for row in res.all()]

# ---- Users ----
@retry_db
async def upsert_user(
    session: AsyncSession,
    *,
    id: int,
    username: str | None,
    full_name: str | None,
    terms_accepted: bool | None = None
) -> User:
    # если клиент не указал terms_accepted — по умолчанию вставляем False
    terms_val = False if terms_accepted is None else terms_accepted

    # INSERT ... ON DUPLICATE KEY UPDATE
    stmt = mysql_insert(User).values(
        id=id,
        username=username,
        full_name=full_name,
        terms_accepted=terms_val
    )

    # Поля, которые всегда обновляем
    update_fields: dict[str, any] = {
        "username": stmt.inserted.username,
        "full_name": stmt.inserted.full_name,
    }
    # Обновляем terms_accepted только если клиент передал его явно
    if terms_accepted is not None:
        update_fields["terms_accepted"] = stmt.inserted.terms_accepted

    stmt = stmt.on_duplicate_key_update(**update_fields)

    await session.execute(stmt)
    await session.commit()

    # Возвращаем актуальный объект из базы
    return await session.get(User, id)

@retry_db
async def get_user(session: AsyncSession, id: int):
    stmt = select(User).where(User.id == id)
    res = await session.execute(stmt)
    return res.scalar_one_or_none()

@retry_db
async def update_user(session: AsyncSession, id: int, **fields):
    async with session.begin():
        stmt = update(User).where(User.id == id).values(**fields)
        await session.execute(stmt)

@retry_db
async def delete_user(session: AsyncSession, id: int):
    async with session.begin():
        await session.execute(delete(User).where(User.id == id))

@retry_db
async def upsert_user_to_chat(session: AsyncSession, user_id: int, chat_id: int) -> UserMembership:
    stmt = select(UserMembership).where(
        UserMembership.user_id == user_id,
        UserMembership.chat_id == chat_id
    )
    res = await session.execute(stmt)
    membership = res.scalar_one_or_none()
    if membership is not None:
        return membership

    membership = UserMembership(user_id=user_id, chat_id=chat_id)
    session.add(membership)
    try:
        await session.flush()
    except IntegrityError:
        await session.rollback()
        res = await session.execute(stmt)
        membership = res.scalar_one()

    await session.commit()
    return membership

@retry_db
async def remove_user_from_chat(session: AsyncSession, user_id: int, chat_id: int):
    async with session.begin():
        await session.execute(
            delete(UserMembership)
            .where(UserMembership.user_id == user_id)
            .where(UserMembership.chat_id == chat_id)
        )
        
@retry_db
async def is_user_in_chat(
    session: AsyncSession,
    user_id: int,
    chat_id: int
) -> bool:
    """
    Возвращает True, если в таблице memberships есть запись
    для пары (user_id, chat_id), иначе False.
    """
    stmt = select(UserMembership).where(
        UserMembership.user_id == user_id,
        UserMembership.chat_id == chat_id
    )
    res = await session.execute(stmt)
    return res.scalar_one_or_none() is not None

# ---- Invite Links ----
@retry_db
async def save_invite_link(
    session: AsyncSession, user_id: int, chat_id: int,
    invite_link: str, created_at, expires_at
):
    stmt = mysql_insert(InviteLink).values(
        user_id=user_id,
        chat_id=chat_id,
        invite_link=invite_link,
        created_at=created_at,
        expires_at=expires_at
    )
    upsert_stmt = stmt.on_duplicate_key_update(
        invite_link=stmt.inserted.invite_link,
        created_at=stmt.inserted.created_at,
        expires_at=stmt.inserted.expires_at
    )
    try:
        await session.execute(upsert_stmt)
        await session.commit()
    except SQLAlchemyError:
        await session.rollback()
        raise

    result = await session.execute(
        select(InviteLink).where(
            InviteLink.user_id == user_id,
            InviteLink.chat_id == chat_id
        )
    )
    return result.scalar_one()

@retry_db
async def get_valid_invite_links(session: AsyncSession, user_id: int):
    now = func.now()
    stmt = select(InviteLink).where(
        InviteLink.user_id == user_id,
        InviteLink.expires_at > now
    )
    res = await session.execute(stmt)
    return res.scalars().all()

@retry_db
async def get_invite_links(session: AsyncSession, user_id: int):
    stmt = select(InviteLink).where(
        InviteLink.user_id == user_id
    )
    res = await session.execute(stmt)
    return res.scalars().all()

@retry_db
async def delete_invite_links(session: AsyncSession, user_id: int):
    async with session.begin():
        await session.execute(delete(InviteLink).where(InviteLink.user_id == user_id))

# ---- Algorithm Progress ----
@retry_db
async def get_user_step(session: AsyncSession, user_id: int):
    stmt = select(UserAlgorithmProgress.current_step).where(UserAlgorithmProgress.user_id == user_id)
    res = await session.execute(stmt)
    return res.scalar_one_or_none()

@retry_db
async def set_user_step(session: AsyncSession, user_id: int, step: int):
    async with session.begin():
        obj = await session.get(UserAlgorithmProgress, user_id)
        if obj:
            obj.current_step = step
        else:
            obj = UserAlgorithmProgress(user_id=user_id, current_step=step)
            session.add(obj)
    return obj

@retry_db
async def get_basic_completed(session: AsyncSession, user_id: int):
    stmt = select(UserAlgorithmProgress.basic_completed).where(UserAlgorithmProgress.user_id == user_id)
    res = await session.execute(stmt)
    return res.scalar_one_or_none()

@retry_db
async def set_basic_completed(session: AsyncSession, user_id: int, completed: bool):
    async with session.begin():
        obj = await session.get(UserAlgorithmProgress, user_id)
        if obj:
            obj.basic_completed = completed
        else:
            obj = UserAlgorithmProgress(user_id=user_id, basic_completed=completed)
            session.add(obj)
    return obj

@retry_db
async def get_advanced_completed(session: AsyncSession, user_id: int):
    stmt = select(UserAlgorithmProgress.advanced_completed).where(UserAlgorithmProgress.user_id == user_id)
    res = await session.execute(stmt)
    return res.scalar_one_or_none()

@retry_db
async def set_advanced_completed(session: AsyncSession, user_id: int, completed: bool):
    async with session.begin():
        obj = await session.get(UserAlgorithmProgress, user_id)
        if obj:
            obj.advanced_completed = completed
        else:
            obj = UserAlgorithmProgress(user_id=user_id, advanced_completed=completed)
            session.add(obj)
    return obj

@retry_db
async def clear_user_data(session: AsyncSession, user_id: int):
    async with session.begin():
        await session.execute(delete(UserAlgorithmProgress).where(UserAlgorithmProgress.user_id == user_id))

# ---- Settings & Cleanup ----
@retry_db
async def get_cleanup_cron(session: AsyncSession):
    stmt = select(Setting.value).where(Setting.id == 1)
    res = await session.execute(stmt)
    return res.scalar_one_or_none() or '0 3 * * 6'

@retry_db
async def set_cleanup_cron(session: AsyncSession, cron_str: str):
    async with session.begin():
        obj = await session.get(Setting, 1)
        if obj:
            obj.cleanup_cron = cron_str
        else:
            obj = Setting(id=1, cleanup_cron=cron_str)
            session.add(obj)
    return obj

@retry_db
async def cleanup_orphan_users(session: AsyncSession):
    # Получаем ID пользователей, которые не состоят ни в одном чате
    subq = select(UserMembership.user_id)
    stmt = select(User).where(~User.id.in_(subq))
    res = await session.execute(stmt)
    users_to_delete = res.scalars().all()

    if not users_to_delete:
        return []

    for user in users_to_delete:
        await session.delete(user)

    await session.commit()
    return [user.id for user in users_to_delete]

@retry_db
async def increment_link_visit(session: AsyncSession, link_key: str) -> Link:
    stmt = select(Link).where(Link.link_key == link_key)
    result = await session.execute(stmt)
    link = result.scalars().first()

    if not link:
        raise HTTPException(status_code=404, detail="Link not found")

    link.visits += 1
    await session.commit()
    return link

# -------------------- OFFER --------------------

@retry_db
async def get_all_offers(session: AsyncSession) -> list[Offer]:
    result = await session.execute(select(Offer))
    return result.scalars().all()


@retry_db
async def get_offer_by_id(session: AsyncSession, offer_id: int) -> Offer:
    obj = await session.get(Offer, offer_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Offer not found")
    return obj


@retry_db
async def create_offer(session: AsyncSession, data: OfferCreate) -> Offer:
    # Используем переданные значения
    total_sum = data.total_sum
    expense = data.expense

    # Применяем бизнес-логику
    tax = total_sum * 0.06  # Налог
    payout = total_sum - expense - tax  # Выплата
    to_you = payout * 0.335  # Вам
    to_ludochat = payout * 0.335  # Лудочат
    to_manager = payout * 0.33  # Менеджер

    # Создаем объект Offer
    obj = Offer(
        name=data.name,
        total_sum=total_sum,
        turnover=data.turnover,  # Переименовано с income
        expense=expense,
        payout=payout,
        tax=tax,
        to_you=to_you,
        to_ludochat=to_ludochat,
        to_manager=to_manager,
    )
    session.add(obj)
    await session.commit()
    await session.refresh(obj)
    return obj


@retry_db
async def update_offer(
    session: AsyncSession,
    offer_id: int,
    data: OfferUpdate
) -> Offer:
    obj = await session.get(Offer, offer_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Offer not found")

    # Обновляем значения
    obj.name = data.name
    obj.total_sum = data.total_sum
    obj.turnover = data.turnover  # Обновляем turnover
    obj.expense = data.expense

    # Пересчитываем другие значения на основе total_sum, expense и turnover
    tax = obj.total_sum * 0.06
    payout = obj.total_sum - obj.expense - tax
    obj.tax = tax
    obj.payout = payout
    obj.to_you = payout * 0.335
    obj.to_ludochat = payout * 0.335
    obj.to_manager = payout * 0.33

    await session.commit()
    await session.refresh(obj)
    return obj


@retry_db
async def patch_offer(
    session: AsyncSession,
    offer_id: int,
    data: OfferPatch
) -> Offer:
    obj = await session.get(Offer, offer_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Offer not found")

    # частично обновляем поля
    if data.name is not None:
        obj.name = data.name
    if data.turnover is not None:  # Переименовано с income
        obj.turnover = data.turnover
    if data.expense is not None:
        obj.expense = data.expense

    # если изменился turnover или expense — пересчитываем всё
    if data.turnover is not None or data.expense is not None:
        tax = obj.total_sum * 0.06
        payout = obj.total_sum - obj.expense - tax
        obj.tax = tax
        obj.payout = payout
        obj.to_you = payout * 0.335
        obj.to_ludochat = payout * 0.335
        obj.to_manager = payout * 0.33

    await session.commit()
    await session.refresh(obj)
    return obj


@retry_db
async def delete_offer(session: AsyncSession, offer_id: int) -> None:
    result = await session.execute(
        delete(Offer).where(Offer.id == offer_id)
    )
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Offer not found")
    await session.commit()




# -------------------- REQUEST --------------------

@retry_db
async def get_all_requests(session: AsyncSession) -> list[Request]:
    result = await session.execute(select(Request))
    return result.scalars().all()


@retry_db
async def get_request_by_id(session: AsyncSession, request_id: int) -> Request:
    obj = await session.get(Request, request_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Request not found")
    return obj


@retry_db
async def create_request(
    session: AsyncSession,
    data: RequestCreate
) -> Request:
    # проверяем оффер
    offer = await session.get(Offer, data.offer_id)
    if not offer:
        raise HTTPException(status_code=404, detail="Offer not found")

    obj = Request(
        user_id=data.user_id,
        offer_id=data.offer_id,
    )
    session.add(obj)
    await session.commit()
    await session.refresh(obj)
    return obj


@retry_db
async def update_request(
    session: AsyncSession,
    request_id: int,
    data: RequestUpdate
) -> Request:
    obj = await session.get(Request, request_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Request not found")

    # обновляем все поля
    obj.user_id = data.user_id
    obj.offer_id = data.offer_id
    obj.is_completed = data.is_completed

    await session.commit()
    await session.refresh(obj)
    return obj


@retry_db
async def patch_request(
    session: AsyncSession,
    request_id: int,
    data: RequestPatch
) -> Request:
    obj = await session.get(Request, request_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Request not found")

    if data.user_id is not None:
        obj.user_id = data.user_id
    if data.offer_id is not None:
        # проверяем новый оффер
        offer = await session.get(Offer, data.offer_id)
        if not offer:
            raise HTTPException(status_code=404, detail="Offer not found")
        obj.offer_id = data.offer_id
    if data.is_completed is not None:
        obj.is_completed = data.is_completed

    await session.commit()
    await session.refresh(obj)
    return obj


@retry_db
async def delete_request(session: AsyncSession, request_id: int) -> None:
    result = await session.execute(
        delete(Request).where(Request.id == request_id)
    )
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Request not found")
    await session.commit()


# -------------------- REMINDER SETTINGS --------------------

@retry_db
async def get_all_reminder_settings(
    session: AsyncSession
) -> list[ReminderSetting]:
    result = await session.execute(select(ReminderSetting))
    return result.scalars().all()


@retry_db
async def get_reminder_setting_by_id(
    session: AsyncSession,
    setting_id: int
) -> ReminderSetting:
    obj = await session.get(ReminderSetting, setting_id)
    if not obj:
        raise HTTPException(status_code=404, detail="ReminderSetting not found")
    return obj


@retry_db
async def create_reminder_setting(
    session: AsyncSession,
    data: ReminderSettingsCreate
) -> ReminderSetting:
    # Проверяем, существует ли уже запись с таким request_id
    existing_reminder = await session.execute(
        select(ReminderSetting).filter(ReminderSetting.request_id == data.request_id)
    )
    existing_reminder = existing_reminder.scalars().first()

    if existing_reminder:
        # Если запись существует, возвращаем её (или обновляем, если нужно)
        return existing_reminder
    
    # Если записи нет, создаём новую
    obj = ReminderSetting(
        request_id=data.request_id,
        first_notification_at=data.first_notification_at,
        frequency_hours=data.frequency_hours,
    )
    session.add(obj)
    await session.commit()
    await session.refresh(obj)
    return obj


@retry_db
async def update_reminder_setting(
    session: AsyncSession,
    setting_id: int,
    data: ReminderSettingsUpdate
) -> ReminderSetting:
    obj = await session.get(ReminderSetting, setting_id)
    if not obj:
        raise HTTPException(status_code=404, detail="ReminderSetting not found")

    obj.request_id = data.request_id
    obj.first_notification_at = data.first_notification_at
    obj.frequency_hours = data.frequency_hours

    await session.commit()
    await session.refresh(obj)
    return obj


@retry_db
async def patch_reminder_setting(
    session: AsyncSession,
    setting_id: int,
    data: ReminderSettingsPatch
) -> ReminderSetting:
    obj = await session.get(ReminderSetting, setting_id)
    if not obj:
        raise HTTPException(status_code=404, detail="ReminderSetting not found")

    if data.request_id is not None:
        req = await session.get(Request, data.request_id)
        if not req:
            raise HTTPException(status_code=404, detail="Request not found")
        obj.request_id = data.request_id
    if data.first_notification_at is not None:
        obj.first_notification_at = data.first_notification_at
    if data.frequency_hours is not None:
        obj.frequency_hours = data.frequency_hours

    await session.commit()
    await session.refresh(obj)
    return obj


@retry_db
async def delete_reminder_setting(
    session: AsyncSession,
    setting_id: int
) -> None:
    result = await session.execute(
        delete(ReminderSetting).where(ReminderSetting.id == setting_id)
    )
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="ReminderSetting not found")
    await session.commit()


# -------------------- NOTIFICATION --------------------

@retry_db
async def get_all_notifications(session: AsyncSession) -> list[Notification]:
    result = await session.execute(select(Notification))
    return result.scalars().all()


@retry_db
async def get_notification_by_id(
    session: AsyncSession,
    notification_id: int
) -> Notification:
    obj = await session.get(Notification, notification_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Notification not found")
    return obj


@retry_db
async def create_notification(
    session: AsyncSession,
    data: NotificationCreate
) -> Notification:
    ts = data.notification_at or datetime.utcnow()
    req = await session.get(Request, data.request_id)
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")

    obj = Notification(
        request_id=data.request_id,
        notification_at=ts,
    )
    session.add(obj)
    await session.commit()
    await session.refresh(obj)
    return obj


@retry_db
async def update_notification(
    session: AsyncSession,
    notification_id: int,
    data: NotificationUpdate
) -> Notification:
    obj = await session.get(Notification, notification_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Notification not found")

    obj.request_id = data.request_id
    obj.notification_at = data.notification_at

    await session.commit()
    await session.refresh(obj)
    return obj


@retry_db
async def patch_notification(
    session: AsyncSession,
    notification_id: int,
    data: NotificationPatch
) -> Notification:
    obj = await session.get(Notification, notification_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Notification not found")

    if data.request_id is not None:
        req = await session.get(Request, data.request_id)
        if not req:
            raise HTTPException(status_code=404, detail="Request not found")
        obj.request_id = data.request_id
    if data.notification_at is not None:
        obj.notification_at = data.notification_at

    await session.commit()
    await session.refresh(obj)
    return obj


@retry_db
async def delete_notification(
    session: AsyncSession,
    notification_id: int
) -> None:
    result = await session.execute(
        delete(Notification).where(Notification.id == notification_id)
    )
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Notification not found")
    await session.commit()
    
    
# -------------------- Announcement --------------------

async def create_scheduled_announcement(session: AsyncSession, data: ScheduledAnnouncementCreate) -> ScheduledAnnouncement:
    announcement = ScheduledAnnouncement(**data.dict())
    session.add(announcement)
    await session.commit()
    await session.refresh(announcement)
    return announcement


async def get_scheduled_announcements(session: AsyncSession) -> list[ScheduledAnnouncement]:
    result = await session.execute(select(ScheduledAnnouncement))
    return result.scalars().all()


async def get_scheduled_announcement(session: AsyncSession, announcement_id: int) -> ScheduledAnnouncement | None:
    result = await session.execute(
        select(ScheduledAnnouncement).where(ScheduledAnnouncement.id == announcement_id)
    )
    return result.scalar_one_or_none()


async def update_scheduled_announcement(
    session: AsyncSession, announcement_id: int, data: ScheduledAnnouncementUpdate
) -> ScheduledAnnouncement | None:
    announcement = await get_scheduled_announcement(session, announcement_id)
    if not announcement:
        return None
    for key, value in data.dict(exclude_unset=True).items():
        setattr(announcement, key, value)
    await session.commit()
    await session.refresh(announcement)
    return announcement


async def delete_scheduled_announcement(session: AsyncSession, announcement_id: int) -> bool:
    announcement = await get_scheduled_announcement(session, announcement_id)
    if not announcement:
        return False
    await session.delete(announcement)
    await session.commit()
    return True