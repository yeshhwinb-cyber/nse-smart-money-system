BEGIN;

CREATE TABLE IF NOT EXISTS ladder.price_ladder_snapshots (
    id BIGSERIAL PRIMARY KEY,
    symbol TEXT NOT NULL,
    mode TEXT NOT NULL,
    snapshot_time TIMESTAMPTZ NOT NULL DEFAULT now(),
    current_price NUMERIC(18, 4),
    bucket_size NUMERIC(18, 4) NOT NULL,
    feed_state TEXT NOT NULL,
    source TEXT NOT NULL,
    row_count INTEGER NOT NULL DEFAULT 0,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE TABLE IF NOT EXISTS ladder.price_ladder_rows (
    id BIGSERIAL PRIMARY KEY,
    snapshot_id BIGINT NOT NULL REFERENCES ladder.price_ladder_snapshots(id) ON DELETE CASCADE,
    price_range TEXT NOT NULL,
    range_low NUMERIC(18, 4) NOT NULL,
    range_high NUMERIC(18, 4) NOT NULL,
    hist_volume BIGINT NOT NULL DEFAULT 0,
    live_volume BIGINT NOT NULL DEFAULT 0,
    touch_count INTEGER NOT NULL DEFAULT 0,
    buy_volume BIGINT NOT NULL DEFAULT 0,
    sell_volume BIGINT NOT NULL DEFAULT 0,
    delta BIGINT NOT NULL DEFAULT 0,
    total_volume BIGINT NOT NULL DEFAULT 0,
    abs_buy NUMERIC(18, 4),
    abs_sell NUMERIC(18, 4),
    net_abs NUMERIC(18, 4),
    up_reaction NUMERIC(18, 4),
    down_reaction NUMERIC(18, 4),
    reclaim_count INTEGER NOT NULL DEFAULT 0,
    level TEXT NOT NULL DEFAULT 'NEUTRAL',
    breakout_state TEXT NOT NULL DEFAULT 'DATA_PENDING',
    row_payload JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE TABLE IF NOT EXISTS analytics.reaction_zones (
    id BIGSERIAL PRIMARY KEY,
    symbol TEXT NOT NULL,
    mode TEXT NOT NULL,
    zone_type TEXT NOT NULL,
    range_low NUMERIC(18, 4) NOT NULL,
    range_high NUMERIC(18, 4) NOT NULL,
    first_seen TIMESTAMPTZ NOT NULL DEFAULT now(),
    last_seen TIMESTAMPTZ NOT NULL DEFAULT now(),
    touch_count INTEGER NOT NULL DEFAULT 0,
    defense_count INTEGER NOT NULL DEFAULT 0,
    rejection_count INTEGER NOT NULL DEFAULT 0,
    absorption_score NUMERIC(18, 4) NOT NULL DEFAULT 0,
    liquidity_score NUMERIC(18, 4) NOT NULL DEFAULT 0,
    confidence_score NUMERIC(18, 4) NOT NULL DEFAULT 0,
    status TEXT NOT NULL DEFAULT 'ACTIVE',
    evidence JSONB NOT NULL DEFAULT '[]'::jsonb
);

CREATE TABLE IF NOT EXISTS analytics.sector_participation (
    id BIGSERIAL PRIMARY KEY,
    sector TEXT NOT NULL,
    snapshot_time TIMESTAMPTZ NOT NULL DEFAULT now(),
    strength NUMERIC(18, 4) NOT NULL DEFAULT 0,
    participation_breadth NUMERIC(18, 4) NOT NULL DEFAULT 0,
    volume_score NUMERIC(18, 4) NOT NULL DEFAULT 0,
    rotation_direction TEXT NOT NULL DEFAULT 'NEUTRAL',
    leading_symbols JSONB NOT NULL DEFAULT '[]'::jsonb,
    lagging_symbols JSONB NOT NULL DEFAULT '[]'::jsonb
);

CREATE TABLE IF NOT EXISTS analytics.confidence_history (
    id BIGSERIAL PRIMARY KEY,
    symbol TEXT NOT NULL,
    mode TEXT NOT NULL,
    snapshot_time TIMESTAMPTZ NOT NULL DEFAULT now(),
    fast_confidence NUMERIC(18, 4) NOT NULL DEFAULT 0,
    structural_confidence NUMERIC(18, 4) NOT NULL DEFAULT 0,
    persistence_score NUMERIC(18, 4) NOT NULL DEFAULT 0,
    final_confidence NUMERIC(18, 4) NOT NULL DEFAULT 0,
    market_state TEXT,
    positive_factors JSONB NOT NULL DEFAULT '[]'::jsonb,
    negative_factors JSONB NOT NULL DEFAULT '[]'::jsonb
);

CREATE TABLE IF NOT EXISTS screener.promoted_symbols (
    symbol TEXT PRIMARY KEY,
    mode TEXT NOT NULL,
    symbol_state TEXT NOT NULL,
    confidence NUMERIC(18, 4) NOT NULL DEFAULT 0,
    market_state TEXT,
    absorption_state TEXT,
    liquidity_state TEXT,
    sector TEXT,
    reason JSONB NOT NULL DEFAULT '[]'::jsonb,
    promoted_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS strategy.test_trades (
    id BIGSERIAL PRIMARY KEY,
    symbol TEXT NOT NULL,
    mode TEXT NOT NULL,
    setup TEXT NOT NULL,
    direction TEXT NOT NULL,
    status TEXT NOT NULL,
    risk_status TEXT NOT NULL,
    entry_price NUMERIC(18, 4),
    stop_price NUMERIC(18, 4),
    target_price NUMERIC(18, 4),
    quantity INTEGER,
    reason JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS reports.market_reports (
    id BIGSERIAL PRIMARY KEY,
    report_date DATE NOT NULL,
    report_type TEXT NOT NULL,
    status TEXT NOT NULL,
    expected_market_type TEXT,
    market_summary JSONB NOT NULL DEFAULT '{}'::jsonb,
    sector_summary JSONB NOT NULL DEFAULT '{}'::jsonb,
    news_risk JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE(report_date, report_type)
);

CREATE INDEX IF NOT EXISTS idx_ladder_snapshots_symbol_time ON ladder.price_ladder_snapshots(symbol, snapshot_time DESC);
CREATE INDEX IF NOT EXISTS idx_ladder_rows_snapshot_range ON ladder.price_ladder_rows(snapshot_id, range_low, range_high);
CREATE INDEX IF NOT EXISTS idx_reaction_zones_symbol_score ON analytics.reaction_zones(symbol, confidence_score DESC);
CREATE INDEX IF NOT EXISTS idx_sector_participation_time ON analytics.sector_participation(snapshot_time DESC);
CREATE INDEX IF NOT EXISTS idx_confidence_symbol_time ON analytics.confidence_history(symbol, snapshot_time DESC);
CREATE INDEX IF NOT EXISTS idx_promoted_symbols_confidence ON screener.promoted_symbols(confidence DESC);

COMMIT;
