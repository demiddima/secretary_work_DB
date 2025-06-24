from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.schemas import LinkVisitIn
from src.database import get_session
from src import crud

router = APIRouter(
    prefix="/links",
    tags=["links"]
)

@router.post("/visit", response_model=None)
async def increment_link_visit(
    visit: LinkVisitIn,
    session: AsyncSession = Depends(get_session)
):
    try:
        await crud.increment_link_visit(session, link_key=visit.link_key)
        return {"ok": True}
    except HTTPException as exc:
        raise exc
