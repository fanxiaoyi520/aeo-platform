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


class AmazonDataSource(StrEnum):
    MOCK = "mock"
    SPAPI = "spapi"


class AmazonSettings(BaseSettings):
    model_config = SettingsConfigDict(extra="ignore")

    data_source: AmazonDataSource = Field(alias="AMAZON_DATA_SOURCE", default=AmazonDataSource.MOCK)
    marketplace_id: str = Field(alias="AMAZON_MARKETPLACE_ID", default="ATVPDKIKX0DER")
    region: str = Field(alias="AMAZON_REGION", default="us-east-1")
    sp_api_client_id: str = Field(alias="SP_API_CLIENT_ID", default="")
    sp_api_client_secret: str = Field(alias="SP_API_CLIENT_SECRET", default="")
    sp_api_refresh_token: str = Field(alias="SP_API_REFRESH_TOKEN", default="")


@lru_cache
def get_amazon_settings() -> AmazonSettings:
    env_file = _find_env_file()
    if env_file:
        return AmazonSettings(_env_file=env_file)  # type: ignore[call-arg]
    return AmazonSettings()
