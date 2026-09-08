"""MV4-03 acceptance tests — AfterSalesScript + ScriptLibrary."""

from __future__ import annotations


def test_after_sales_script_dataclass() -> None:
    from aeo_shared.after_sales_scripts import AfterSalesScript

    script = AfterSalesScript(
        script_id="return-001",
        scenario="return",
        platform="amazon",
        template_text="We're sorry to hear you'd like to return this item.",
        keywords=["return", "send back", "refund"],
        escalation_conditions=[],
        confidence_threshold=0.6,
    )
    assert script.script_id == "return-001"
    assert script.scenario == "return"
    assert script.platform == "amazon"
    assert len(script.keywords) == 3


def test_script_library_builtin_has_at_least_5_scenarios() -> None:
    from aeo_shared.after_sales_scripts import ScriptLibrary

    library = ScriptLibrary()
    all_scripts = library.list_all()
    assert len(all_scripts) >= 5

    scenarios = {s.scenario for s in all_scripts}
    assert "return" in scenarios
    assert "refund" in scenarios
    assert "shipping" in scenarios


def test_script_library_match_by_scenario() -> None:
    from aeo_shared.after_sales_scripts import ScriptLibrary

    library = ScriptLibrary()
    results = library.match(scenario="return", platform="amazon")
    assert len(results) >= 1
    assert all(r.scenario == "return" for r in results)


def test_script_library_match_by_scenario_no_results() -> None:
    from aeo_shared.after_sales_scripts import ScriptLibrary

    library = ScriptLibrary()
    results = library.match(scenario="nonexistent", platform="amazon")
    assert len(results) == 0


def test_script_library_get_best() -> None:
    from aeo_shared.after_sales_scripts import ScriptLibrary

    library = ScriptLibrary()
    best = library.get_best(scenario="return", platform="amazon")
    assert best is not None
    assert best.scenario == "return"
    assert best.platform == "amazon"


def test_script_library_get_best_missing() -> None:
    from aeo_shared.after_sales_scripts import ScriptLibrary

    library = ScriptLibrary()
    best = library.get_best(scenario="nonexistent", platform="amazon")
    assert best is None


def test_script_library_filter_by_platform() -> None:
    from aeo_shared.after_sales_scripts import ScriptLibrary

    library = ScriptLibrary()
    amazon_scripts = library.filter_by(platform="amazon")
    assert len(amazon_scripts) >= 1
    assert all(s.platform == "amazon" for s in amazon_scripts)


def test_script_library_list_scenarios() -> None:
    from aeo_shared.after_sales_scripts import ScriptLibrary

    library = ScriptLibrary()
    scenarios = library.list_scenarios()
    assert "return" in scenarios
    assert "refund" in scenarios
    assert "shipping" in scenarios


def test_script_library_singleton() -> None:
    from aeo_shared.after_sales_scripts import get_script_library

    lib1 = get_script_library()
    lib2 = get_script_library()
    assert lib1 is lib2


def test_after_sales_script_to_dict() -> None:
    from aeo_shared.after_sales_scripts import AfterSalesScript

    script = AfterSalesScript(
        script_id="test-001",
        scenario="return",
        platform="amazon",
        template_text="Test template",
        keywords=["test"],
    )
    d = script.to_dict()
    assert d["script_id"] == "test-001"
    assert d["scenario"] == "return"
    assert d["platform"] == "amazon"
    assert d["template_text"] == "Test template"
