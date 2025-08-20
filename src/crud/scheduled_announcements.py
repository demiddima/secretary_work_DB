
from .base import AsyncSession, select
from src.models import ScheduledAnnouncement
from src.schemas import ScheduledAnnouncementCreate, ScheduledAnnouncementUpdate

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
