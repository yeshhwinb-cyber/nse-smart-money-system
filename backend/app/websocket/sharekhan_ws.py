from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime
from typing import Any

import websockets

from app.auth.session_manager import session_manager
from app.core.database import db
from app.core.settings import IST, get_settings
from app.events.bus import event_bus
from app.market.normalizer import SharekhanNormalizer
from app.models.market import MarketEvent
from app.repositories.market_repository import market_repository
from app.websocket.subscription_manager import SubscriptionManager, SubscriptionState

logger = logging.getLogger(__name__)


class SharekhanWebSocketService:
    def __init__(self) -> None:
        settings = get_settings()
        self.subscriptions = SubscriptionManager(limit=settings.max_ws_subscriptions)
        self.normalizer = SharekhanNormalizer()
        self.connection_state = "DISCONNECTED"
        self.websocket_status = "DISCONNECTED"
        self.ticks_received = 0
        self.last_tick_at: datetime | None = None
        self.last_heartbeat_at: datetime | None = None
        self.last_error_code: str | None = None
        self.last_error_message: str | None = None
        self._task: asyncio.Task | None = None
        self._running = False
        self._ws: websockets.ClientConnection | None = None
        self._db_status_warning_logged = False

    async def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._run_loop(), name="sharekhan-websocket")

    async def stop(self) -> None:
        self._running = False
        if self._ws:
            await self._ws.close()
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None

    async def restart(self) -> None:
        await self.stop()
        await self.start()

    async def subscribe(self, symbol: str, feed_code: str, mode: str = "ltp") -> None:
        sub = self.subscriptions.add(symbol, feed_code)
        sub.mode = mode  # type: ignore[assignment]
        if self._ws and self.connection_state == "CONNECTED":
            await self._send_feed_subscription(feed_code, str(mode))

    def health(self) -> dict[str, Any]:
        return {
            "connection_state": self.connection_state,
            "websocket_status": self.websocket_status,
            "subscription_count": self.subscriptions.subscribed_count(),
            "ticks_received": self.ticks_received,
            "last_tick_at": self.last_tick_at.isoformat() if self.last_tick_at else None,
            "last_heartbeat_at": self.last_heartbeat_at.isoformat() if self.last_heartbeat_at else None,
            "last_error_code": self.last_error_code,
            "last_error_message": self.last_error_message,
        }

    async def _run_loop(self) -> None:
        retry = 1.0
        while self._running:
            if not session_manager.is_active():
                self.connection_state = "AUTH_REQUIRED"
                await self._persist_status()
                await asyncio.sleep(5)
                continue
            try:
                await self._connect_and_listen()
                retry = 1.0
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                self.connection_state = "RECONNECTING"
                self.websocket_status = "ERROR"
                self.last_error_code = exc.__class__.__name__
                self.last_error_message = str(exc)
                logger.exception("Sharekhan websocket loop failed")
                await self._persist_status()
                await asyncio.sleep(retry)
                retry = min(30.0, retry * 2)

    async def _connect_and_listen(self) -> None:
        settings = get_settings()
        url = f"{settings.sharekhan_websocket_url}?ACCESS_TOKEN={session_manager.access_token}&API_KEY={settings.sharekhan_api_key}"
        self.connection_state = "CONNECTING"
        await self._persist_status()
        async with websockets.connect(url, ping_interval=None, close_timeout=5) as ws:
            self._ws = ws
            self.connection_state = "CONNECTED"
            self.websocket_status = "CONNECTED"
            await self._send_json({"action": "subscribe", "key": ["feed", "ack"], "value": [""]})
            if settings.sharekhan_customer_id:
                await self._send_json({"action": "ack", "key": [""], "value": [settings.sharekhan_customer_id]})
            for sub in self.subscriptions.all():
                await self._send_feed_subscription(sub.feed_code, sub.mode.value if hasattr(sub.mode, "value") else str(sub.mode))
                sub.state = SubscriptionState.SUBSCRIBED
            await self._persist_status()
            async for raw in ws:
                await self._handle_message(raw)

    async def _send_feed_subscription(self, feed_code: str, mode: str) -> None:
        await self._send_json({"action": "feed", "key": [mode], "value": [feed_code]})

    async def _send_json(self, payload: dict[str, Any]) -> None:
        if not self._ws:
            return
        await self._ws.send(json.dumps(payload, separators=(",", ":")))

    async def _handle_message(self, raw: str | bytes) -> None:
        self.last_heartbeat_at = datetime.now(IST)
        if raw == "heartbeat":
            await self._persist_status()
            return
        payload = json.loads(raw)
        ticks = self.normalizer.normalize_message(payload)
        for tick in ticks:
            self.ticks_received += 1
            self.last_tick_at = tick.event_time
            try:
                async for conn in db.acquire():
                    await market_repository.insert_tick(conn, tick)
                    await market_repository.upsert_snapshot(conn, tick)
            except Exception as exc:
                logger.warning("Tick DB persistence skipped symbol=%s error=%s", tick.symbol, exc)
            await event_bus.publish(MarketEvent(event_type="tick", channel="market.tick", symbol=tick.symbol, payload=tick, created_at=datetime.now(IST)))
        await self._persist_status()

    async def _persist_status(self) -> None:
        try:
            async for conn in db.acquire():
                await market_repository.provider_status(
                    conn,
                    "SHAREKHAN",
                    status="OK" if self.connection_state == "CONNECTED" else self.connection_state,
                    connection_state=self.connection_state,
                    token_status=session_manager.token_status,
                    session_status=session_manager.session_status,
                    websocket_status=self.websocket_status,
                    subscription_count=self.subscriptions.subscribed_count(),
                    ticks_received=self.ticks_received,
                    last_tick_at=self.last_tick_at,
                    last_heartbeat_at=self.last_heartbeat_at,
                    last_error_code=self.last_error_code,
                    last_error_message=self.last_error_message,
                )
            self._db_status_warning_logged = False
        except Exception as exc:
            if not self._db_status_warning_logged:
                logger.warning("Provider status persistence skipped: %s", exc)
                self._db_status_warning_logged = True


sharekhan_ws_service = SharekhanWebSocketService()
