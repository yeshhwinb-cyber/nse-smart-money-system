# PostgreSQL Connection

The backend reads PostgreSQL from `.env`:

```env
DATABASE_URL=postgresql://postgres:YOUR_PASSWORD@127.0.0.1:5432/nse_trading_system
```

Current Phase-1 runtime starts even if the database password is wrong. In that case:

```json
{
  "database": {
    "status": "DB_UNHEALTHY",
    "error_code": "InvalidPasswordError"
  }
}
```

Fix by updating `backend\.env` with the PostgreSQL 18 password/user used in pgAdmin.

Then test:

```powershell
Invoke-RestMethod http://127.0.0.1:8001/api/health/db
```
