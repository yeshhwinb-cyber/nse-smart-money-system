from __future__ import annotations

import hashlib
import logging
from datetime import datetime, time, timedelta
from typing import Any
from urllib.parse import urlencode

import httpx

from app.auth.crypto import encrypt_text
from app.auth.session_manager import session_manager
from app.core.database import db
from app.core.settings import IST, get_settings

logger = logging.getLogger(__name__)


class SharekhanAuthService:
    def build_auth_url(self, state: str | None = None) -> str:
        settings = get_settings()
        query = {
            "api_key": settings.sharekhan_api_key,
        }
        if state:
            query["state"] = state
        return f"{settings.sharekhan_auth_url}?{urlencode(query)}"

    async def process_request_token(self, request_token: str) -> dict[str, Any]:
        settings = get_settings()
        if not request_token:
            return {"status": "TOKEN_MISSING", "error_code": "REQUEST_TOKEN_REQUIRED"}
        if not settings.sharekhan_api_key:
            return {"status": "CONFIG_MISSING", "error_code": "SHAREKHAN_API_KEY_REQUIRED"}

        payload = {
            "apiKey": settings.sharekhan_api_key,
            "requestToken": request_token,
            "secretKey": settings.sharekhan_secret_key,
        }
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.post(settings.sharekhan_token_url, json=payload)

        if response.status_code >= 400:
            return {
                "status": "TOKEN_EXCHANGE_FAILED",
                "error_code": f"HTTP_{response.status_code}",
                "error_message": response.text[:500],
            }

        data = response.json()
        access_token = (
            data.get("access_token")
            or data.get("accessToken")
            or data.get("token")
            or data.get("data", {}).get("access_token")
            or data.get("data", {}).get("accessToken")
        )
        if not access_token:
            return {"status": "TOKEN_EXCHANGE_FAILED", "error_code": "ACCESS_TOKEN_NOT_FOUND", "raw": data}

        expiry = self.midnight_expiry()
        token_hash = hashlib.sha256(access_token.encode("utf-8")).hexdigest()
        encrypt_text(access_token, settings.token_encryption_key or settings.sharekhan_secret_key or settings.sharekhan_api_key)
        async for conn in db.acquire():
            await conn.execute(
                """
                INSERT INTO auth.sharekhan_sessions(customer_id, access_token_hash, token_status, session_status,
                                                    issued_at, expires_at, last_validated_at, last_error_code, last_error_message)
                VALUES($1,$2,'TOKEN_ACTIVE','SESSION_ACTIVE',now(),$3,now(),NULL,NULL)
                """,
                settings.sharekhan_customer_id,
                token_hash,
                expiry,
            )
        session_manager.set_access_token(access_token, expiry)
        return {"status": "TOKEN_ACTIVE", "session_status": "SESSION_ACTIVE", "expires_at": expiry.isoformat()}

    def midnight_expiry(self) -> datetime:
        now = datetime.now(IST)
        tomorrow = now.date() + timedelta(days=1)
        return datetime.combine(tomorrow, time.min, tzinfo=IST)


auth_service = SharekhanAuthService()
