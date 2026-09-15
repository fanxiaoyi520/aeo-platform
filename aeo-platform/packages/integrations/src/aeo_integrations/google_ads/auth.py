from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from typing import Any

import requests

logger = logging.getLogger(__name__)

_TOKEN_URL = "https://oauth2.googleapis.com/token"
_TOKEN_EXPIRY_BUFFER = 60


@dataclass
class GoogleAccessToken:
    access_token: str
    expires_at: float


_cached_token: GoogleAccessToken | None = None


def get_access_token(
    client_id: str,
    client_secret: str,
    refresh_token: str,
) -> GoogleAccessToken:
    global _cached_token

    if _cached_token and time.time() < _cached_token.expires_at - _TOKEN_EXPIRY_BUFFER:
        return _cached_token

    data: dict[str, str] = {
        "grant_type": "refresh_token",
        "client_id": client_id,
        "client_secret": client_secret,
        "refresh_token": refresh_token,
    }

    response = requests.post(_TOKEN_URL, data=data, timeout=15)
    response.raise_for_status()
    payload: dict[str, Any] = response.json()

    _cached_token = GoogleAccessToken(
        access_token=payload["access_token"],
        expires_at=time.time() + payload.get("expires_in", 3600),
    )
    return _cached_token
