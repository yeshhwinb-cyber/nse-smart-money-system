from __future__ import annotations

from functools import lru_cache
from zoneinfo import ZoneInfo

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

IST = ZoneInfo("Asia/Kolkata")


class Settings(BaseSettings):
    app_name: str = "NSE Smart Money Runtime"
    app_host: str = "127.0.0.1"
    app_port: int = 8001
    app_env: str = "development"
    log_level: str = "INFO"
    frontend_origin: str = "http://127.0.0.1:5173"

    database_url: str = Field(default="")

    sharekhan_api_key: str = ""
    sharekhan_secret_key: str = ""
    sharekhan_customer_id: str = ""
    sharekhan_vendor_key: str = ""
    sharekhan_access_token: str = ""
    sharekhan_auth_url: str = "https://api.sharekhan.com/skapi/auth/login.html"
    sharekhan_token_url: str = "https://api.sharekhan.com/skapi/services/access/token"
    sharekhan_websocket_url: str = "wss://stream.sharekhan.com/skstream/api/stream"
    token_encryption_key: str = ""

    scripmaster_url: str = ""
    historical_base_url: str = ""
    finnhub_api_key: str = ""

    max_ws_subscriptions: int = 1000
    rest_requests_per_second: int = 5
    websocket_heartbeat_seconds: int = 20
    websocket_stale_seconds: int = 45

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
