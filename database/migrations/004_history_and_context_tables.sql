BEGIN;

CREATE TABLE IF NOT EXISTS eqhist.candles (
    id BIGSERIAL PRIMARY KEY,
    symbol TEXT NOT NULL,
    timeframe TEXT NOT NULL,
    candle_time TIMESTAMPTZ NOT NULL,
    open_price NUMERIC(18, 4) NOT NULL,
    high_price NUMERIC(18, 4) NOT NULL,
    low_price NUMERIC(18, 4) NOT NULL,
    close_price NUMERIC(18, 4) NOT NULL,
    volume BIGINT,
    source TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE(symbol, timeframe, candle_time, source)
);

CREATE TABLE IF NOT EXISTS fnohist.futures_snapshots (
    id BIGSERIAL PRIMARY KEY,
    symbol TEXT NOT NULL,
    contract_symbol TEXT NOT NULL,
    expiry_date DATE,
    snapshot_time TIMESTAMPTZ NOT NULL,
    futures_price NUMERIC(18, 4),
    spot_price NUMERIC(18, 4),
    premium_discount NUMERIC(18, 4),
    source TEXT NOT NULL,
    raw_payload JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE TABLE IF NOT EXISTS optionhist.option_chain_snapshots (
    id BIGSERIAL PRIMARY KEY,
    underlying TEXT NOT NULL,
    expiry_date DATE,
    snapshot_time TIMESTAMPTZ NOT NULL,
    underlying_price NUMERIC(18, 4),
    active_strike NUMERIC(18, 4),
    source TEXT NOT NULL,
    pcr_oi NUMERIC(18, 6),
    pcr_volume NUMERIC(18, 6),
    total_ce_oi BIGINT,
    total_pe_oi BIGINT,
    total_ce_volume BIGINT,
    total_pe_volume BIGINT,
    raw_payload JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE TABLE IF NOT EXISTS optionhist.option_chain_rows (
    id BIGSERIAL PRIMARY KEY,
    snapshot_id BIGINT NOT NULL REFERENCES optionhist.option_chain_snapshots(id) ON DELETE CASCADE,
    strike_price NUMERIC(18, 4) NOT NULL,
    ce_ltp NUMERIC(18, 4),
    ce_oi BIGINT,
    ce_change_oi BIGINT,
    ce_volume BIGINT,
    ce_iv NUMERIC(18, 6),
    pe_ltp NUMERIC(18, 4),
    pe_oi BIGINT,
    pe_change_oi BIGINT,
    pe_volume BIGINT,
    pe_iv NUMERIC(18, 6)
);

CREATE INDEX IF NOT EXISTS idx_eqhist_candles_symbol_tf_time ON eqhist.candles(symbol, timeframe, candle_time DESC);
CREATE INDEX IF NOT EXISTS idx_futures_snapshots_symbol_time ON fnohist.futures_snapshots(symbol, snapshot_time DESC);
CREATE INDEX IF NOT EXISTS idx_option_snapshots_underlying_time ON optionhist.option_chain_snapshots(underlying, snapshot_time DESC);
CREATE INDEX IF NOT EXISTS idx_option_rows_snapshot_strike ON optionhist.option_chain_rows(snapshot_id, strike_price);

COMMIT;
