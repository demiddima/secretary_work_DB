from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.schemas import AlgorithmProgressModel
from src.database import get_session
from src import crud

router = APIRouter(
    prefix="/algo",
    tags=["algorithm"]
)

@router.get("/{user_id}", response_model=AlgorithmProgressModel)
async def get_user_progress(
    user_id: int,
    session: AsyncSession = Depends(get_session)
):
    step = await crud.get_user_step(session, user_id=user_id)
    basic = await crud.get_basic_completed(session, user_id=user_id)
    advanced = await crud.get_advanced_completed(session, user_id=user_id)
    updated_at = None  # если надо, можно сделать отдельный crud метод для updated_at
    return AlgorithmProgressModel(
        user_id=user_id,
        current_step=step or 0,
        basic_completed=basic or False,
        advanced_completed=advanced or False,
        updated_at=updated_at
    )

@router.put("/{user_id}/step", response_model=None)
async def set_user_step(
    user_id: int,
    step: int,
    session: AsyncSession = Depends(get_session)
):
    await crud.set_user_step(session, user_id=user_id, step=step)
    return {"ok": True}

@router.put("/{user_id}/basic", response_model=None)
async def set_basic_completed(
    user_id: int,
    completed: bool,
    session: AsyncSession = Depends(get_session)
):
    await crud.set_basic_completed(session, user_id=user_id, completed=completed)
    return {"ok": True}

@router.put("/{user_id}/advanced", response_model=None)
async def set_advanced_completed(
    user_id: int,
    completed: bool,
    session: AsyncSession = Depends(get_session)
):
    await crud.set_advanced_completed(session, user_id=user_id, completed=completed)
    return {"ok": True}

@router.delete("/{user_id}", response_model=None)
async def clear_user_data(
    user_id: int,
    session: AsyncSession = Depends(get_session)
):
    await crud.clear_user_data(session, user_id=user_id)
    return {"ok": True}
