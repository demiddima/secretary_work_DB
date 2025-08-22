# src/routers/audiences.py
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.dependencies import get_session
from src.schemas import AudiencePreviewRequest, AudiencePreviewResponse
from src.audience_sql import exec_preview, AudienceSQLValidationError
from src.models import UserSubscription

router = APIRouter(prefix="/audiences", tags=["audiences"])

# Сколько элементов максимум возвращаем в sample (остальное только в total)
_SAMPLE_CAP = 50
# Жёсткий кап на limit на уровне превью
_LIMIT_CAP = 10_000


@router.post("/preview", response_model=AudiencePreviewResponse)
async def preview(req: AudiencePreviewRequest, session: AsyncSession = Depends(get_session)):
    """
    Предпросмотр аудитории:
    - target.type == "sql": выполняем безопасную обёртку SQL и возвращаем user_id
    - target.type == "ids": используем переданные id (uniq + сохранение порядка)
    - target.type == "kind": берём по флагу подписки (news/meetings/important)
    """
    target = req.target
    limit = max(0, min(req.limit, _LIMIT_CAP))  # кап, чтобы не ушли в бездну

    if target.type == "sql":
        try:
            ids = await exec_preview(session, target.sql, limit=limit)
        except AudienceSQLValidationError as e:
            raise HTTPException(status_code=400, detail=str(e))
        return AudiencePreviewResponse(total=len(ids), sample=ids[: min(_SAMPLE_CAP, len(ids))])

    if target.type == "ids":
        # uniq + keep order
        uniq_ids = list(dict.fromkeys(int(x) for x in target.user_ids))
        return AudiencePreviewResponse(total=len(uniq_ids), sample=uniq_ids[: min(_SAMPLE_CAP, len(uniq_ids))])

    if target.type == "kind":
        kind = target.kind
        if kind not in {"news", "meetings", "important"}:
            raise HTTPException(status_code=400, detail="Unknown kind")

        flag = f"{kind}_enabled"
        # getattr гарантирует обращение к конкретному Boolean-колонке
        q = select(UserSubscription.user_id).where(getattr(UserSubscription, flag) == True)  # noqa: E712
        res = await session.execute(q)
        ids = [int(r[0]) for r in res.fetchall()]
        # uniq + keep order на всякий случай
        uniq_ids = list(dict.fromkeys(ids))
        return AudiencePreviewResponse(total=len(uniq_ids), sample=uniq_ids[: min(_SAMPLE_CAP, len(uniq_ids))])

    raise HTTPException(status_code=400, detail="Unsupported target type")
