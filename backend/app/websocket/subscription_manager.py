from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from app.models.market import FeedMode, SymbolState


class SubscriptionState(StrEnum):
    SUBSCRIBED = "SUBSCRIBED"
    UNSUBSCRIBED = "UNSUBSCRIBED"
    REJECTED = "REJECTED"


@dataclass(slots=True)
class Subscription:
    symbol: str
    feed_code: str
    mode: FeedMode = FeedMode.LTP
    symbol_state: SymbolState = SymbolState.NORMAL
    state: SubscriptionState = SubscriptionState.UNSUBSCRIBED


class SubscriptionManager:
    def __init__(self, limit: int = 1000) -> None:
        self.limit = limit
        self._items: dict[str, Subscription] = {}

    def add(self, symbol: str, feed_code: str, mode: FeedMode = FeedMode.LTP, state: SymbolState = SymbolState.NORMAL) -> Subscription:
        if len(self._items) >= self.limit and feed_code not in self._items:
            raise RuntimeError("SHAREKHAN_SUBSCRIPTION_LIMIT_REACHED")
        sub = Subscription(symbol=symbol.upper(), feed_code=feed_code, mode=mode, symbol_state=state)
        self._items[feed_code] = sub
        return sub

    def promote(self, feed_code: str, target_mode: FeedMode = FeedMode.FULL) -> Subscription | None:
        sub = self._items.get(feed_code)
        if not sub:
            return None
        sub.mode = target_mode
        sub.symbol_state = SymbolState.PROMOTED
        return sub

    def all(self) -> list[Subscription]:
        return list(self._items.values())

    def subscribed_count(self) -> int:
        return len([item for item in self._items.values() if item.state == SubscriptionState.SUBSCRIBED])
