from __future__ import annotations

from enum import StrEnum
from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


def _find_env_file() -> str | None:
    for directory in (Path.cwd(), *Path.cwd().parents):
        candidate = directory / ".env"
        if candidate.is_file():
            return str(candidate)
    return None


class ShopifyDataSource(StrEnum):
    MOCK = "mock"
    SHOPIFY = "shopify"


class ShopifySettings(BaseSettings):
    model_config = SettingsConfigDict(extra="ignore")

    data_source: ShopifyDataSource = Field(
        alias="SHOPIFY_DATA_SOURCE", default=ShopifyDataSource.MOCK
    )
    store_url: str = Field(alias="SHOPIFY_STORE_URL", default="")
    access_token: str = Field(alias="SHOPIFY_ACCESS_TOKEN", default="")
    api_version: str = Field(alias="SHOPIFY_API_VERSION", default="2024-01")
    fallback_enabled: bool = Field(alias="SHOPIFY_FALLBACK_ENABLED", default=True)
    request_timeout: int = Field(alias="SHOPIFY_REQUEST_TIMEOUT", default=30)


@lru_cache
def get_shopify_settings() -> ShopifySettings:
    env_file = _find_env_file()
    if env_file:
        return ShopifySettings(_env_file=env_file)  # type: ignore[call-arg]
    return ShopifySettings()
