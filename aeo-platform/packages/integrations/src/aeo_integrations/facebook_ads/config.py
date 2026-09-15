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


class FacebookAdsDataSource(StrEnum):
    MOCK = "mock"
    FACEBOOK = "facebook"


class FacebookAdsSettings(BaseSettings):
    model_config = SettingsConfigDict(extra="ignore")

    data_source: FacebookAdsDataSource = Field(
        alias="FACEBOOK_ADS_DATA_SOURCE", default=FacebookAdsDataSource.MOCK
    )
    access_token: str = Field(alias="FACEBOOK_ADS_ACCESS_TOKEN", default="")
    ad_account_id: str = Field(alias="FACEBOOK_ADS_AD_ACCOUNT_ID", default="")
    api_version: str = Field(alias="FACEBOOK_ADS_API_VERSION", default="v19.0")
    fallback_enabled: bool = Field(alias="FACEBOOK_ADS_FALLBACK_ENABLED", default=True)
    request_timeout: int = Field(alias="FACEBOOK_ADS_REQUEST_TIMEOUT", default=30)


@lru_cache
def get_facebook_ads_settings() -> FacebookAdsSettings:
    env_file = _find_env_file()
    if env_file:
        return FacebookAdsSettings(_env_file=env_file)  # type: ignore[call-arg]
    return FacebookAdsSettings()
