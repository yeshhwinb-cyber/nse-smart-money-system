from __future__ import annotations

from fastapi import APIRouter

from app.health.monitor import health_monitor

router = APIRouter(prefix="/api/health", tags=["health"])


@router.get("/runtime")
async def runtime_health() -> dict[str, object]:
    return await health_monitor.runtime_health()


@router.get("/db")
async def db_health() -> dict[str, object]:
    return await health_monitor.db_health()
