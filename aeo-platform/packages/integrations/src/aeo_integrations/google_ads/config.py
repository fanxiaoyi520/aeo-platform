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


class GoogleAdsDataSource(StrEnum):
    MOCK = "mock"
    GOOGLE = "google"


class GoogleAdsSettings(BaseSettings):
    model_config = SettingsConfigDict(extra="ignore")

    data_source: GoogleAdsDataSource = Field(
        alias="GOOGLE_ADS_DATA_SOURCE", default=GoogleAdsDataSource.MOCK
    )
    developer_token: str = Field(alias="GOOGLE_ADS_DEVELOPER_TOKEN", default="")
    client_id: str = Field(alias="GOOGLE_ADS_CLIENT_ID", default="")
    client_secret: str = Field(alias="GOOGLE_ADS_CLIENT_SECRET", default="")
    refresh_token: str = Field(alias="GOOGLE_ADS_REFRESH_TOKEN", default="")
    customer_id: str = Field(alias="GOOGLE_ADS_CUSTOMER_ID", default="")
    api_version: str = Field(alias="GOOGLE_ADS_API_VERSION", default="v17")
    fallback_enabled: bool = Field(alias="GOOGLE_ADS_FALLBACK_ENABLED", default=True)
    request_timeout: int = Field(alias="GOOGLE_ADS_REQUEST_TIMEOUT", default=30)

    @property
    def clean_customer_id(self) -> str:
        return self.customer_id.replace("-", "")


@lru_cache
def get_google_ads_settings() -> GoogleAdsSettings:
    env_file = _find_env_file()
    if env_file:
        return GoogleAdsSettings(_env_file=env_file)  # type: ignore[call-arg]
    return GoogleAdsSettings()
