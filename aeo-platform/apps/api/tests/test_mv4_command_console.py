"""MV4-07 acceptance — six-agent command console deliverables."""

from __future__ import annotations

from pathlib import Path

import pytest

_AEO_PLATFORM_ROOT = Path(__file__).resolve().parents[3]
_WEB_SRC = _AEO_PLATFORM_ROOT / "apps" / "web" / "src"

_COMMAND_CONSOLE_ARTIFACTS = [
    "app/agents/page.tsx",
    "app/api/agents/route.ts",
    "components/agents/agent-command-grid.tsx",
    "components/agents/subgraph-pipeline.tsx",
    "lib/agent-display.ts",
]


@pytest.mark.parametrize("relative_path", _COMMAND_CONSOLE_ARTIFACTS)
def test_mv4_command_console_artifacts_exist(relative_path: str) -> None:
    path = _WEB_SRC / relative_path
    assert path.is_file(), f"missing command console artifact: {relative_path}"


def test_mv4_sidebar_links_command_console() -> None:
    content = (_WEB_SRC / "components/layout/sidebar-nav.tsx").read_text(encoding="utf-8")
    assert 'href: "/agents"' in content
    assert "指挥台" in content


def test_mv4_agents_api_router_registered() -> None:
    main_source = (_AEO_PLATFORM_ROOT / "apps" / "api" / "src" / "aeo_api" / "main.py").read_text(
        encoding="utf-8"
    )
    assert "agents" in main_source
