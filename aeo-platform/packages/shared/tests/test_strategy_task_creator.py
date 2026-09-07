"""MV4-05 — ActionMapping + StrategyTaskCreator tests."""

from __future__ import annotations

from aeo_shared.agent_catalog import get_default_registry
from aeo_shared.strategy_task_creator import (
    StrategyTaskCreator,
    get_action_mapping,
)
from aeo_shared.task_scheduler import AgentTaskScheduler, TaskPriority


class TestActionMapping:
    def test_default_mapping_has_expected_actions(self) -> None:
        mapping = get_action_mapping()
        assert "increase_ad_spend" in mapping
        assert "restock" in mapping
        assert "optimize_listing" in mapping

    def test_mapping_entry_has_agent_and_capability(self) -> None:
        mapping = get_action_mapping()
        entry = mapping["increase_ad_spend"]
        assert entry.agent_id == "ads_agent"
        assert entry.capability == "ads.suggest"

    def test_mapping_entry_has_default_priority(self) -> None:
        mapping = get_action_mapping()
        entry = mapping["optimize_listing"]
        assert entry.priority == TaskPriority.NORMAL

    def test_unknown_action_returns_none(self) -> None:
        mapping = get_action_mapping()
        assert mapping.resolve("nonexistent_action") is None

    def test_known_action_returns_entry(self) -> None:
        mapping = get_action_mapping()
        entry = mapping.resolve("restock")
        assert entry is not None
        assert entry.agent_id == "operations_agent"


class TestStrategyTaskCreator:
    def _creator(self) -> StrategyTaskCreator:
        registry = get_default_registry()
        scheduler = AgentTaskScheduler(registry)
        return StrategyTaskCreator(scheduler=scheduler, mapping=get_action_mapping())

    def test_create_tasks_from_suggestions(self) -> None:
        creator = self._creator()
        suggestions = [
            {"action": "increase_ad_spend", "sku": "SKU-001", "reason": "High ROI"},
            {"action": "restock", "sku": "SKU-002", "reason": "Low inventory"},
        ]
        tasks = creator.create_tasks(suggestions=suggestions, parent_task_id="analytics-1")
        assert len(tasks) == 2
        assert tasks[0].agent_id == "ads_agent"
        assert tasks[0].capability == "ads.suggest"
        assert tasks[0].parent_task_id == "analytics-1"
        assert tasks[0].payload["sku"] == "SKU-001"
        assert tasks[0].payload["reason"] == "High ROI"
        assert tasks[1].agent_id == "operations_agent"

    def test_unknown_action_skipped(self) -> None:
        creator = self._creator()
        suggestions = [
            {"action": "unknown_thing", "sku": "SKU-001", "reason": "test"},
            {"action": "increase_ad_spend", "sku": "SKU-002", "reason": "good ROI"},
        ]
        tasks = creator.create_tasks(suggestions=suggestions)
        assert len(tasks) == 1
        assert tasks[0].agent_id == "ads_agent"

    def test_empty_suggestions_returns_empty(self) -> None:
        creator = self._creator()
        tasks = creator.create_tasks(suggestions=[])
        assert tasks == []

    def test_parent_task_id_propagated(self) -> None:
        creator = self._creator()
        suggestions = [{"action": "restock", "sku": "SKU-001", "reason": "low"}]
        tasks = creator.create_tasks(suggestions=suggestions, parent_task_id="parent-123")
        assert tasks[0].parent_task_id == "parent-123"

    def test_payload_includes_action_and_sku(self) -> None:
        creator = self._creator()
        suggestions = [{"action": "increase_ad_spend", "sku": "SKU-X", "reason": "ROI > 3x"}]
        tasks = creator.create_tasks(suggestions=suggestions)
        assert tasks[0].payload["action"] == "increase_ad_spend"
        assert tasks[0].payload["sku"] == "SKU-X"
        assert tasks[0].payload["reason"] == "ROI > 3x"
