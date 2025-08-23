# src/routers/audiences.py
from __future__ import annotations

from typing import List
import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.dependencies import get_session
from src.models import UserSubscription
from src.schemas import (
    AudiencePreviewRequest,
    AudiencePreviewResponse,
    AudienceResolveRequest,
    AudienceResolveResponse,
)
from src.audience_sql import exec_preview, AudienceSQLValidationError

router = APIRouter(prefix="/audiences", tags=["audiences"])
logger = logging.getLogger(__name__)

# --- лимиты ---
_SAMPLE_CAP = 50          # сколько id максимум возвращаем в sample превью
_PREVIEW_LIMIT_CAP = 10_000
_RESOLVE_LIMIT_CAP = 500_000


def _cap(n: int, hi: int) -> int:
    return max(0, min(int(n), int(hi)))


def _uniq_keep_order(ids: List[int], limit: int | None = None) -> List[int]:
    """uniq + keep order + опциональный лимит."""
    out: List[int] = []
    seen = set()
    lim = int(limit) if limit else None
    for x in ids:
        try:
            uid = int(x)
        except Exception:
            continue
        if uid <= 0 or uid in seen:
            continue
        seen.add(uid)
        out.append(uid)
        if lim is not None and len(out) >= lim:
            break
    return out


@router.post("/preview", response_model=AudiencePreviewResponse)
async def preview(req: AudiencePreviewRequest, session: AsyncSession = Depends(get_session)):
    """
    Предпросмотр аудитории: sql | ids | kind.
    На вход логируем тип и лимит; на выход — только итоги.
    """
    try:
        target = req.target
        limit = _cap(req.limit, _PREVIEW_LIMIT_CAP)
        logger.info(f"[POST /audiences/preview] Предпросмотр аудитории (вход): type={target.type}, limit={limit}")

        if target.type == "sql":
            try:
                ids = await exec_preview(session, target.sql, limit=limit)
            except AudienceSQLValidationError as e:
                raise HTTPException(status_code=400, detail=str(e))
            ids = _uniq_keep_order(ids, limit)
            resp = AudiencePreviewResponse(total=len(ids), sample=ids[:_SAMPLE_CAP])
            logger.info(
                f"[POST /audiences/preview] Возвращён предпросмотр (total={resp.total}, sample_len={len(resp.sample)})"
            )
            return resp

        if target.type == "ids":
            uniq_ids = _uniq_keep_order(list(target.user_ids), limit)
            resp = AudiencePreviewResponse(total=len(uniq_ids), sample=uniq_ids[:_SAMPLE_CAP])
            logger.info(
                f"[POST /audiences/preview] Возвращён предпросмотр (total={resp.total}, sample_len={len(resp.sample)})"
            )
            return resp

        if target.type == "kind":
            kind = target.kind
            if kind not in {"news", "meetings", "important"}:
                raise HTTPException(status_code=400, detail="Unknown kind")
            flag = f"{kind}_enabled"
            q = select(UserSubscription.user_id).where(getattr(UserSubscription, flag) == True)  # noqa: E712
            if limit:
                q = q.limit(limit)
            res = await session.execute(q)
            rows = [int(r[0]) for r in res.fetchall()]
            uniq_ids = _uniq_keep_order(rows, limit)
            resp = AudiencePreviewResponse(total=len(uniq_ids), sample=uniq_ids[:_SAMPLE_CAP])
            logger.info(
                f"[POST /audiences/preview] Возвращён предпросмотр (total={resp.total}, sample_len={len(resp.sample)})"
            )
            return resp

        raise HTTPException(status_code=400, detail="Unsupported target type")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[POST /audiences/preview] Ошибка при предпросмотре аудитории: {e}")
        raise HTTPException(status_code=500, detail="Ошибка при предпросмотре аудитории")


@router.post("/resolve", response_model=AudienceResolveResponse)
async def resolve(req: AudienceResolveRequest, session: AsyncSession = Depends(get_session)):
    """
    Полный (ограниченный лимитами) список id аудитории для реальной отправки.
    Логируем только тип/лимит на входе и итоговые количества на выходе.
    """
    try:
        target = req.target
        limit = _cap(req.limit, _RESOLVE_LIMIT_CAP)
        logger.info(f"[POST /audiences/resolve] Полная материализация аудитории (вход): type={target.type}, limit={limit}")

        if target.type == "sql":
            try:
                ids = await exec_preview(session, target.sql, limit=limit)
            except AudienceSQLValidationError as e:
                raise HTTPException(status_code=400, detail=str(e))
            ids = _uniq_keep_order(ids, limit)
            resp = AudienceResolveResponse(total=len(ids), ids=ids)
            logger.info(f"[POST /audiences/resolve] Возвращён список id (total={resp.total})")
            return resp

        if target.type == "ids":
            uniq_ids = _uniq_keep_order(list(target.user_ids), limit)
            resp = AudienceResolveResponse(total=len(uniq_ids), ids=uniq_ids)
            logger.info(f"[POST /audiences/resolve] Возвращён список id (total={resp.total})")
            return resp

        if target.type == "kind":
            kind = target.kind
            if kind not in {"news", "meetings", "important"}:
                raise HTTPException(status_code=400, detail="Unknown kind")
            flag = f"{kind}_enabled"
            q = select(UserSubscription.user_id).where(getattr(UserSubscription, flag) == True)  # noqa: E712
            if limit:
                q = q.limit(limit)
            res = await session.execute(q)
            rows = [int(r[0]) for r in res.fetchall()]
            uniq_ids = _uniq_keep_order(rows, limit)
            resp = AudienceResolveResponse(total=len(uniq_ids), ids=uniq_ids)
            logger.info(f"[POST /audiences/resolve] Возвращён список id (total={resp.total})")
            return resp

        raise HTTPException(status_code=400, detail="Unsupported target type")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[POST /audiences/resolve] Ошибка при полной материализации аудитории: {e}")
        raise HTTPException(status_code=500, detail="Ошибка при материализации аудитории")
