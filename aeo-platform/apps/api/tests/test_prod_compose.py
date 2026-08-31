"""S6-01 — production Docker Compose profile acceptance checks."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
PROD_COMPOSE = ROOT / "infra" / "compose" / "docker-compose.prod.yml"
COMPOSE_TEXT = PROD_COMPOSE.read_text(encoding="utf-8")


def test_prod_compose_internal_data_services_have_no_host_ports() -> None:
    assert PROD_COMPOSE.is_file()
    postgres_block = COMPOSE_TEXT.split("postgres:")[1].split("\n  redis:")[0]
    redis_block = COMPOSE_TEXT.split("redis:")[1].split("\n  api:")[0]
    assert "ports:" not in postgres_block
    assert "ports:" not in redis_block


def test_prod_compose_exposes_web_and_api() -> None:
    assert '"3000:3000"' in COMPOSE_TEXT or "- 3000:3000" in COMPOSE_TEXT
    assert '"8000:8000"' in COMPOSE_TEXT or "- 8000:8000" in COMPOSE_TEXT
    assert "aeo-web-prod" in COMPOSE_TEXT
    assert "Dockerfile.web" in COMPOSE_TEXT


def test_prod_compose_api_has_rag_config() -> None:
    assert "CHROMA_PATH: data/chroma" in COMPOSE_TEXT
    assert "KNOWLEDGE_PATH: knowledge" in COMPOSE_TEXT
    assert 'RAG_USE_HASH_EMBEDDINGS: "true"' in COMPOSE_TEXT
    assert "chroma_data:/app/data/chroma" in COMPOSE_TEXT
    assert "API_BASE_URL: http://api:8000" in COMPOSE_TEXT


def test_prod_compose_resource_limits_match_performance_standards() -> None:
    assert 'cpus: "2"' in COMPOSE_TEXT
    assert "memory: 2G" in COMPOSE_TEXT
    assert 'cpus: "1"' in COMPOSE_TEXT
    assert "memory: 512M" in COMPOSE_TEXT
    assert 'cpus: "0.5"' in COMPOSE_TEXT
    assert "memory: 256M" in COMPOSE_TEXT
    assert "memory: 1G" in COMPOSE_TEXT


def test_prod_compose_scripts_exist() -> None:
    assert (ROOT / "scripts" / "prod-up.ps1").is_file()
    assert (ROOT / "scripts" / "prod-down.ps1").is_file()
    assert (ROOT / ".env.prod.example").is_file()
    assert (ROOT / "infra" / "docker" / "Dockerfile.web").is_file()
