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


class LLMSettings(BaseSettings):
    model_config = SettingsConfigDict(extra="ignore")

    llm_base_url: str = Field(alias="LLM_BASE_URL")
    llm_api_key: str = Field(alias="LLM_API_KEY")
    llm_model: str = Field(alias="LLM_MODEL", default="gpt-4o-mini")
    llm_timeout_seconds: int = Field(alias="LLM_TIMEOUT_SECONDS", default=45)
    embed_base_url: str = Field(alias="EMBED_BASE_URL")
    embed_api_key: str = Field(alias="EMBED_API_KEY")
    embed_model: str = Field(alias="EMBED_MODEL", default="text-embedding-3-small")


@lru_cache
def get_llm_settings() -> LLMSettings:
    env_file = _find_env_file()
    if env_file:
        return LLMSettings(_env_file=env_file)  # type: ignore[call-arg]
    return LLMSettings()  # type: ignore[call-arg]
