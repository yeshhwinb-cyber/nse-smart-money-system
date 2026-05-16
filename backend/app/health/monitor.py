from __future__ import annotations

from datetime import datetime
from typing import Any

from app.auth.session_manager import session_manager
from app.core.database import db
from app.core.settings import IST
from app.websocket.sharekhan_ws import sharekhan_ws_service


class HealthMonitor:
    async def db_health(self) -> dict[str, Any]:
        try:
            ok = await db.ping()
            return {"status": "OK" if ok else "DB_UNHEALTHY"}
        except Exception as exc:
            return {"status": "DB_UNHEALTHY", "error_code": exc.__class__.__name__, "error_message": str(exc)}

    async def runtime_health(self) -> dict[str, Any]:
        return {
            "status": "OK",
            "time": datetime.now(IST).isoformat(),
            "auth": session_manager.health(),
            "websocket": sharekhan_ws_service.health(),
            "database": await self.db_health(),
        }


health_monitor = HealthMonitor()
