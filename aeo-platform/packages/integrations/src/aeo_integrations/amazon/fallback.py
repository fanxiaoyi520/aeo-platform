from __future__ import annotations

import logging
import time
from typing import Any

import requests

from aeo_integrations.amazon.auth import AmazonCredentialError

logger = logging.getLogger(__name__)

_FALLBACK_ERRORS: tuple[type[Exception], ...] = (
    requests.exceptions.ConnectionError,
    requests.exceptions.Timeout,
    requests.exceptions.HTTPError,
    AmazonCredentialError,
)


def _is_fallback_error(exc: Exception) -> bool:
    if isinstance(exc, _FALLBACK_ERRORS):
        return True
    exc_type = type(exc)
    module = getattr(exc_type, "__module__", "") or ""
    return "sp_api" in module


class FallbackWrapper:
    def __init__(
        self,
        primary: Any,
        fallback: Any,
        *,
        max_retries: int = 2,
        backoff_base: float = 0.5,
        primary_name: str = "spapi",
    ) -> None:
        self._primary = primary
        self._fallback = fallback
        self._max_retries = max_retries
        self._backoff_base = backoff_base
        self._primary_name = primary_name
        self._degraded = False

    @property
    def data_source(self) -> str:
        if self._degraded:
            return f"{self._primary_name}-degraded"
        return self._primary_name

    def __getattr__(self, name: str) -> Any:
        if name.startswith("_"):
            msg = f"'{type(self).__name__}' object has no attribute '{name}'"
            raise AttributeError(msg)

        primary_method = getattr(self._primary, name)
        fallback_method = getattr(self._fallback, name)

        if not callable(primary_method):
            return primary_method

        def wrapper(*args: Any, **kwargs: Any) -> Any:
            return self._call_with_fallback(name, primary_method, fallback_method, *args, **kwargs)

        return wrapper

    def _call_with_fallback(
        self,
        method_name: str,
        primary_method: Any,
        fallback_method: Any,
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        last_error: Exception | None = None

        for attempt in range(self._max_retries + 1):
            try:
                result = primary_method(*args, **kwargs)
                if self._degraded:
                    logger.info(
                        "%s recovered from degradation for %s",
                        self._primary_name,
                        method_name,
                    )
                    self._degraded = False
                return result
            except (KeyError, ValueError, TypeError):
                raise
            except Exception as exc:
                last_error = exc
                if not _is_fallback_error(exc):
                    raise
                if attempt < self._max_retries:
                    delay = self._backoff_base * (2**attempt)
                    logger.warning(
                        "%s %s attempt %d failed (%s), retrying in %.1fs",
                        self._primary_name,
                        method_name,
                        attempt + 1,
                        type(exc).__name__,
                        delay,
                    )
                    time.sleep(delay)

        self._degraded = True
        logger.warning(
            "%s %s failed after %d attempts (%s), falling back to mock",
            self._primary_name,
            method_name,
            self._max_retries + 1,
            type(last_error).__name__ if last_error else "unknown",
        )
        return fallback_method(*args, **kwargs)
