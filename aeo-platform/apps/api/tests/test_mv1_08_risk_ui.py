"""MV1-08 acceptance — risk rules configuration page deliverables."""

from __future__ import annotations

from pathlib import Path

import pytest

_AEO_PLATFORM_ROOT = Path(__file__).resolve().parents[3]
_WEB_SRC = _AEO_PLATFORM_ROOT / "apps" / "web" / "src"

_RISK_UI_ARTIFACTS = [
    "app/risk/page.tsx",
    "app/api/risk/route.ts",
]


@pytest.mark.parametrize("relative_path", _RISK_UI_ARTIFACTS)
def test_mv1_08_risk_ui_artifacts_exist(relative_path: str) -> None:
    path = _WEB_SRC / relative_path
    assert path.is_file(), f"missing risk UI artifact: {relative_path}"


def test_mv1_08_sidebar_links_risk() -> None:
    content = (_WEB_SRC / "components" / "layout" / "sidebar-nav.tsx").read_text(encoding="utf-8")
    assert 'href: "/risk"' in content
    assert "风控" in content


def test_mv1_08_risk_api_router_registered() -> None:
    main_source = (_AEO_PLATFORM_ROOT / "apps" / "api" / "src" / "aeo_api" / "main.py").read_text(
        encoding="utf-8"
    )
    assert "risk" in main_source


def test_mv1_08_risk_rules_endpoint_exists() -> None:
    router_source = (
        _AEO_PLATFORM_ROOT / "apps" / "api" / "src" / "aeo_api" / "routers" / "risk.py"
    ).read_text(encoding="utf-8")
    assert "/rules" in router_source
    assert "list_risk_rules" in router_source


def test_mv1_08_risk_page_has_rules_display() -> None:
    content = (_WEB_SRC / "app" / "risk" / "page.tsx").read_text(encoding="utf-8")
    assert "L0" in content
    assert "L1" in content
    assert "L2" in content
    assert "规则" in content


def test_mv1_08_risk_page_has_evaluation_form() -> None:
    content = (_WEB_SRC / "app" / "risk" / "page.tsx").read_text(encoding="utf-8")
    assert "模拟评估" in content or "评估" in content
    assert "listing.publish" in content


def test_mv1_08_risk_page_has_audit_log() -> None:
    content = (_WEB_SRC / "app" / "risk" / "page.tsx").read_text(encoding="utf-8")
    assert "审计" in content


def test_mv1_08_risk_dsl_default_rules() -> None:
    from aeo_shared.risk_dsl import default_production_rule_set

    rule_set = default_production_rule_set()
    assert len(rule_set.rules) >= 8
    actions = {r.action.value for r in rule_set.rules}
    assert "research.read" in actions
    assert "listing.publish" in actions
    assert "account.open" in actions


def test_mv1_08_risk_engine_exposes_rule_set() -> None:
    from aeo_api.services.risk_engine import RiskEngine

    engine = RiskEngine()
    assert engine._rule_set is not None
    assert len(engine._rule_set.rules) >= 8
