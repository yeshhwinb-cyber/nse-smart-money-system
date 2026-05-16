from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any

from app.events.bus import event_bus
from app.models.market import MarketEvent, NormalizedTick, SymbolState


@dataclass
class SymbolRuntimeState:
    symbol: str
    state: SymbolState = SymbolState.NORMAL
    last_price: Decimal | None = None
    recent_qty: deque[int] = field(default_factory=lambda: deque(maxlen=30))
    volume_spike_score: Decimal = Decimal("0")
    reason: list[str] = field(default_factory=list)


class LightweightScreener:
    def __init__(self) -> None:
        self.symbols: dict[str, SymbolRuntimeState] = {}
        self.started = False

    async def start(self) -> None:
        if self.started:
            return
        event_bus.subscribe("market.tick", self.on_tick)
        self.started = True

    async def on_tick(self, event: MarketEvent) -> None:
        if not isinstance(event.payload, NormalizedTick):
            return
        tick = event.payload
        state = self.symbols.setdefault(tick.symbol, SymbolRuntimeState(symbol=tick.symbol))
        qty = tick.ltq or 0
        state.recent_qty.append(qty)
        state.last_price = tick.ltp
        avg = Decimal(sum(state.recent_qty)) / Decimal(max(1, len(state.recent_qty)))
        if avg > 0 and Decimal(qty) >= avg * Decimal("3"):
            state.volume_spike_score = min(Decimal("100"), Decimal(qty) / avg * Decimal("20"))
            state.state = SymbolState.PROMOTED
            state.reason = [f"Volume spike {qty} vs avg {avg:.2f}"]
        elif state.state != SymbolState.INSTITUTIONAL_FOCUS:
            state.state = SymbolState.WATCHLIST if state.volume_spike_score >= Decimal("40") else SymbolState.NORMAL

    def snapshot(self) -> dict[str, Any]:
        items = [
            {
                "symbol": item.symbol,
                "state": item.state.value,
                "last_price": str(item.last_price) if item.last_price is not None else None,
                "volume_spike_score": str(item.volume_spike_score),
                "reason": item.reason,
            }
            for item in self.symbols.values()
            if item.state in {SymbolState.WATCHLIST, SymbolState.PROMOTED, SymbolState.INSTITUTIONAL_FOCUS}
        ]
        items.sort(key=lambda row: Decimal(row["volume_spike_score"]), reverse=True)
        return {"status": "OK", "items": items, "count": len(items)}


lightweight_screener = LightweightScreener()
