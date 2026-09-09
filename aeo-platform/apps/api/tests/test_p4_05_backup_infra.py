"""P4-05: Backup infrastructure tests — script, compose config, Redis persistence."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import yaml  # type: ignore[import-untyped]

INFRA_ROOT = Path(__file__).resolve().parents[3] / "infra"
SCRIPTS_ROOT = Path(__file__).resolve().parents[3] / "scripts"
COMPOSE_FILE = INFRA_ROOT / "compose" / "docker-compose.prod.yml"
BACKUP_SCRIPT = SCRIPTS_ROOT / "backup.sh"


def _load_compose() -> dict[str, Any]:
    with open(COMPOSE_FILE) as f:
        return yaml.safe_load(f)  # type: ignore[no-any-return]


class TestBackupScript:
    def test_backup_script_exists(self) -> None:
        assert BACKUP_SCRIPT.exists(), "scripts/backup.sh must exist"

    def test_backup_script_has_postgres_dump(self) -> None:
        content = BACKUP_SCRIPT.read_text()
        assert "pg_dump" in content

    def test_backup_script_has_redis_backup(self) -> None:
        content = BACKUP_SCRIPT.read_text()
        assert "BGSAVE" in content
        assert "redis" in content.lower()

    def test_backup_script_has_chroma_backup(self) -> None:
        content = BACKUP_SCRIPT.read_text()
        assert "chroma" in content.lower()
        assert "tar czf" in content

    def test_backup_script_has_manifest(self) -> None:
        content = BACKUP_SCRIPT.read_text()
        assert "manifest.txt" in content
        assert "postgres=" in content
        assert "redis=" in content
        assert "chroma=" in content

    def test_backup_script_has_retention(self) -> None:
        content = BACKUP_SCRIPT.read_text()
        assert "RETENTION_DAYS" in content
        assert "find" in content
        assert "-mtime" in content

    def test_backup_script_uses_strict_mode(self) -> None:
        content = BACKUP_SCRIPT.read_text()
        assert "set -euo pipefail" in content


class TestRedisPersistence:
    def test_redis_has_save_config(self) -> None:
        compose = _load_compose()
        redis_cmd = compose["services"]["redis"].get("command", "")
        assert "--save" in redis_cmd

    def test_redis_has_aof_enabled(self) -> None:
        compose = _load_compose()
        redis_cmd = compose["services"]["redis"].get("command", "")
        assert "--appendonly yes" in redis_cmd

    def test_redis_has_data_volume(self) -> None:
        compose = _load_compose()
        volumes = compose["services"]["redis"].get("volumes", [])
        assert any("redis_data" in v for v in volumes)


class TestComposeVolumes:
    def test_all_named_volumes_declared(self) -> None:
        compose = _load_compose()
        declared = set(compose.get("volumes", {}).keys())
        required = {"pg_data", "redis_data", "chroma_data", "prometheus_data", "grafana_data"}
        assert required.issubset(declared), f"Missing volumes: {required - declared}"

    def test_certbot_volumes_declared(self) -> None:
        compose = _load_compose()
        declared = set(compose.get("volumes", {}).keys())
        assert "certbot_certs" in declared
        assert "certbot_webroot" in declared


class TestSecurityConfig:
    def test_prometheus_not_exposed_to_host(self) -> None:
        compose = _load_compose()
        prometheus_ports = compose["services"]["prometheus"].get("ports", [])
        assert len(prometheus_ports) == 0, "Prometheus should not be exposed to host network"


class TestBackupManifestFormat:
    def test_manifest_regex_pattern(self) -> None:
        manifest_lines = [
            "timestamp=20260909_120000",
            "postgres=postgres.sql",
            "redis=redis.rdb",
            "chroma=chroma_data.tar.gz",
            "compose_file=infra/compose/docker-compose.prod.yml",
        ]
        pattern = re.compile(r"^(\w+)=(.+)$")
        for line in manifest_lines:
            m = pattern.match(line)
            assert m is not None, f"Manifest line does not match key=value format: {line}"
