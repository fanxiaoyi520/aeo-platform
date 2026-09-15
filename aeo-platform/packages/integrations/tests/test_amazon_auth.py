"""Tests for P6-16: SP-API OAuth token refresh + caching."""

from __future__ import annotations

from collections.abc import Generator
from unittest.mock import MagicMock, patch

import pytest
from aeo_integrations.amazon.auth import (
    AmazonCredentialError,
    clear_token_cache,
    get_access_token,
)


@pytest.fixture(autouse=True)
def _clear_cache() -> Generator[None, None, None]:
    clear_token_cache()
    yield
    clear_token_cache()


def test_mock_mode_returns_mock_token(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AMAZON_DATA_SOURCE", "mock")
    from aeo_integrations.amazon import config as config_module

    config_module.get_amazon_settings.cache_clear()

    token = get_access_token()
    assert token.access_token == "mock-access-token"
    assert token.expires_in == 3600


def test_spapi_missing_refresh_token_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AMAZON_DATA_SOURCE", "spapi")
    monkeypatch.setenv("SP_API_CLIENT_ID", "test-id")
    monkeypatch.setenv("SP_API_CLIENT_SECRET", "test-secret")
    monkeypatch.delenv("SP_API_REFRESH_TOKEN", raising=False)
    from aeo_integrations.amazon import config as config_module

    config_module.get_amazon_settings.cache_clear()

    with pytest.raises(AmazonCredentialError, match="SP_API_REFRESH_TOKEN"):
        get_access_token()


def test_spapi_missing_client_id_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AMAZON_DATA_SOURCE", "spapi")
    monkeypatch.delenv("SP_API_CLIENT_ID", raising=False)
    monkeypatch.setenv("SP_API_CLIENT_SECRET", "test-secret")
    monkeypatch.setenv("SP_API_REFRESH_TOKEN", "test-refresh")
    from aeo_integrations.amazon import config as config_module

    config_module.get_amazon_settings.cache_clear()

    with pytest.raises(AmazonCredentialError, match="SP_API_CLIENT_ID"):
        get_access_token()


def test_spapi_token_refresh(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AMAZON_DATA_SOURCE", "spapi")
    monkeypatch.setenv("SP_API_CLIENT_ID", "test-id")
    monkeypatch.setenv("SP_API_CLIENT_SECRET", "test-secret")
    monkeypatch.setenv("SP_API_REFRESH_TOKEN", "test-refresh")
    from aeo_integrations.amazon import config as config_module

    config_module.get_amazon_settings.cache_clear()

    mock_response = MagicMock()
    mock_response.access_token = "real-access-token"
    mock_response.expires_in = 3600
    mock_response.token_type = "bearer"

    with patch("sp_api.auth.AccessTokenClient") as mock_client_cls:
        mock_client = MagicMock()
        mock_client.get_auth.return_value = mock_response
        mock_client_cls.return_value = mock_client

        token = get_access_token()

    assert token.access_token == "real-access-token"
    assert token.expires_in == 3600
    assert token.token_type == "bearer"


def test_spapi_token_cached(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AMAZON_DATA_SOURCE", "spapi")
    monkeypatch.setenv("SP_API_CLIENT_ID", "test-id")
    monkeypatch.setenv("SP_API_CLIENT_SECRET", "test-secret")
    monkeypatch.setenv("SP_API_REFRESH_TOKEN", "test-refresh")
    from aeo_integrations.amazon import config as config_module

    config_module.get_amazon_settings.cache_clear()

    mock_response = MagicMock()
    mock_response.access_token = "cached-token"
    mock_response.expires_in = 3600
    mock_response.token_type = "bearer"

    with patch("sp_api.auth.AccessTokenClient") as mock_client_cls:
        mock_client = MagicMock()
        mock_client.get_auth.return_value = mock_response
        mock_client_cls.return_value = mock_client

        token1 = get_access_token()
        token2 = get_access_token()

    assert token1.access_token == "cached-token"
    assert token2.access_token == "cached-token"
    assert mock_client.get_auth.call_count == 1


def test_clear_token_cache_forces_refresh(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AMAZON_DATA_SOURCE", "spapi")
    monkeypatch.setenv("SP_API_CLIENT_ID", "test-id")
    monkeypatch.setenv("SP_API_CLIENT_SECRET", "test-secret")
    monkeypatch.setenv("SP_API_REFRESH_TOKEN", "test-refresh")
    from aeo_integrations.amazon import config as config_module

    config_module.get_amazon_settings.cache_clear()

    mock_response = MagicMock()
    mock_response.access_token = "fresh-token"
    mock_response.expires_in = 3600
    mock_response.token_type = "bearer"

    with patch("sp_api.auth.AccessTokenClient") as mock_client_cls:
        mock_client = MagicMock()
        mock_client.get_auth.return_value = mock_response
        mock_client_cls.return_value = mock_client

        get_access_token()
        clear_token_cache()
        get_access_token()

    assert mock_client.get_auth.call_count == 2
