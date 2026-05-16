# NSE Smart Money Market Intelligence Database Plan

Project path: `J:\sharekhan\nse-smart-money-system`

Database engine: PostgreSQL 18

Database name: `nse_trading_system`

This system is an institutional market intelligence platform. It is not an indicator crossover platform and not an OI-only option system.

Primary intelligence priority:

1. Live market structure
2. Liquidity behavior
3. Absorption
4. Sector participation
5. Confidence scoring
6. Futures/options context
7. Reaction zones

## Provider Rules

Sharekhan is primary for:

- live tick streaming
- LTP / full / depth feed
- live price movement
- market depth
- historical candles
- market structure

NSE India is used for:

- option chain
- OI
- PCR
- strike-level analytics

Finnhub is used for:

- market-impact news
- macro news
- sector-impact news

## Database Schemas

- `auth`: Sharekhan authorization/session state
- `market`: symbols, tokens, live ticks, depth, snapshots, provider status
- `system`: sync logs, runtime health, settings
- `eqhist`: equity historical candles
- `fnohist`: futures historical candles and snapshots
- `optionhist`: option chain snapshots from NSE India
- `screener`: promotion/filter results
- `analytics`: market state, sector rotation, confidence, absorption, reaction zones
- `ladder`: adaptive price ladder snapshots/rows
- `strategy`: watch/test trade logic only
- `reports`: morning/EOD reports and news risk summaries

## Build Order

1. Create schemas and extensions.
2. Create foundation tables: symbols, tokens, sessions, provider status, sync logs.
3. Create live data tables: ticks, depth, snapshots, subscriptions.
4. Create historical tables: equity, futures, options.
5. Create intelligence tables: ladder, reaction zones, absorption, confidence.
6. Create screener/promotion tables.
7. Create report and test-trade tables.
8. Build backend data access layer.
9. Build Sharekhan auth/session manager.
10. Build one-websocket live runtime.
11. Build engines.
12. Build frontend.

## Critical Rules

- Never use float for price internally.
- Use Python `Decimal`.
- Use PostgreSQL `NUMERIC`.
- Normalize all provider payloads before engine use.
- Only one Sharekhan websocket connection per API key.
- Respect 1000 symbol subscription limit.
- Respect 5 requests/sec REST limit.
- Store raw provider payloads for audit, but engines must consume normalized events only.
- No real broker order execution.
- Test/learning mode only.
