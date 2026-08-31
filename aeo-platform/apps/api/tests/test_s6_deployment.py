"""S6-05 — deployment documentation and operational scripts."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
REPO_ROOT = ROOT.parent
DEPLOYMENT_DOC = REPO_ROOT / "docs" / "DEPLOYMENT.md"
BACKUP_SH = ROOT / "scripts" / "backup.sh"
BACKUP_PS1 = ROOT / "scripts" / "backup.ps1"
DEMO_PS1 = ROOT / "scripts" / "demo.ps1"


def test_deployment_doc_exists_and_covers_core_topics() -> None:
    assert DEPLOYMENT_DOC.is_file()
    text = DEPLOYMENT_DOC.read_text(encoding="utf-8")
    for topic in (
        "prod-up.ps1",
        "backup.sh",
        "demo.ps1",
        "AUTH_API_KEY",
        "CORS_ORIGINS",
        "postgres.sql",
        "chroma_data.tar.gz",
    ):
        assert topic in text, f"missing topic in DEPLOYMENT.md: {topic}"


def test_backup_script_dumps_postgres_and_chroma() -> None:
    assert BACKUP_SH.is_file()
    text = BACKUP_SH.read_text(encoding="utf-8")
    assert "pg_dump" in text
    assert "chroma_data.tar.gz" in text
    assert "/app/data/chroma" in text
    assert text.startswith("#!/usr/bin/env bash")


def test_backup_and_demo_powershell_wrappers_exist() -> None:
    assert BACKUP_PS1.is_file()
    assert DEMO_PS1.is_file()
    backup_text = BACKUP_PS1.read_text(encoding="utf-8")
    demo_text = DEMO_PS1.read_text(encoding="utf-8")
    assert "backup.sh" in backup_text
    assert "/health" in demo_text
    assert "/api/v1/audit-logs" in demo_text


def test_backups_dir_gitignored() -> None:
    gitignore = (ROOT / ".gitignore").read_text(encoding="utf-8")
    assert "backups/" in gitignore
