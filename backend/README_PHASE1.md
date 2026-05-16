# Phase-1 Backend Runtime

This is the foundation runtime for `J:\sharekhan\nse-smart-money-system`.

It does not include frontend, advanced analytics, option engines, replay, or execution.

## Run

```powershell
cd J:\sharekhan\nse-smart-money-system\backend
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
python -m uvicorn app.main:app --host 127.0.0.1 --port 8001 --reload
```

## Health URLs

- `GET /health`
- `GET /api/health/runtime`
- `GET /api/health/db`
- `GET /api/auth/sharekhan/login-url`
- `POST /api/auth/sharekhan/request-token`
- `GET /api/websocket/status`
- `GET /api/screener/lightweight`

## Rules

- One Sharekhan websocket runtime only.
- Decimal prices internally.
- Raw provider payloads are stored/audited but engines consume normalized events.
- No broker execution.
- No frontend in Phase 1.
