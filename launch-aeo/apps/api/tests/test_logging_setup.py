"""Logging setup smoke tests."""

import structlog
from aeo_api.logging_setup import _redact_sensitive_fields, setup_logging


def test_setup_logging_debug_and_production_modes() -> None:
    setup_logging(debug=True)
    logger = structlog.get_logger("test.debug")
    logger.info("debug mode", api_key="secret")

    setup_logging(debug=False)
    logger = structlog.get_logger("test.prod")
    redacted = _redact_sensitive_fields(
        __import__("logging").getLogger("test"),
        "info",
        {"api_key": "secret", "event": "prod"},
    )
    assert redacted["api_key"] == "***"
