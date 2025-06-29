from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.schemas import UserModel, UserUpdate
from src.database import get_session
from src import crud

router = APIRouter(
    prefix="/users",
    tags=["users"]
)

@router.put("/{user_id}/upsert", response_model=UserModel)
async def upsert_user(
    user_id: int,
    user: UserModel,
    session: AsyncSession = Depends(get_session)
):
    db_user = await crud.upsert_user(session, id=user_id, username=user.username, full_name=user.full_name)
    return db_user

@router.get("/{user_id}", response_model=UserModel)
async def get_user(
    user_id: int,
    session: AsyncSession = Depends(get_session)
):
    db_user = await crud.get_user(session, id=user_id)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user

@router.put("/{user_id}", response_model=None)
async def update_user(
    user_id: int,
    user: UserUpdate,                     # <-- здесь UserUpdate
    session: AsyncSession = Depends(get_session)
):
    # собираем только те пары (ключ:значение), что не None
    data = {
        k: v
        for k, v in {
            "username":        user.username,
            "full_name":       user.full_name,
            "terms_accepted":  user.terms_accepted,
        }.items()
        if v is not None
    }
    await crud.update_user(session, id=user_id, **data)
    return {"ok": True}

@router.delete("/{user_id}", response_model=None)
async def delete_user(
    user_id: int,
    session: AsyncSession = Depends(get_session)
):
    await crud.delete_user(session, id=user_id)
    return {"ok": True}
