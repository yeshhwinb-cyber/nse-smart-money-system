from __future__ import annotations

import json
from typing import Any


class SystemRepository:
    async def log_sync(
        self,
        conn: Any,
        *,
        source: str,
        module: str,
        status: str,
        symbol: str | None = None,
        error_code: str | None = None,
        error_message: str | None = None,
        row_count: int | None = None,
        duration_ms: float | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        await conn.execute(
            """
            INSERT INTO system.sync_logs(source, module, status, symbol, error_code, error_message, row_count, duration_ms, metadata)
            VALUES($1,$2,$3,$4,$5,$6,$7,$8,$9)
            """,
            source,
            module,
            status,
            symbol,
            error_code,
            error_message,
            row_count,
            duration_ms,
            json.dumps(metadata or {}),
        )


system_repository = SystemRepository()
