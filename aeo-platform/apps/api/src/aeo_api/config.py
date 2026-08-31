from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

DEFAULT_DEV_API_KEYS: frozenset[str] = frozenset(
    {
        "dev-api-key",
        "dev-api-key-change-in-production",
    }
)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_env: str = Field(alias="APP_ENV", default="development")
    app_name: str = Field(alias="APP_NAME", default="aeo-platform")
    app_debug: bool = Field(alias="APP_DEBUG", default=False)

    api_host: str = Field(alias="API_HOST", default="0.0.0.0")
    api_port: int = Field(alias="API_PORT", default=8000)

    db_url: str = Field(alias="DB_URL")
    db_url_sync: str = Field(alias="DB_URL_SYNC")

    redis_url: str = Field(alias="REDIS_URL", default="redis://localhost:6379/0")

    auth_api_key: str = Field(alias="AUTH_API_KEY", default="dev-api-key")

    agent_max_concurrent: int = Field(alias="AGENT_MAX_CONCURRENT", default=3)
    rate_limit_per_minute: int = Field(alias="RATE_LIMIT_PER_MINUTE", default=100)
    cors_origins: str = Field(alias="CORS_ORIGINS", default="")

    def get_cors_origins(self) -> list[str]:
        if self.cors_origins.strip():
            return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]
        if self.app_env == "production":
            return []
        return ["http://localhost:3000", "http://127.0.0.1:3000"]


def validate_production_settings(settings: Settings) -> None:
    if settings.app_env != "production":
        return
    if settings.auth_api_key in DEFAULT_DEV_API_KEYS:
        raise RuntimeError(
            "AUTH_API_KEY must be changed from the default dev value when APP_ENV=production"
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
