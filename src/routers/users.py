import logging
from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.ext.asyncio import AsyncSession
from src.schemas import UserModel, UserUpdate
from src.database import get_session
from src import crud
from src.utils import user_to_dict  # Импортируем функцию преобразования

# Настроим логгер
logger = logging.getLogger()

router = APIRouter(
    prefix="/users",
    tags=["users"]
)

# Создание или обновление пользователя
@router.put("/{user_id}/upsert", response_model=UserModel)
async def upsert_user(
    user_id: int,
    user: UserModel,
    session: AsyncSession = Depends(get_session)
):
    try:
        # Логируем входящий запрос
        logger.info(f"[{user_id}] - [PUT /users/{user_id}/upsert] Входящий запрос для создания или обновления пользователя: {user.dict()}")

        # Обрабатываем запрос
        db_user = await crud.upsert_user(session, id=user_id, username=user.username, full_name=user.full_name)

        # Логируем исходящий ответ
        logger.info(f"[{user_id}] - [PUT /users/{user_id}/upsert] Исходящий ответ: {user_to_dict(db_user)}")
        return db_user
    except Exception as e:
        # Логируем ошибку
        logger.error(f"[{user_id}] - [PUT /users/{user_id}/upsert] Ошибка при обновлении пользователя: {str(e)}")
        raise HTTPException(status_code=500, detail="Ошибка при обновлении пользователя")

# Получить пользователя по ID
@router.get("/{user_id}", response_model=UserModel)
async def get_user(
    user_id: int,
    session: AsyncSession = Depends(get_session)
):
    try:
        # Логируем входящий запрос
        logger.info(f"[{user_id}] - [GET /users/{user_id}] Входящий запрос для получения пользователя с user_id={user_id}")

        db_user = await crud.get_user(session, id=user_id)
        if not db_user:
            raise HTTPException(status_code=404, detail="User not found")

        # Логируем исходящий ответ
        logger.info(f"[{user_id}] - [GET /users/{user_id}] Исходящий ответ: {user_to_dict(db_user)}")
        return db_user
    except HTTPException:
        raise
    except Exception as e:
        # Логируем ошибку
        logger.error(f"[{user_id}] - [GET /users/{user_id}] Ошибка при получении пользователя: {str(e)}")
        raise HTTPException(status_code=500, detail="Ошибка при получении пользователя")

# Обновление пользователя
@router.put("/{user_id}", response_model=None)
async def update_user(
    user_id: int,
    user: UserUpdate,
    session: AsyncSession = Depends(get_session)
):
    try:
        # Логируем входящий запрос
        logger.info(f"[{user_id}] - [PUT /users/{user_id}] Входящий запрос для обновления пользователя с user_id={user_id}: {user.dict()}")

        # Обрабатываем запрос
        data = {
            key: value
            for key, value in {
                "username":        user.username,
                "full_name":       user.full_name,
                "terms_accepted":  user.terms_accepted,
            }.items()
            if value is not None
        }
        await crud.update_user(session, id=user_id, **data)

        # Логируем исходящий ответ
        logger.info(f"[{user_id}] - [PUT /users/{user_id}] Исходящий ответ: {{'ok': True}}")
        return {"ok": True}
    except Exception as e:
        # Логируем ошибку
        logger.error(f"[{user_id}] - [PUT /users/{user_id}] Ошибка при обновлении пользователя: {str(e)}")
        raise HTTPException(status_code=500, detail="Ошибка при обновлении пользователя")

# Частичное обновление пользователя
@router.patch("/{user_id}", status_code=204)
async def patch_user(
    user_id: int,
    user: UserUpdate = Body(...),
    session: AsyncSession = Depends(get_session),
):
    try:
        # Логируем входящий запрос
        logger.info(f"[{user_id}] - [PATCH /users/{user_id}] Входящий запрос для частичного обновления пользователя с user_id={user_id}: {user.dict()}")

        # Обрабатываем запрос
        data = user.model_dump(exclude_unset=True)
        if not data:
            raise HTTPException(status_code=400, detail="Нет полей для обновления")
        await crud.update_user(session, id=user_id, **data)

        # Логируем исходящий ответ
        logger.info(f"[{user_id}] - [PATCH /users/{user_id}] Исходящий ответ: {{'ok': True}}")
    except Exception as e:
        # Логируем ошибку
        logger.error(f"[{user_id}] - [PATCH /users/{user_id}] Ошибка при частичном обновлении пользователя: {str(e)}")
        raise HTTPException(status_code=500, detail="Ошибка при частичном обновлении пользователя")

# Удаление пользователя
@router.delete("/{user_id}", response_model=None)
async def delete_user(
    user_id: int,
    session: AsyncSession = Depends(get_session)
):
    try:
        # Логируем входящий запрос
        logger.info(f"[{user_id}] - [DELETE /users/{user_id}] Входящий запрос для удаления пользователя с user_id={user_id}")

        await crud.delete_user(session, id=user_id)

        # Логируем исходящий ответ
        logger.info(f"[{user_id}] - [DELETE /users/{user_id}] Исходящий ответ: {{'ok': True}}")
        return {"ok": True}
    except Exception as e:
        # Логируем ошибку
        logger.error(f"[{user_id}] - [DELETE /users/{user_id}] Ошибка при удалении пользователя: {str(e)}")
        raise HTTPException(status_code=500, detail="Ошибка при удалении пользователя")
