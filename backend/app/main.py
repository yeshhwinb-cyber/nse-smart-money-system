from __future__ import annotations

from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.auth import router as auth_router
from app.api.health import router as health_router
from app.api.market import router as market_router
from app.api.screener import router as screener_router
from app.api.websocket import router as websocket_router
from app.auth.session_manager import session_manager
from app.core.database import db
from app.core.logging import configure_logging
from app.core.settings import get_settings
from app.events.bus import event_bus
from app.screener.lightweight_screener import lightweight_screener
from app.websocket.sharekhan_ws import sharekhan_ws_service

configure_logging()
settings = get_settings()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI):
    try:
        await db.connect()
    except Exception as exc:
        logger.error("Database startup connection failed: %s", exc)
    await event_bus.start()
    await lightweight_screener.start()
    session_manager.register_restart_hook(sharekhan_ws_service.restart)
    await session_manager.start()
    await sharekhan_ws_service.start()
    try:
        yield
    finally:
        await sharekhan_ws_service.stop()
        await session_manager.stop()
        await event_bus.stop()
        await db.close()


app = FastAPI(title=settings.app_name, version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin, "http://127.0.0.1:5173", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(health_router)
app.include_router(websocket_router)
app.include_router(market_router)
app.include_router(screener_router)


@app.get("/health")
async def health() -> dict[str, object]:
    return {"status": "OK", "app": settings.app_name, "phase": "PHASE_1_FOUNDATION"}
