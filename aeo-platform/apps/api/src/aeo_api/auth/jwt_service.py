"""P5-02: JWT token creation and validation."""

from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

import jwt
from pydantic import BaseModel

from aeo_api.auth.config import get_auth_settings


class TokenPayload(BaseModel):
    sub: UUID
    tid: UUID
    role: str = "member"
    exp: int
    iat: int
    type: str = "access"


def create_access_token(user_id: UUID, tenant_id: UUID, role: str) -> str:
    settings = get_auth_settings()
    now = datetime.now(UTC)
    expire = now + timedelta(minutes=settings.jwt_access_token_expire_minutes)
    payload: dict[str, Any] = {
        "sub": str(user_id),
        "tid": str(tenant_id),
        "role": role,
        "exp": int(expire.timestamp()),
        "iat": int(now.timestamp()),
        "type": "access",
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def create_refresh_token(user_id: UUID, tenant_id: UUID) -> str:
    settings = get_auth_settings()
    now = datetime.now(UTC)
    expire = now + timedelta(days=settings.jwt_refresh_token_expire_days)
    payload: dict[str, Any] = {
        "sub": str(user_id),
        "tid": str(tenant_id),
        "exp": int(expire.timestamp()),
        "iat": int(now.timestamp()),
        "type": "refresh",
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_token(token: str) -> TokenPayload:
    settings = get_auth_settings()
    data = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
    return TokenPayload(
        sub=UUID(data["sub"]),
        tid=UUID(data["tid"]),
        role=data.get("role", "member"),
        exp=data["exp"],
        iat=data["iat"],
        type=data.get("type", "access"),
    )
