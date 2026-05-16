from __future__ import annotations

from fastapi import APIRouter

from app.screener.lightweight_screener import lightweight_screener

router = APIRouter(prefix="/api/screener", tags=["screener"])


@router.get("/lightweight")
async def lightweight() -> dict[str, object]:
    return lightweight_screener.snapshot()
