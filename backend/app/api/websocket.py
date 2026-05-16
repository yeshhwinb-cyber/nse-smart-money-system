from __future__ import annotations

from pydantic import BaseModel
from fastapi import APIRouter

from app.websocket.sharekhan_ws import sharekhan_ws_service

router = APIRouter(prefix="/api/websocket", tags=["websocket"])


class SubscribePayload(BaseModel):
    symbol: str
    feed_code: str
    mode: str = "ltp"


@router.get("/status")
async def websocket_status() -> dict[str, object]:
    return sharekhan_ws_service.health()


@router.post("/start")
async def websocket_start() -> dict[str, object]:
    await sharekhan_ws_service.start()
    return {"status": "STARTED", **sharekhan_ws_service.health()}


@router.post("/stop")
async def websocket_stop() -> dict[str, object]:
    await sharekhan_ws_service.stop()
    return {"status": "STOPPED"}


@router.post("/subscribe")
async def websocket_subscribe(payload: SubscribePayload) -> dict[str, object]:
    await sharekhan_ws_service.subscribe(payload.symbol, payload.feed_code, payload.mode)
    return {"status": "OK", "symbol": payload.symbol.upper(), "feed_code": payload.feed_code, "mode": payload.mode}
