"""Redact sensitive fields from logs and API payloads per M06 §4."""

from __future__ import annotations

from typing import Any

REDACTED = "***"

SENSITIVE_KEYS: frozenset[str] = frozenset(
    {
        "api_key",
        "password",
        "supplier_price",
        "cost_price",
    }
)


def is_sensitive_key(key: str) -> bool:
    return key.lower() in SENSITIVE_KEYS


def redact_value(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _redact_mapping(key, nested) for key, nested in value.items()}
    if isinstance(value, list):
        return [redact_value(item) for item in value]
    if isinstance(value, tuple):
        return tuple(redact_value(item) for item in value)
    return value


def _redact_mapping(key: str, value: Any) -> Any:
    if is_sensitive_key(key):
        return REDACTED
    return redact_value(value)
