import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from ..dependencies import get_session
from .. import crud, schemas
from ..utils import scheduled_announcement_to_dict

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/scheduled-announcements",
    tags=["scheduled_announcements"]
)


@router.post("/", response_model=schemas.ScheduledAnnouncementRead)
async def create_announcement(
    data: schemas.ScheduledAnnouncementCreate,
    session: AsyncSession = Depends(get_session),
):
    try:
        logger.info(
            f"[POST /scheduled-announcements/] "
            f"Создание объявления с именем '{data.name}', schedule: '{data.schedule}', "
            f"next_announcements: '{data.next_announcements}', "
            f"chat_id: {data.chat_id}, thread_id: {data.thread_id}"
        )
        return await crud.create_scheduled_announcement(session, data)
    except Exception as e:
        logger.error(f"[POST /scheduled-announcements/] Ошибка при создании объявления: {e}")
        raise HTTPException(status_code=500, detail="Ошибка при создании объявления")


@router.get("/", response_model=list[schemas.ScheduledAnnouncementRead])
async def read_announcements(
    session: AsyncSession = Depends(get_session),
):
    try:
        announcements = await crud.get_scheduled_announcements(session)
        logger.info(f"[GET /scheduled-announcements/] Запрошен список объявлений — всего {len(announcements)} записей")
        return announcements
    except Exception as e:
        logger.error(f"[GET /scheduled-announcements/] Ошибка при получении списка объявлений: {e}")
        raise HTTPException(status_code=500, detail="Ошибка при получении объявлений")


@router.get("/{announcement_id}", response_model=schemas.ScheduledAnnouncementRead)
async def read_announcement(
    announcement_id: int,
    session: AsyncSession = Depends(get_session),
):
    try:
        result = await crud.get_scheduled_announcement(session, announcement_id)
        if not result:
            raise HTTPException(status_code=404, detail="Объявление не найдено")
        logger.info(
            f"[GET /scheduled-announcements/{announcement_id}] Получены данные по объявлению: "
            f"{scheduled_announcement_to_dict(result)}"
        )
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[GET /scheduled-announcements/{announcement_id}] Ошибка при получении объявления: {e}")
        raise HTTPException(status_code=500, detail="Ошибка при получении объявления")


@router.patch("/{announcement_id}", response_model=schemas.ScheduledAnnouncementRead)
async def update_announcement(
    announcement_id: int,
    data: schemas.ScheduledAnnouncementUpdate,
    session: AsyncSession = Depends(get_session),
):
    try:
        logger.info(
            f"[PATCH /scheduled-announcements/{announcement_id}] "
            f"Запрос на обновление объявления: {data.dict(exclude_none=True)}"
        )
        result = await crud.update_scheduled_announcement(session, announcement_id, data)
        if not result:
            raise HTTPException(status_code=404, detail="Объявление не найдено")
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[PATCH /scheduled-announcements/{announcement_id}] Ошибка при обновлении объявления: {e}")
        raise HTTPException(status_code=500, detail="Ошибка при обновлении объявления")


@router.delete("/{announcement_id}", response_model=dict)
async def delete_announcement(
    announcement_id: int,
    session: AsyncSession = Depends(get_session),
):
    try:
        result = await crud.delete_scheduled_announcement(session, announcement_id)
        if not result:
            raise HTTPException(status_code=404, detail="Объявление не найдено")
        logger.info(
            f"[DELETE /scheduled-announcements/{announcement_id}] "
            f"Объявление успешно удалено"
        )
        return {"ok": True}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[DELETE /scheduled-announcements/{announcement_id}] Ошибка при удалении объявления: {e}")
        raise HTTPException(status_code=500, detail="Ошибка при удалении объявления")
