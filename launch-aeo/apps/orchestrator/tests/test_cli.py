"""CLI helper tests."""

import pytest
from aeo_orchestrator.cli import _print_human_summary


def test_print_human_summary_includes_trace_and_output(capsys: pytest.CaptureFixture[str]) -> None:
    _print_human_summary(
        {
            "task_id": "task-1",
            "status": "completed",
            "waiting_hitl": False,
            "degraded_mode": True,
            "final_output": {
                "title": "OBD2 Scanner",
                "bullets": ["Fast read", "Wide coverage"],
                "metrics": {"retry_count": 1, "compliance_passed": True},
            },
            "trace": [{"agent": "research_agent"}, {"agent": "generate_agent"}],
        }
    )
    output = capsys.readouterr().out
    assert "OBD2 Scanner" in output
    assert "Degraded mode" in output
    assert "research_agent" in output
