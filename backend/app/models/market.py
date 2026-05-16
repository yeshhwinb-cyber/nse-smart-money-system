from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class Exchange(StrEnum):
    NSE_EQ = "NSE_EQ"
    BSE_EQ = "BSE_EQ"
    NSE_FNO = "NSE_FNO"
    NSE_CURR = "NSE_CURR"
    MCX = "MCX"
    UNKNOWN = "UNKNOWN"


class FeedMode(StrEnum):
    LTP = "ltp"
    FULL = "full"
    DEPTH = "depth"


class SymbolState(StrEnum):
    NORMAL = "normal"
    WATCHLIST = "watchlist"
    PROMOTED = "promoted"
    INSTITUTIONAL_FOCUS = "institutional_focus"


class NormalizedTick(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    symbol: str
    provider: str = "SHAREKHAN"
    exchange: Exchange = Exchange.UNKNOWN
    segment: str | None = None
    scrip_code: str | None = None
    feed_code: str | None = None
    event_time: datetime
    received_at: datetime
    ltp: Decimal
    ltq: int | None = None
    session_qty: int | None = None
    open_price: Decimal | None = None
    high_price: Decimal | None = None
    low_price: Decimal | None = None
    close_price: Decimal | None = None
    avg_price: Decimal | None = None
    bid_price: Decimal | None = None
    bid_qty: int | None = None
    ask_price: Decimal | None = None
    ask_qty: int | None = None
    total_buy_qty: int | None = None
    total_sell_qty: int | None = None
    current_oi: int | None = None
    oi_change: int | None = None
    percent_change: Decimal | None = None
    rupee_change: Decimal | None = None
    side: str = "UNKNOWN"
    raw_payload: dict[str, Any] = Field(default_factory=dict)


class DepthSnapshot(BaseModel):
    symbol: str
    provider: str = "SHAREKHAN"
    exchange: Exchange = Exchange.UNKNOWN
    feed_code: str
    snapshot_time: datetime
    bid_levels: list[dict[str, Any]] = Field(default_factory=list)
    ask_levels: list[dict[str, Any]] = Field(default_factory=list)
    total_buy_qty: int | None = None
    total_sell_qty: int | None = None
    raw_payload: dict[str, Any] = Field(default_factory=dict)


class MarketEvent(BaseModel):
    event_type: str
    channel: str
    symbol: str | None = None
    payload: NormalizedTick | DepthSnapshot | dict[str, Any]
    created_at: datetime
