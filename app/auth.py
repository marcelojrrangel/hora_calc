import secrets
from datetime import datetime, timedelta
from typing import Optional

import bcrypt
from fastapi import Cookie, HTTPException, Request, Response
from starlette.status import HTTP_401_UNAUTHORIZED

from app.config import settings

_sessions: dict[str, datetime] = {}

SESSION_DURATION_HOURS = 24


def verify_password(password: str) -> bool:
    stored = settings.auth_password_hash
    if not stored:
        return False

    if not stored.startswith("$2"):
        return False

    try:
        return bcrypt.checkpw(
            password.encode("utf-8"), stored.encode("utf-8")
        )
    except (ValueError, TypeError):
        return False


def create_session() -> str:
    token = secrets.token_urlsafe(32)
    _sessions[token] = datetime.now() + timedelta(hours=SESSION_DURATION_HOURS)
    return token


def validate_session(token: str) -> bool:
    if token not in _sessions:
        return False
    if datetime.now() > _sessions[token]:
        del _sessions[token]
        return False
    return True


def destroy_session(token: str) -> None:
    _sessions.pop(token, None)


def cleanup_expired_sessions() -> None:
    now = datetime.now()
    expired = [t for t, exp in _sessions.items() if now > exp]
    for token in expired:
        del _sessions[token]


async def get_current_session_token(
    request: Request,
    session_token: Optional[str] = Cookie(None),
) -> Optional[str]:
    if session_token and validate_session(session_token):
        return session_token
    return None


async def require_auth(
    request: Request,
    session_token: Optional[str] = Cookie(None),
) -> str:
    if session_token and validate_session(session_token):
        return session_token

    if request.url.path in ("/login", "/static/login.css"):
        return ""

    raise HTTPException(
        status_code=HTTP_401_UNAUTHORIZED,
        detail="Not authenticated",
        headers={"WWW-Authenticate": "Bearer"},
    )


def set_session_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key="session_token",
        value=token,
        httponly=True,
        secure=settings.environment == "production",
        samesite="lax",
        max_age=SESSION_DURATION_HOURS * 3600,
    )


def clear_session_cookie(response: Response) -> None:
    response.delete_cookie(key="session_token")
