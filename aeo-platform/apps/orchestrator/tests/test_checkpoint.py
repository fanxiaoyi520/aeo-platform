import pytest
from aeo_orchestrator.checkpoint import (
    create_memory_checkpointer,
    get_checkpoint_db_url,
    normalize_postgres_conn_string,
)


def test_normalize_postgres_conn_string() -> None:
    assert (
        normalize_postgres_conn_string("postgresql+psycopg://aeo:aeo@localhost:5432/aeo")
        == "postgresql://aeo:aeo@localhost:5432/aeo"
    )


def test_create_memory_checkpointer() -> None:
    saver = create_memory_checkpointer()
    assert saver is not None


def test_get_checkpoint_db_url_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DB_URL_SYNC", "postgresql+psycopg://aeo:aeo@localhost:5432/aeo")
    assert get_checkpoint_db_url() == "postgresql://aeo:aeo@localhost:5432/aeo"
