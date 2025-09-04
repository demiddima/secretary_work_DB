# src/routers/ads.py
# commit: feat(routers): /ads и /ads-random-branches — CRUD + upsert; лог в стиле scheduled_announcements
import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.dependencies import get_session
from src import schemas
from src.crud import ads as crud

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ads", tags=["ads"])


@router.post("/", response_model=schemas.AdRead)
async def create_ad(data: schemas.AdCreate, session: AsyncSession = Depends(get_session)):
    try:
        res = await crud.create_ad(session, data)
        logger.info(f"[POST /ads] создано ad id={res.id}")
        return res
    except Exception as e:
        logger.error(f"[POST /ads] ошибка: {e}")
        raise HTTPException(status_code=500, detail="Ошибка создания объявления")


@router.get("/", response_model=list[schemas.AdRead])
async def list_ads(session: AsyncSession = Depends(get_session)):
    try:
        res = await crud.get_ads(session)
        logger.info(f"[GET /ads] total={len(res)}")
        return res
    except Exception as e:
        logger.error(f"[GET /ads] ошибка: {e}")
        raise HTTPException(status_code=500, detail="Ошибка получения списка")


@router.get("/{ad_id}", response_model=schemas.AdRead)
async def read_ad(ad_id: int, session: AsyncSession = Depends(get_session)):
    try:
        res = await crud.get_ad(session, ad_id)
        if not res:
            raise HTTPException(status_code=404, detail="Объявление не найдено")
        logger.info(f"[GET /ads/{ad_id}] ok")
        return res
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[GET /ads/{ad_id}] ошибка: {e}")
        raise HTTPException(status_code=500, detail="Ошибка получения объявления")


@router.patch("/{ad_id}", response_model=schemas.AdRead)
async def update_ad(ad_id: int, data: schemas.AdUpdate, session: AsyncSession = Depends(get_session)):
    try:
        res = await crud.update_ad(session, ad_id, data)
        if not res:
            raise HTTPException(status_code=404, detail="Объявление не найдено")
        logger.info(f"[PATCH /ads/{ad_id}] ok")
        return res
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[PATCH /ads/{ad_id}] ошибка: {e}")
        raise HTTPException(status_code=500, detail="Ошибка обновления объявления")


@router.delete("/{ad_id}", response_model=dict)
async def delete_ad(ad_id: int, session: AsyncSession = Depends(get_session)):
    try:
        ok = await crud.delete_ad(session, ad_id)
        if not ok:
            raise HTTPException(status_code=404, detail="Объявление не найдено")
        logger.info(f"[DELETE /ads/{ad_id}] ok")
        return {"ok": True}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[DELETE /ads/{ad_id}] ошибка: {e}")
        raise HTTPException(status_code=500, detail="Ошибка удаления объявления")


# --- Random branches ---

rb_router = APIRouter(prefix="/ads-random-branches", tags=["ads_random"])


@rb_router.post("/", response_model=schemas.RandomBranchRead)
async def upsert_branch(data: schemas.RandomBranchCreate, session: AsyncSession = Depends(get_session)):
    try:
        res = await crud.upsert_random_branch(session, data)
        logger.info(f"[POST /ads-random-branches] upsert chat={res.chat_id} thread={res.thread_id}")
        return res
    except Exception as e:
        logger.error(f"[POST /ads-random-branches] ошибка: {e}")
        raise HTTPException(status_code=500, detail="Ошибка сохранения настроек ветки")


@rb_router.get("/", response_model=list[schemas.RandomBranchRead])
async def list_branches(session: AsyncSession = Depends(get_session)):
    try:
        res = await crud.list_random_branches(session)
        logger.info(f"[GET /ads-random-branches] total={len(res)}")
        return res
    except Exception as e:
        logger.error(f"[GET /ads-random-branches] ошибка: {e}")
        raise HTTPException(status_code=500, detail="Ошибка получения списка веток")


@rb_router.get("/{branch_id}", response_model=schemas.RandomBranchRead)
async def read_branch(branch_id: int, session: AsyncSession = Depends(get_session)):
    try:
        res = await crud.get_random_branch(session, branch_id)
        if not res:
            raise HTTPException(status_code=404, detail="Ветка не найдена")
        logger.info(f"[GET /ads-random-branches/{branch_id}] ok")
        return res
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[GET /ads-random-branches/{branch_id}] ошибка: {e}")
        raise HTTPException(status_code=500, detail="Ошибка получения ветки")


@rb_router.patch("/{branch_id}", response_model=schemas.RandomBranchRead)
async def update_branch(branch_id: int, data: schemas.RandomBranchUpdate, session: AsyncSession = Depends(get_session)):
    try:
        res = await crud.update_random_branch(session, branch_id, data)
        if not res:
            raise HTTPException(status_code=404, detail="Ветка не найдена")
        logger.info(f"[PATCH /ads-random-branches/{branch_id}] ok")
        return res
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[PATCH /ads-random-branches/{branch_id}] ошибка: {e}")
        raise HTTPException(status_code=500, detail="Ошибка обновления ветки")


@rb_router.delete("/{branch_id}", response_model=dict)
async def delete_branch(branch_id: int, session: AsyncSession = Depends(get_session)):
    try:
        ok = await crud.delete_random_branch(session, branch_id)
        if not ok:
            raise HTTPException(status_code=404, detail="Ветка не найдена")
        logger.info(f"[DELETE /ads-random-branches/{branch_id}] ok")
        return {"ok": True}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[DELETE /ads-random-branches/{branch_id}] ошибка: {e}")
        raise HTTPException(status_code=500, detail="Ошибка удаления ветки")
