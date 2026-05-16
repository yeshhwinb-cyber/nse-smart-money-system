from __future__ import annotations

from decimal import Decimal
from typing import Any

import httpx

from app.core.database import db
from app.core.settings import get_settings
from app.repositories.system_repository import system_repository


SUPPORTED_TIMEFRAMES = {"daily", "weekly", "monthly", "1m", "5m", "15m", "30m", "60m", "90m"}


class HistoricalService:
    async def sync_symbol(self, symbol: str, timeframe: str = "daily") -> dict[str, Any]:
        settings = get_settings()
        if timeframe not in SUPPORTED_TIMEFRAMES:
            return {"status": "INVALID_TIMEFRAME", "supported": sorted(SUPPORTED_TIMEFRAMES)}
        if not settings.historical_base_url:
            return {"status": "SOURCE_REQUIRED", "error_code": "HISTORICAL_BASE_URL_MISSING"}

        url = f"{settings.historical_base_url.rstrip('/')}/{symbol.upper()}/{timeframe}"
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(url)
        response.raise_for_status()
        payload = response.json()
        rows = payload.get("data") if isinstance(payload, dict) else payload
        if not isinstance(rows, list):
            rows = []

        inserted = 0
        async for conn in db.acquire():
            async with conn.transaction():
                for row in rows:
                    try:
                        await conn.execute(
                            """
                            INSERT INTO eqhist.candles(symbol, timeframe, candle_time, open_price, high_price, low_price, close_price, volume, source)
                            VALUES($1,$2,$3,$4,$5,$6,$7,$8,'SHAREKHAN')
                            ON CONFLICT(symbol, timeframe, candle_time, source) DO UPDATE SET
                                open_price = EXCLUDED.open_price,
                                high_price = EXCLUDED.high_price,
                                low_price = EXCLUDED.low_price,
                                close_price = EXCLUDED.close_price,
                                volume = EXCLUDED.volume
                            """,
                            symbol.upper(),
                            timeframe,
                            row.get("time") or row.get("datetime") or row.get("timestamp"),
                            Decimal(str(row.get("open"))),
                            Decimal(str(row.get("high"))),
                            Decimal(str(row.get("low"))),
                            Decimal(str(row.get("close"))),
                            _int(row.get("volume")),
                        )
                        inserted += 1
                    except Exception:
                        continue
                await system_repository.log_sync(conn, source="SHAREKHAN", module="HISTORICAL", status="OK", symbol=symbol.upper(), row_count=inserted)
        return {"status": "OK", "symbol": symbol.upper(), "timeframe": timeframe, "rows": inserted}


def _int(value: Any) -> int | None:
    try:
        if value in (None, ""):
            return None
        return int(float(value))
    except (TypeError, ValueError):
        return None


historical_service = HistoricalService()
