from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_env: str = Field(alias="APP_ENV", default="development")
    app_name: str = Field(alias="APP_NAME", default="launch-aeo")
    app_debug: bool = Field(alias="APP_DEBUG", default=False)

    api_host: str = Field(alias="API_HOST", default="0.0.0.0")
    api_port: int = Field(alias="API_PORT", default=8000)

    db_url: str = Field(alias="DB_URL")
    db_url_sync: str = Field(alias="DB_URL_SYNC")

    redis_url: str = Field(alias="REDIS_URL", default="redis://localhost:6379/0")

    auth_api_key: str = Field(alias="AUTH_API_KEY", default="dev-api-key")

    agent_max_concurrent: int = Field(alias="AGENT_MAX_CONCURRENT", default=3)
    rate_limit_per_minute: int = Field(alias="RATE_LIMIT_PER_MINUTE", default=100)


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
