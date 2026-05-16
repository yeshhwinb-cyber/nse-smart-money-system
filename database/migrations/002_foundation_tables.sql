BEGIN;

CREATE TABLE IF NOT EXISTS auth.sharekhan_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id TEXT,
    access_token_hash TEXT NOT NULL,
    token_status TEXT NOT NULL DEFAULT 'TOKEN_UNKNOWN',
    session_status TEXT NOT NULL DEFAULT 'SESSION_UNKNOWN',
    issued_at TIMESTAMPTZ,
    expires_at TIMESTAMPTZ,
    last_validated_at TIMESTAMPTZ,
    last_error_code TEXT,
    last_error_message TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS auth.auth_events (
    id BIGSERIAL PRIMARY KEY,
    event_time TIMESTAMPTZ NOT NULL DEFAULT now(),
    event_type TEXT NOT NULL,
    customer_id TEXT,
    status TEXT NOT NULL,
    error_code TEXT,
    error_message TEXT,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE TABLE IF NOT EXISTS market.symbols (
    id BIGSERIAL PRIMARY KEY,
    symbol TEXT NOT NULL UNIQUE,
    display_name TEXT NOT NULL,
    company_name TEXT,
    exchange TEXT NOT NULL DEFAULT 'NSE',
    segment TEXT NOT NULL,
    instrument_type TEXT NOT NULL,
    sector TEXT,
    industry TEXT,
    is_index BOOLEAN NOT NULL DEFAULT false,
    is_fno BOOLEAN NOT NULL DEFAULT false,
    is_active BOOLEAN NOT NULL DEFAULT true,
    lot_size INTEGER,
    tick_size NUMERIC(18, 6),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS market.instrument_tokens (
    id BIGSERIAL PRIMARY KEY,
    symbol_id BIGINT NOT NULL REFERENCES market.symbols(id) ON DELETE CASCADE,
    provider TEXT NOT NULL,
    exchange_code TEXT NOT NULL,
    segment_code TEXT,
    scrip_code TEXT NOT NULL,
    feed_code TEXT NOT NULL,
    feed_ltp_code TEXT,
    feed_full_code TEXT,
    feed_depth_code TEXT,
    expiry_date DATE,
    strike_price NUMERIC(18, 4),
    option_type TEXT,
    is_primary BOOLEAN NOT NULL DEFAULT true,
    is_active BOOLEAN NOT NULL DEFAULT true,
    raw_metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE(provider, feed_code)
);

CREATE TABLE IF NOT EXISTS market.provider_status (
    provider TEXT PRIMARY KEY,
    status TEXT NOT NULL,
    connection_state TEXT NOT NULL DEFAULT 'DISCONNECTED',
    token_status TEXT,
    session_status TEXT,
    websocket_status TEXT,
    subscription_count INTEGER NOT NULL DEFAULT 0,
    ticks_received BIGINT NOT NULL DEFAULT 0,
    last_tick_at TIMESTAMPTZ,
    last_heartbeat_at TIMESTAMPTZ,
    latency_ms NUMERIC(18, 3),
    last_error_code TEXT,
    last_error_message TEXT,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS market.subscription_state (
    id BIGSERIAL PRIMARY KEY,
    symbol_id BIGINT REFERENCES market.symbols(id) ON DELETE CASCADE,
    provider TEXT NOT NULL,
    feed_code TEXT NOT NULL,
    feed_mode TEXT NOT NULL,
    symbol_state TEXT NOT NULL DEFAULT 'normal',
    subscribed BOOLEAN NOT NULL DEFAULT false,
    promoted BOOLEAN NOT NULL DEFAULT false,
    institutional_focus BOOLEAN NOT NULL DEFAULT false,
    last_subscribed_at TIMESTAMPTZ,
    last_unsubscribed_at TIMESTAMPTZ,
    last_error_code TEXT,
    last_error_message TEXT,
    UNIQUE(provider, feed_code, feed_mode)
);

CREATE TABLE IF NOT EXISTS system.sync_logs (
    id BIGSERIAL PRIMARY KEY,
    event_time TIMESTAMPTZ NOT NULL DEFAULT now(),
    source TEXT NOT NULL,
    module TEXT NOT NULL,
    status TEXT NOT NULL,
    symbol TEXT,
    error_code TEXT,
    error_message TEXT,
    row_count BIGINT,
    duration_ms NUMERIC(18, 3),
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE INDEX IF NOT EXISTS idx_symbols_segment_active ON market.symbols(segment, is_active);
CREATE INDEX IF NOT EXISTS idx_symbols_sector ON market.symbols(sector);
CREATE INDEX IF NOT EXISTS idx_tokens_symbol_provider ON market.instrument_tokens(symbol_id, provider);
CREATE INDEX IF NOT EXISTS idx_sync_logs_time ON system.sync_logs(event_time DESC);
CREATE INDEX IF NOT EXISTS idx_sync_logs_module_status ON system.sync_logs(module, status);

COMMIT;
