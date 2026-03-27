from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Query

from app.services.table_service import table_service

router = APIRouter(prefix="/history", tags=["history"])


@router.get("")
def get_history(
    ch: Optional[int] = Query(default=None, description="Filter by table channel"),
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
) -> list[dict]:
    return table_service.get_history(ch=ch, limit=limit, offset=offset)
