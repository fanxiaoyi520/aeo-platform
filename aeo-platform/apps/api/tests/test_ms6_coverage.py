"""MS6 coverage gate acceptance."""

import tomllib
from pathlib import Path


def test_pyproject_coverage_fail_under_is_70() -> None:
    root = Path(__file__).resolve().parents[3]
    data = tomllib.loads(root.joinpath("pyproject.toml").read_text(encoding="utf-8"))
    assert data["tool"]["coverage"]["report"]["fail_under"] == 70


def test_coverage_sources_include_core_packages() -> None:
    root = Path(__file__).resolve().parents[3]
    data = tomllib.loads(root.joinpath("pyproject.toml").read_text(encoding="utf-8"))
    sources = data["tool"]["coverage"]["run"]["source"]
    assert "apps" in sources
    assert "packages" in sources
