"""P5-02: JWT and auth configuration."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class AuthSettings(BaseSettings):
    model_config = SettingsConfigDict(extra="ignore")

    jwt_secret_key: str = "dev-jwt-secret-change-in-production"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 15
    jwt_refresh_token_expire_days: int = 7
    admin_default_password: str = "admin123"


@lru_cache
def get_auth_settings() -> AuthSettings:
    return AuthSettings()
