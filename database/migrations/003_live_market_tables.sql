BEGIN;

CREATE TABLE IF NOT EXISTS market.live_ticks (
    id BIGSERIAL PRIMARY KEY,
    symbol_id BIGINT REFERENCES market.symbols(id) ON DELETE SET NULL,
    symbol TEXT NOT NULL,
    provider TEXT NOT NULL,
    exchange_code TEXT,
    segment TEXT,
    scrip_code TEXT,
    feed_code TEXT,
    event_time TIMESTAMPTZ NOT NULL,
    received_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    ltp NUMERIC(18, 4) NOT NULL,
    ltq BIGINT,
    session_qty BIGINT,
    open_price NUMERIC(18, 4),
    high_price NUMERIC(18, 4),
    low_price NUMERIC(18, 4),
    close_price NUMERIC(18, 4),
    avg_price NUMERIC(18, 4),
    bid_price NUMERIC(18, 4),
    bid_qty BIGINT,
    ask_price NUMERIC(18, 4),
    ask_qty BIGINT,
    total_buy_qty BIGINT,
    total_sell_qty BIGINT,
    current_oi BIGINT,
    oi_change BIGINT,
    percent_change NUMERIC(18, 6),
    rupee_change NUMERIC(18, 4),
    side TEXT NOT NULL DEFAULT 'UNKNOWN',
    tick_hash TEXT NOT NULL,
    raw_payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    UNIQUE(provider, feed_code, tick_hash)
);

CREATE TABLE IF NOT EXISTS market.live_snapshots (
    symbol TEXT PRIMARY KEY,
    symbol_id BIGINT REFERENCES market.symbols(id) ON DELETE SET NULL,
    provider TEXT NOT NULL,
    feed_code TEXT,
    source_mode TEXT NOT NULL DEFAULT 'LIVE',
    ltp NUMERIC(18, 4),
    open_price NUMERIC(18, 4),
    high_price NUMERIC(18, 4),
    low_price NUMERIC(18, 4),
    close_price NUMERIC(18, 4),
    session_qty BIGINT,
    ltq BIGINT,
    bid_price NUMERIC(18, 4),
    bid_qty BIGINT,
    ask_price NUMERIC(18, 4),
    ask_qty BIGINT,
    total_buy_qty BIGINT,
    total_sell_qty BIGINT,
    current_oi BIGINT,
    oi_change BIGINT,
    market_state TEXT,
    last_tick_at TIMESTAMPTZ,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    raw_payload JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE TABLE IF NOT EXISTS market.depth_snapshots (
    id BIGSERIAL PRIMARY KEY,
    symbol TEXT NOT NULL,
    symbol_id BIGINT REFERENCES market.symbols(id) ON DELETE SET NULL,
    provider TEXT NOT NULL,
    feed_code TEXT NOT NULL,
    snapshot_time TIMESTAMPTZ NOT NULL,
    bid_levels JSONB NOT NULL DEFAULT '[]'::jsonb,
    ask_levels JSONB NOT NULL DEFAULT '[]'::jsonb,
    total_buy_qty BIGINT,
    total_sell_qty BIGINT,
    raw_payload JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE TABLE IF NOT EXISTS market.normalized_events (
    id BIGSERIAL PRIMARY KEY,
    event_time TIMESTAMPTZ NOT NULL,
    received_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    provider TEXT NOT NULL,
    event_type TEXT NOT NULL,
    symbol TEXT,
    feed_code TEXT,
    payload JSONB NOT NULL,
    processed BOOLEAN NOT NULL DEFAULT false
);

CREATE INDEX IF NOT EXISTS idx_live_ticks_symbol_time ON market.live_ticks(symbol, event_time DESC);
CREATE INDEX IF NOT EXISTS idx_live_ticks_provider_feed_time ON market.live_ticks(provider, feed_code, event_time DESC);
CREATE INDEX IF NOT EXISTS idx_live_ticks_received ON market.live_ticks(received_at DESC);
CREATE INDEX IF NOT EXISTS idx_depth_symbol_time ON market.depth_snapshots(symbol, snapshot_time DESC);
CREATE INDEX IF NOT EXISTS idx_normalized_events_unprocessed ON market.normalized_events(processed, received_at);

COMMIT;
