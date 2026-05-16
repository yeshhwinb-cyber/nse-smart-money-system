from __future__ import annotations

import asyncio
import logging
from collections.abc import Awaitable, Callable
from datetime import datetime, time
from typing import Any

from app.core.settings import IST, get_settings

logger = logging.getLogger(__name__)
RestartHook = Callable[[], Awaitable[None]]


class SessionManager:
    def __init__(self) -> None:
        self.access_token: str | None = None
        self.token_status = "TOKEN_UNKNOWN"
        self.session_status = "SESSION_UNKNOWN"
        self.expires_at: datetime | None = None
        self._restart_hooks: list[RestartHook] = []
        self._task: asyncio.Task | None = None
        self._running = False

    def load_from_env(self) -> None:
        settings = get_settings()
        if settings.sharekhan_access_token:
            self.access_token = settings.sharekhan_access_token
            self.token_status = "TOKEN_ACTIVE"
            self.session_status = "SESSION_ACTIVE"
            self.expires_at = self._today_midnight()
        else:
            self.token_status = "TOKEN_MISSING"
            self.session_status = "AUTH_REQUIRED"

    def set_access_token(self, access_token: str, expires_at: datetime | None = None) -> None:
        self.access_token = access_token
        self.token_status = "TOKEN_ACTIVE"
        self.session_status = "SESSION_ACTIVE"
        self.expires_at = expires_at or self._today_midnight()

    def register_restart_hook(self, hook: RestartHook) -> None:
        self._restart_hooks.append(hook)

    async def start(self) -> None:
        self.load_from_env()
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._monitor_loop(), name="session-manager")

    async def stop(self) -> None:
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None

    def is_active(self) -> bool:
        if not self.access_token or not self.expires_at:
            return False
        return datetime.now(IST) < self.expires_at

    def health(self) -> dict[str, Any]:
        if self.access_token and self.expires_at and datetime.now(IST) >= self.expires_at:
            self.token_status = "TOKEN_EXPIRED"
            self.session_status = "AUTH_REQUIRED"
        return {
            "token_status": self.token_status,
            "session_status": self.session_status,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "active": self.is_active(),
        }

    async def _monitor_loop(self) -> None:
        while self._running:
            self.health()
            await asyncio.sleep(30)

    def _today_midnight(self) -> datetime:
        now = datetime.now(IST)
        return datetime.combine(now.date(), time.max, tzinfo=IST)


session_manager = SessionManager()
