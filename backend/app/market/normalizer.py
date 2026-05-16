from __future__ import annotations

from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import Any

from app.core.settings import IST
from app.models.market import Exchange, NormalizedTick


EXCHANGE_MAP = {
    "NC": Exchange.NSE_EQ,
    "BC": Exchange.BSE_EQ,
    "NF": Exchange.NSE_FNO,
    "RN": Exchange.NSE_CURR,
    "MX": Exchange.MCX,
}


def _decimal(value: Any) -> Decimal | None:
    if value in (None, "", " "):
        return None
    try:
        return Decimal(str(value).replace(",", ""))
    except (InvalidOperation, ValueError):
        return None


def _int(value: Any) -> int | None:
    if value in (None, "", " "):
        return None
    try:
        return int(Decimal(str(value).replace(",", "")))
    except (InvalidOperation, ValueError):
        return None


def _time(value: Any) -> datetime:
    if isinstance(value, datetime):
        return value.astimezone(IST) if value.tzinfo else value.replace(tzinfo=IST)
    text = str(value or "").strip()
    for fmt in ("%m/%d/%Y %H:%M:%S", "%d/%m/%Y %H:%M:%S"):
        try:
            return datetime.strptime(text, fmt).replace(tzinfo=IST)
        except ValueError:
            pass
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
        return parsed.astimezone(IST) if parsed.tzinfo else parsed.replace(tzinfo=IST)
    except ValueError:
        return datetime.now(IST)


class SharekhanNormalizer:
    def __init__(self, feed_symbol_map: dict[str, str] | None = None) -> None:
        self.feed_symbol_map = feed_symbol_map or {}

    def normalize_message(self, message: dict[str, Any]) -> list[NormalizedTick]:
        if message.get("status") != 100 or message.get("message") != "feed":
            return []
        payload = message.get("data")
        rows = payload if isinstance(payload, list) else [payload]
        ticks: list[NormalizedTick] = []
        for row in rows:
            if isinstance(row, dict):
                tick = self.normalize_tick(row)
                if tick:
                    ticks.append(tick)
        return ticks

    def normalize_tick(self, row: dict[str, Any]) -> NormalizedTick | None:
        exchange_code = str(row.get("exchangeCode") or row.get("Exchange") or "").upper()
        scrip_code = str(row.get("scripCode") or row.get("scripcode") or "")
        feed_code = f"{exchange_code}{scrip_code}" if exchange_code and scrip_code else None
        symbol = self.feed_symbol_map.get(str(feed_code), str(row.get("tradingSymbol") or row.get("TradingSymbol") or feed_code or "UNKNOWN").upper())
        ltp = _decimal(row.get("ltp") or row.get("LTP") or row.get("price"))
        if ltp is None:
            return None
        now = datetime.now(IST)
        bid_qty = _int(row.get("bidQty"))
        ask_qty = _int(row.get("offQty") or row.get("askQty"))
        side = "UNKNOWN"
        if bid_qty is not None and ask_qty is not None and bid_qty != ask_qty:
            side = "BUY" if bid_qty > ask_qty else "SELL"
        return NormalizedTick(
            symbol=symbol,
            exchange=EXCHANGE_MAP.get(exchange_code, Exchange.UNKNOWN),
            segment=str(row.get("insType") or row.get("SegmentCode") or ""),
            scrip_code=scrip_code,
            feed_code=feed_code,
            event_time=_time(row.get("ltt") or row.get("lastUpdatedTime") or message_time(row) or now),
            received_at=now,
            ltp=ltp,
            ltq=_int(row.get("ltq") or row.get("preltq")),
            session_qty=_int(row.get("qty")),
            open_price=_decimal(row.get("open")),
            high_price=_decimal(row.get("high")),
            low_price=_decimal(row.get("low")),
            close_price=_decimal(row.get("close")),
            avg_price=_decimal(row.get("avgPrice")),
            bid_price=_decimal(row.get("bidPrice")),
            bid_qty=bid_qty,
            ask_price=_decimal(row.get("offPrice") or row.get("askPrice")),
            ask_qty=ask_qty,
            total_buy_qty=_int(row.get("totalBuyQty")),
            total_sell_qty=_int(row.get("totalSellQty")),
            current_oi=_int(row.get("currentOI")),
            oi_change=_int(row.get("oichange") or row.get("oiChange") or row.get("oidiff")),
            percent_change=_decimal(row.get("perChange")),
            rupee_change=_decimal(row.get("rsChange")),
            side=side,
            raw_payload=row,
        )


def message_time(row: dict[str, Any]) -> Any:
    return row.get("timestamp")
