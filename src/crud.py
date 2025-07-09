from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from sqlalchemy.exc import OperationalError
from sqlalchemy import select, delete, func, update
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException
from sqlalchemy.dialects.mysql import insert
from datetime import datetime
from . import models, schemas

from .models import (
    Chat, User, UserMembership, InviteLink, UserAlgorithmProgress, Setting, Link, Request, ReminderSetting, Notification
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
async def upsert_user(session: AsyncSession,
                      id: int,
                      username: str | None,
                      full_name: str | None,
                      terms_accepted: bool = False):
    async with session.begin():
        stmt = select(User).where(User.id == id)
        res = await session.execute(stmt)
        user = res.scalar_one_or_none()
        if user:
            user.username = username
            user.full_name = full_name
            user.terms_accepted = terms_accepted
        else:
            user = User(
                id=id,
                username=username,
                full_name=full_name,
                terms_accepted=terms_accepted
            )
            session.add(user)
    return user

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

# ---- Memberships ----
@retry_db
async def upsert_user_to_chat(session: AsyncSession, user_id: int, chat_id: int):
    async with session.begin():
        stmt = select(UserMembership).where(
            UserMembership.user_id == user_id,
            UserMembership.chat_id == chat_id
        )
        res = await session.execute(stmt)
        membership = res.scalar_one_or_none()
        if not membership:
            membership = UserMembership(user_id=user_id, chat_id=chat_id)
            session.add(membership)
    return membership

@retry_db
async def remove_user_from_chat(session: AsyncSession, user_id: int, chat_id: int):
    async with session.begin():
        await session.execute(
            delete(UserMembership)
            .where(UserMembership.user_id == user_id)
            .where(UserMembership.chat_id == chat_id)
        )

# ---- Invite Links ----
@retry_db
async def save_invite_link(
    session: AsyncSession, user_id: int, chat_id: int,
    invite_link: str, created_at, expires_at
):
    stmt = insert(InviteLink).values(
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
    # delete InviteLink entries and orphan Users without nested transaction
    subq = select(UserMembership.user_id)
    stmt = select(User.id).where(~User.id.in_(subq))
    res = await session.execute(stmt)
    user_ids = [row[0] for row in res.all()]
    if user_ids:
        await session.execute(delete(InviteLink).where(InviteLink.user_id.in_(user_ids)))
        await session.execute(delete(User).where(User.id.in_(user_ids)))
        await session.commit()
    return user_ids

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
async def get_all_offers(session: AsyncSession) -> list[models.Offer]:
    result = await session.execute(select(models.Offer))
    return result.scalars().all()


@retry_db
async def get_offer_by_id(session: AsyncSession, offer_id: int) -> models.Offer:
    obj = await session.get(models.Offer, offer_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Offer not found")
    return obj


@retry_db
async def create_offer(session: AsyncSession, data: schemas.OfferCreate) -> models.Offer:
    # Используем переданные значения
    income = data.income
    expense = data.expense
    total_sum = data.total_sum

    tax = income * 0.06
    payout = income - expense - tax
    to_you = payout * 0.335
    to_ludochat = payout * 0.335
    to_manager = payout * 0.33

    obj = models.Offer(
        name=data.name,
        total_sum=total_sum,
        income=income,
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
    data: schemas.OfferUpdate
) -> models.Offer:
    obj = await session.get(models.Offer, offer_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Offer not found")

    # Обновляем значения
    obj.name = data.name
    obj.total_sum = data.total_sum
    obj.income = data.income
    obj.expense = data.expense

    # Пересчитываем другие значения на основе income и expense
    tax = obj.income * 0.06
    payout = obj.income - obj.expense - tax
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
    data: schemas.OfferPatch
) -> models.Offer:
    obj = await session.get(models.Offer, offer_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Offer not found")

    # частично обновляем поля
    if data.name is not None:
        obj.name = data.name
    if data.income is not None:
        obj.income = data.income
    if data.expense is not None:
        obj.expense = data.expense

    # если изменился доход или расход — пересчитать всё
    if data.income is not None or data.expense is not None:
        tax = obj.income * 0.06
        payout = obj.income - obj.expense - tax
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
        delete(models.Offer).where(models.Offer.id == offer_id)
    )
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Offer not found")
    await session.commit()


# -------------------- REQUEST --------------------

@retry_db
async def get_all_requests(session: AsyncSession) -> list[models.Request]:
    result = await session.execute(select(models.Request))
    return result.scalars().all()


@retry_db
async def get_request_by_id(session: AsyncSession, request_id: int) -> models.Request:
    obj = await session.get(models.Request, request_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Request not found")
    return obj


@retry_db
async def create_request(
    session: AsyncSession,
    data: schemas.RequestCreate
) -> models.Request:
    # проверяем оффер
    offer = await session.get(models.Offer, data.offer_id)
    if not offer:
        raise HTTPException(status_code=404, detail="Offer not found")

    obj = models.Request(
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
    data: schemas.RequestUpdate
) -> models.Request:
    obj = await session.get(models.Request, request_id)
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
    data: schemas.RequestPatch
) -> models.Request:
    obj = await session.get(models.Request, request_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Request not found")

    if data.user_id is not None:
        obj.user_id = data.user_id
    if data.offer_id is not None:
        # проверяем новый оффер
        offer = await session.get(models.Offer, data.offer_id)
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
        delete(models.Request).where(models.Request.id == request_id)
    )
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Request not found")
    await session.commit()


# -------------------- REMINDER SETTINGS --------------------

@retry_db
async def get_all_reminder_settings(
    session: AsyncSession
) -> list[models.ReminderSetting]:
    result = await session.execute(select(models.ReminderSetting))
    return result.scalars().all()


@retry_db
async def get_reminder_setting_by_id(
    session: AsyncSession,
    setting_id: int
) -> models.ReminderSetting:
    obj = await session.get(models.ReminderSetting, setting_id)
    if not obj:
        raise HTTPException(status_code=404, detail="ReminderSetting not found")
    return obj


@retry_db
async def create_reminder_setting(
    session: AsyncSession,
    data: schemas.ReminderSettingsCreate
) -> models.ReminderSetting:
    # Проверяем, существует ли уже запись с таким request_id
    existing_reminder = await session.execute(
        select(models.ReminderSetting).filter(models.ReminderSetting.request_id == data.request_id)
    )
    existing_reminder = existing_reminder.scalars().first()

    if existing_reminder:
        # Если запись существует, возвращаем её (или обновляем, если нужно)
        return existing_reminder
    
    # Если записи нет, создаём новую
    obj = models.ReminderSetting(
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
    data: schemas.ReminderSettingsUpdate
) -> models.ReminderSetting:
    obj = await session.get(models.ReminderSetting, setting_id)
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
    data: schemas.ReminderSettingsPatch
) -> models.ReminderSetting:
    obj = await session.get(models.ReminderSetting, setting_id)
    if not obj:
        raise HTTPException(status_code=404, detail="ReminderSetting not found")

    if data.request_id is not None:
        req = await session.get(models.Request, data.request_id)
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
        delete(models.ReminderSetting).where(models.ReminderSetting.id == setting_id)
    )
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="ReminderSetting not found")
    await session.commit()


# -------------------- NOTIFICATION --------------------

@retry_db
async def get_all_notifications(session: AsyncSession) -> list[models.Notification]:
    result = await session.execute(select(models.Notification))
    return result.scalars().all()


@retry_db
async def get_notification_by_id(
    session: AsyncSession,
    notification_id: int
) -> models.Notification:
    obj = await session.get(models.Notification, notification_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Notification not found")
    return obj


@retry_db
async def create_notification(
    session: AsyncSession,
    data: schemas.NotificationCreate
) -> models.Notification:
    ts = data.notification_at or datetime.utcnow()
    req = await session.get(models.Request, data.request_id)
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")

    obj = models.Notification(
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
    data: schemas.NotificationUpdate
) -> models.Notification:
    obj = await session.get(models.Notification, notification_id)
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
    data: schemas.NotificationPatch
) -> models.Notification:
    obj = await session.get(models.Notification, notification_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Notification not found")

    if data.request_id is not None:
        req = await session.get(models.Request, data.request_id)
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
        delete(models.Notification).where(models.Notification.id == notification_id)
    )
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Notification not found")
    await session.commit()