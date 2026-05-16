from __future__ import annotations

import asyncio
import logging
from collections import defaultdict
from collections.abc import Awaitable, Callable

from app.models.market import MarketEvent

logger = logging.getLogger(__name__)
Handler = Callable[[MarketEvent], Awaitable[None]]


class EventBus:
    def __init__(self) -> None:
        self._channels: dict[str, list[Handler]] = defaultdict(list)
        self._queue: asyncio.Queue[MarketEvent] = asyncio.Queue(maxsize=100_000)
        self._task: asyncio.Task | None = None
        self._running = False

    def subscribe(self, channel: str, handler: Handler) -> None:
        self._channels[channel].append(handler)

    async def publish(self, event: MarketEvent) -> None:
        await self._queue.put(event)

    async def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._dispatch_loop(), name="event-bus")

    async def stop(self) -> None:
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None

    async def _dispatch_loop(self) -> None:
        while self._running:
            event = await self._queue.get()
            handlers = [*self._channels.get(event.channel, []), *self._channels.get("*", [])]
            for handler in handlers:
                try:
                    await handler(event)
                except Exception:
                    logger.exception("Event handler failed channel=%s type=%s", event.channel, event.event_type)


event_bus = EventBus()
