from __future__ import annotations

from pydantic import BaseModel
from fastapi import APIRouter

from app.historical.historical_service import historical_service
from app.market.scripmaster_service import scripmaster_service

router = APIRouter(prefix="/api/market", tags=["market"])


class HistoricalSyncPayload(BaseModel):
    symbol: str
    timeframe: str = "daily"


@router.post("/scripmaster/sync")
async def sync_scripmaster() -> dict[str, object]:
    return await scripmaster_service.sync_daily()


@router.post("/historical/sync")
async def sync_historical(payload: HistoricalSyncPayload) -> dict[str, object]:
    return await historical_service.sync_symbol(payload.symbol, payload.timeframe)
