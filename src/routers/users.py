from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.schemas import UserModel
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
    user: UserModel,                            # <-- теперь принимаем UserUpdate
    session: AsyncSession = Depends(get_session)
):
    # dict только с теми полями, которые реально пришли в запросе
    update_data = user.dict(exclude_unset=True)
    if not update_data:
        raise HTTPException(status_code=400, detail="No fields provided for update")
    await crud.update_user(session, id=user_id, **update_data)
    return {"ok": True}

@router.delete("/{user_id}", response_model=None)
async def delete_user(
    user_id: int,
    session: AsyncSession = Depends(get_session)
):
    await crud.delete_user(session, id=user_id)
    return {"ok": True}
