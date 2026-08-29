from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class LLMSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    llm_base_url: str = Field(alias="LLM_BASE_URL")
    llm_api_key: str = Field(alias="LLM_API_KEY")
    llm_model: str = Field(alias="LLM_MODEL", default="gpt-4o-mini")
    llm_timeout_seconds: int = Field(alias="LLM_TIMEOUT_SECONDS", default=45)
    embed_base_url: str = Field(alias="EMBED_BASE_URL")
    embed_api_key: str = Field(alias="EMBED_API_KEY")
    embed_model: str = Field(alias="EMBED_MODEL", default="text-embedding-3-small")


@lru_cache
def get_llm_settings() -> LLMSettings:
    return LLMSettings()  # type: ignore[call-arg]
