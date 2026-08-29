from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class RagSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    chroma_path: str = Field(alias="CHROMA_PATH", default="data/chroma")
    knowledge_path: str = Field(alias="KNOWLEDGE_PATH", default="knowledge")
    rag_top_k: int = Field(alias="RAG_TOP_K", default=5)
    rag_score_threshold: float = Field(alias="RAG_SCORE_THRESHOLD", default=0.7)
    rag_chunk_size: int = Field(alias="RAG_CHUNK_SIZE", default=512)
    rag_chunk_overlap: int = Field(alias="RAG_CHUNK_OVERLAP", default=64)
    chroma_collection: str = Field(alias="CHROMA_COLLECTION", default="aeo_knowledge")


@lru_cache
def get_rag_settings() -> RagSettings:
    return RagSettings()


def resolve_project_path(relative: str) -> Path:
    """Resolve path relative to launch-aeo monorepo root."""
    here = Path(__file__).resolve()
    for parent in here.parents:
        if (parent / "pyproject.toml").exists() and (parent / "knowledge").exists():
            return (parent / relative).resolve()
        if (parent / "pyproject.toml").exists() and parent.name == "launch-aeo":
            return (parent / relative).resolve()
    # fallback: packages/rag/src/aeo_rag -> launch-aeo
    return (here.parents[4] / relative).resolve()
