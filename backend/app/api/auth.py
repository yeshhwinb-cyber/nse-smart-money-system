from __future__ import annotations

from pydantic import BaseModel
from fastapi import APIRouter

from app.auth.auth_service import auth_service
from app.websocket.sharekhan_ws import sharekhan_ws_service

router = APIRouter(prefix="/api/auth", tags=["auth"])


class RequestTokenPayload(BaseModel):
    request_token: str


@router.get("/sharekhan/login-url")
async def sharekhan_login_url(state: str | None = None) -> dict[str, str]:
    return {"status": "OK", "login_url": auth_service.build_auth_url(state)}


@router.post("/sharekhan/request-token")
async def apply_request_token(payload: RequestTokenPayload) -> dict[str, object]:
    result = await auth_service.process_request_token(payload.request_token)
    if result.get("status") == "TOKEN_ACTIVE":
        await sharekhan_ws_service.restart()
    return result


@router.get("/sharekhan/session")
async def sharekhan_session() -> dict[str, object]:
    from app.auth.session_manager import session_manager

    return session_manager.health()
