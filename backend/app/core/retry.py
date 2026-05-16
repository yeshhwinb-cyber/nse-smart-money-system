from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from typing import TypeVar

T = TypeVar("T")


async def retry_async(
    fn: Callable[[], Awaitable[T]],
    *,
    attempts: int = 5,
    initial_delay: float = 0.5,
    max_delay: float = 15.0,
) -> T:
    delay = initial_delay
    last_exc: Exception | None = None
    for _ in range(attempts):
        try:
            return await fn()
        except Exception as exc:
            last_exc = exc
            await asyncio.sleep(delay)
            delay = min(max_delay, delay * 2)
    assert last_exc is not None
    raise last_exc
