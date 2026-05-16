from __future__ import annotations

import csv
import io
import logging
from typing import Any

import httpx

from app.core.database import db
from app.core.settings import get_settings
from app.repositories.market_repository import market_repository
from app.repositories.system_repository import system_repository

logger = logging.getLogger(__name__)


class ScripMasterService:
    async def sync_daily(self) -> dict[str, Any]:
        settings = get_settings()
        if not settings.scripmaster_url:
            return {"status": "SOURCE_REQUIRED", "error_code": "SCRIPMASTER_URL_MISSING", "rows": 0}
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(settings.scripmaster_url)
        response.raise_for_status()
        rows = list(csv.DictReader(io.StringIO(response.text)))
        count = 0
        async for conn in db.acquire():
            async with conn.transaction():
                for row in rows:
                    symbol = str(row.get("tradingSymbol") or row.get("symbol") or row.get("symbolName") or "").strip().upper()
                    scrip_code = str(row.get("scripCode") or row.get("scripcode") or "").strip()
                    exchange_code = str(row.get("exchangeCode") or row.get("exchange") or "NC").strip().upper()
                    if not symbol or not scrip_code:
                        continue
                    segment = str(row.get("segment") or row.get("instrumentType") or "EQ").upper()
                    is_index = segment in {"INDEX", "IDX"}
                    symbol_id = await market_repository.upsert_symbol(
                        conn,
                        symbol=symbol,
                        display_name=str(row.get("displayName") or row.get("name") or symbol),
                        segment="INDEX" if is_index else "EQUITY",
                        instrument_type="INDEX" if is_index else "EQUITY",
                        sector=row.get("sector"),
                        is_index=is_index,
                        is_fno=bool(row.get("expiryDate")),
                        lot_size=_int(row.get("lotSize")),
                    )
                    await market_repository.upsert_token(
                        conn,
                        symbol_id=symbol_id,
                        provider="SHAREKHAN",
                        exchange_code=exchange_code,
                        segment_code=segment,
                        scrip_code=scrip_code,
                        feed_code=f"{exchange_code}{scrip_code}",
                        raw_metadata=row,
                    )
                    count += 1
                await system_repository.log_sync(conn, source="SHAREKHAN", module="SCRIPMASTER", status="OK", row_count=count)
        return {"status": "OK", "rows": count}


def _int(value: Any) -> int | None:
    try:
        if value in (None, ""):
            return None
        return int(float(value))
    except (TypeError, ValueError):
        return None


scripmaster_service = ScripMasterService()
