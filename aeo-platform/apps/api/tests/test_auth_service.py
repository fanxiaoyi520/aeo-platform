"""P5-02: Auth service unit tests."""

import os
from datetime import UTC, datetime, timedelta
from uuid import uuid4

os.environ.setdefault("DB_URL", "postgresql+asyncpg://aeo:aeo@localhost:5432/aeo")
os.environ.setdefault("DB_URL_SYNC", "postgresql+psycopg://aeo:aeo@localhost:5432/aeo")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("LLM_BASE_URL", "https://api.openai.com/v1")
os.environ.setdefault("LLM_API_KEY", "test-key")
os.environ.setdefault("EMBED_BASE_URL", "https://api.openai.com/v1")
os.environ.setdefault("EMBED_API_KEY", "test-key")
os.environ.setdefault("AUTH_API_KEY", "dev-api-key-change-in-production")

from aeo_api.auth.config import AuthSettings, get_auth_settings
from aeo_api.auth.jwt_service import (
    TokenPayload,
    create_access_token,
    create_refresh_token,
    decode_token,
)
from aeo_api.auth.passwords import hash_password, verify_password


def test_hash_and_verify_password() -> None:
    hashed = hash_password("secure123")
    assert hashed != "secure123"
    assert verify_password("secure123", hashed)
    assert not verify_password("wrong", hashed)


def test_auth_settings_defaults() -> None:
    settings = AuthSettings()
    assert settings.jwt_algorithm == "HS256"
    assert settings.jwt_access_token_expire_minutes == 15
    assert settings.jwt_refresh_token_expire_days == 7


def test_get_auth_settings_cached() -> None:
    s1 = get_auth_settings()
    s2 = get_auth_settings()
    assert s1 is s2


def test_create_access_token() -> None:
    uid = uuid4()
    tid = uuid4()
    token = create_access_token(uid, tid, "admin")
    assert isinstance(token, str)
    assert len(token) > 0


def test_create_refresh_token() -> None:
    uid = uuid4()
    tid = uuid4()
    token = create_refresh_token(uid, tid)
    assert isinstance(token, str)
    assert len(token) > 0


def test_decode_access_token() -> None:
    uid = uuid4()
    tid = uuid4()
    token = create_access_token(uid, tid, "owner")
    payload = decode_token(token)
    assert payload.sub == uid
    assert payload.tid == tid
    assert payload.role == "owner"
    assert payload.type == "access"


def test_decode_refresh_token() -> None:
    uid = uuid4()
    tid = uuid4()
    token = create_refresh_token(uid, tid)
    payload = decode_token(token)
    assert payload.sub == uid
    assert payload.tid == tid
    assert payload.type == "refresh"


def test_decode_invalid_token_raises() -> None:
    import jwt as pyjwt
    import pytest

    with pytest.raises(pyjwt.DecodeError):
        decode_token("invalid.token.here")


def test_decode_expired_token_raises() -> None:
    import jwt as pyjwt
    import pytest

    settings = get_auth_settings()
    past = datetime.now(UTC) - timedelta(hours=1)
    payload = {
        "sub": str(uuid4()),
        "tid": str(uuid4()),
        "role": "member",
        "exp": int(past.timestamp()),
        "iat": int((past - timedelta(minutes=15)).timestamp()),
        "type": "access",
    }
    expired_token = pyjwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
    with pytest.raises(pyjwt.ExpiredSignatureError):
        decode_token(expired_token)


def test_token_payload_model() -> None:
    uid = uuid4()
    tid = uuid4()
    now = datetime.now(UTC)
    tp = TokenPayload(
        sub=uid,
        tid=tid,
        role="admin",
        exp=int(now.timestamp()) + 900,
        iat=int(now.timestamp()),
        type="access",
    )
    assert tp.sub == uid
    assert tp.tid == tid
    assert tp.role == "admin"
