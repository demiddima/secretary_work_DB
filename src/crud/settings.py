
from .base import retry_db, AsyncSession, select, HTTPException
from src.models import Setting, User, UserMembership, Link

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
