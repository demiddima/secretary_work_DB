# src/crud/links.py
# commit: добавлен CRUD для links (increment_link_visit) под текущую модель Link

from __future__ import annotations

from fastapi import HTTPException

from .base import AsyncSession, retry_db, update
from src.models import Link


@retry_db
async def increment_link_visit(session: AsyncSession, *, link_key: str) -> None:
    async with session.begin():
        stmt = (
            update(Link)
            .where(Link.link_key == link_key)
            .values(visits=Link.visits + 1)
        )
        res = await session.execute(stmt)

        if not res.rowcount:
            raise HTTPException(status_code=404, detail="Link not found")
