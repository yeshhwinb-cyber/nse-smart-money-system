from __future__ import annotations

import hashlib
import json
from decimal import Decimal
from typing import Any

from app.models.market import NormalizedTick


def _decimal(value: Decimal | None) -> Decimal | None:
    return value if value is not None else None


class MarketRepository:
    async def find_symbol_by_feed_code(self, conn: Any, provider: str, feed_code: str) -> Any | None:
        return await conn.fetchrow(
            """
            SELECT s.*, t.feed_code, t.exchange_code, t.scrip_code
            FROM market.instrument_tokens t
            JOIN market.symbols s ON s.id = t.symbol_id
            WHERE t.provider = $1 AND t.feed_code = $2 AND t.is_active = true
            LIMIT 1
            """,
            provider,
            feed_code,
        )

    async def upsert_symbol(
        self,
        conn: Any,
        *,
        symbol: str,
        display_name: str,
        segment: str,
        instrument_type: str,
        sector: str | None = None,
        is_index: bool = False,
        is_fno: bool = False,
        lot_size: int | None = None,
    ) -> int:
        return await conn.fetchval(
            """
            INSERT INTO market.symbols(symbol, display_name, company_name, segment, instrument_type, sector, is_index, is_fno, lot_size)
            VALUES($1,$2,$2,$3,$4,$5,$6,$7,$8)
            ON CONFLICT(symbol) DO UPDATE SET
                display_name = EXCLUDED.display_name,
                segment = EXCLUDED.segment,
                instrument_type = EXCLUDED.instrument_type,
                sector = EXCLUDED.sector,
                is_index = EXCLUDED.is_index,
                is_fno = EXCLUDED.is_fno,
                lot_size = EXCLUDED.lot_size,
                updated_at = now()
            RETURNING id
            """,
            symbol,
            display_name,
            segment,
            instrument_type,
            sector,
            is_index,
            is_fno,
            lot_size,
        )

    async def upsert_token(
        self,
        conn: Any,
        *,
        symbol_id: int,
        provider: str,
        exchange_code: str,
        scrip_code: str,
        feed_code: str,
        segment_code: str | None = None,
        is_primary: bool = True,
        raw_metadata: dict[str, Any] | None = None,
    ) -> None:
        await conn.execute(
            """
            INSERT INTO market.instrument_tokens(symbol_id, provider, exchange_code, segment_code, scrip_code, feed_code,
                                                 feed_ltp_code, feed_full_code, feed_depth_code, is_primary, raw_metadata)
            VALUES($1,$2,$3,$4,$5,$6,$6,$6,$6,$7,$8)
            ON CONFLICT(provider, feed_code) DO UPDATE SET
                symbol_id = EXCLUDED.symbol_id,
                exchange_code = EXCLUDED.exchange_code,
                segment_code = EXCLUDED.segment_code,
                scrip_code = EXCLUDED.scrip_code,
                is_primary = EXCLUDED.is_primary,
                raw_metadata = EXCLUDED.raw_metadata,
                updated_at = now()
            """,
            symbol_id,
            provider,
            exchange_code,
            segment_code,
            scrip_code,
            feed_code,
            is_primary,
            json.dumps(raw_metadata or {}),
        )

    async def insert_tick(self, conn: Any, tick: NormalizedTick) -> None:
        raw_payload = json.dumps(tick.raw_payload, default=str, separators=(",", ":"))
        tick_hash = hashlib.sha256(
            f"{tick.provider}|{tick.feed_code}|{tick.event_time.isoformat()}|{tick.ltp}|{tick.ltq}|{tick.session_qty}".encode()
        ).hexdigest()
        await conn.execute(
            """
            INSERT INTO market.live_ticks(
                symbol, provider, exchange_code, segment, scrip_code, feed_code, event_time, received_at,
                ltp, ltq, session_qty, open_price, high_price, low_price, close_price, avg_price,
                bid_price, bid_qty, ask_price, ask_qty, total_buy_qty, total_sell_qty, current_oi, oi_change,
                percent_change, rupee_change, side, tick_hash, raw_payload
            )
            VALUES($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14,$15,$16,$17,$18,$19,$20,$21,$22,$23,$24,$25,$26,$27,$28,$29)
            ON CONFLICT(provider, feed_code, tick_hash) DO NOTHING
            """,
            tick.symbol,
            tick.provider,
            tick.exchange.value,
            tick.segment,
            tick.scrip_code,
            tick.feed_code,
            tick.event_time,
            tick.received_at,
            _decimal(tick.ltp),
            tick.ltq,
            tick.session_qty,
            _decimal(tick.open_price),
            _decimal(tick.high_price),
            _decimal(tick.low_price),
            _decimal(tick.close_price),
            _decimal(tick.avg_price),
            _decimal(tick.bid_price),
            tick.bid_qty,
            _decimal(tick.ask_price),
            tick.ask_qty,
            tick.total_buy_qty,
            tick.total_sell_qty,
            tick.current_oi,
            tick.oi_change,
            _decimal(tick.percent_change),
            _decimal(tick.rupee_change),
            tick.side,
            tick_hash,
            raw_payload,
        )

    async def upsert_snapshot(self, conn: Any, tick: NormalizedTick) -> None:
        await conn.execute(
            """
            INSERT INTO market.live_snapshots(
                symbol, provider, feed_code, source_mode, ltp, open_price, high_price, low_price, close_price,
                session_qty, ltq, bid_price, bid_qty, ask_price, ask_qty, total_buy_qty, total_sell_qty,
                current_oi, oi_change, last_tick_at, raw_payload
            )
            VALUES($1,$2,$3,'LIVE',$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14,$15,$16,$17,$18,$19,$20)
            ON CONFLICT(symbol) DO UPDATE SET
                provider = EXCLUDED.provider,
                feed_code = EXCLUDED.feed_code,
                source_mode = 'LIVE',
                ltp = EXCLUDED.ltp,
                open_price = EXCLUDED.open_price,
                high_price = EXCLUDED.high_price,
                low_price = EXCLUDED.low_price,
                close_price = EXCLUDED.close_price,
                session_qty = EXCLUDED.session_qty,
                ltq = EXCLUDED.ltq,
                bid_price = EXCLUDED.bid_price,
                bid_qty = EXCLUDED.bid_qty,
                ask_price = EXCLUDED.ask_price,
                ask_qty = EXCLUDED.ask_qty,
                total_buy_qty = EXCLUDED.total_buy_qty,
                total_sell_qty = EXCLUDED.total_sell_qty,
                current_oi = EXCLUDED.current_oi,
                oi_change = EXCLUDED.oi_change,
                last_tick_at = EXCLUDED.last_tick_at,
                raw_payload = EXCLUDED.raw_payload,
                updated_at = now()
            """,
            tick.symbol,
            tick.provider,
            tick.feed_code,
            _decimal(tick.ltp),
            _decimal(tick.open_price),
            _decimal(tick.high_price),
            _decimal(tick.low_price),
            _decimal(tick.close_price),
            tick.session_qty,
            tick.ltq,
            _decimal(tick.bid_price),
            tick.bid_qty,
            _decimal(tick.ask_price),
            tick.ask_qty,
            tick.total_buy_qty,
            tick.total_sell_qty,
            tick.current_oi,
            tick.oi_change,
            tick.event_time,
            json.dumps(tick.raw_payload, default=str),
        )

    async def provider_status(self, conn: Any, provider: str, **values: Any) -> None:
        await conn.execute(
            """
            INSERT INTO market.provider_status(provider, status, connection_state, token_status, session_status,
                                               websocket_status, subscription_count, ticks_received, last_tick_at,
                                               last_heartbeat_at, latency_ms, last_error_code, last_error_message, updated_at)
            VALUES($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,now())
            ON CONFLICT(provider) DO UPDATE SET
                status = EXCLUDED.status,
                connection_state = EXCLUDED.connection_state,
                token_status = EXCLUDED.token_status,
                session_status = EXCLUDED.session_status,
                websocket_status = EXCLUDED.websocket_status,
                subscription_count = EXCLUDED.subscription_count,
                ticks_received = EXCLUDED.ticks_received,
                last_tick_at = EXCLUDED.last_tick_at,
                last_heartbeat_at = EXCLUDED.last_heartbeat_at,
                latency_ms = EXCLUDED.latency_ms,
                last_error_code = EXCLUDED.last_error_code,
                last_error_message = EXCLUDED.last_error_message,
                updated_at = now()
            """,
            provider,
            values.get("status", "UNKNOWN"),
            values.get("connection_state", "DISCONNECTED"),
            values.get("token_status"),
            values.get("session_status"),
            values.get("websocket_status"),
            int(values.get("subscription_count") or 0),
            int(values.get("ticks_received") or 0),
            values.get("last_tick_at"),
            values.get("last_heartbeat_at"),
            values.get("latency_ms"),
            values.get("last_error_code"),
            values.get("last_error_message"),
        )


market_repository = MarketRepository()
