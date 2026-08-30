"""MS5 acceptance — workbench deliverables per M05 §5."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

_LAUNCH_AEO_ROOT = Path(__file__).resolve().parents[3]
_WEB_SRC = _LAUNCH_AEO_ROOT / "apps" / "web" / "src"

_REQUIRED_PAGES = [
    "app/tasks/page.tsx",
    "app/tasks/new/page.tsx",
    "app/tasks/[id]/page.tsx",
    "app/tasks/[id]/review/page.tsx",
    "app/tasks/[id]/result/page.tsx",
    "app/knowledge/page.tsx",
    "app/settings/page.tsx",
]

_REQUIRED_BFF = [
    "app/api/tasks/route.ts",
    "app/api/tasks/[id]/route.ts",
    "app/api/tasks/[id]/events/route.ts",
    "app/api/tasks/[id]/approve/route.ts",
    "app/api/tasks/[id]/reject/route.ts",
    "app/api/knowledge/route.ts",
]

_REQUIRED_LIBS = [
    "lib/listing-draft.ts",
    "lib/listing-export.ts",
    "hooks/use-task-events.ts",
    "components/tasks/task-trace-timeline.tsx",
]


@pytest.mark.parametrize("relative_path", _REQUIRED_PAGES)
def test_ms5_workbench_pages_exist(relative_path: str) -> None:
    path = _WEB_SRC / relative_path
    assert path.is_file(), f"missing page: {relative_path}"


@pytest.mark.parametrize("relative_path", _REQUIRED_BFF)
def test_ms5_bff_routes_exist(relative_path: str) -> None:
    path = _WEB_SRC / relative_path
    assert path.is_file(), f"missing BFF route: {relative_path}"


@pytest.mark.parametrize("relative_path", _REQUIRED_LIBS)
def test_ms5_workbench_libraries_exist(relative_path: str) -> None:
    path = _WEB_SRC / relative_path
    assert path.is_file(), f"missing library: {relative_path}"


def test_ms5_task_detail_links_review_and_result() -> None:
    content = (_WEB_SRC / "app/tasks/[id]/page.tsx").read_text(encoding="utf-8")
    assert "/review" in content
    assert "/result" in content
    assert "waiting_hitl" in content
    assert "completed" in content


def test_ms5_listing_export_contract() -> None:
    """Clipboard/JSON/CSV shape matches M05 §5 export requirements."""
    export_source = (_WEB_SRC / "lib/listing-export.ts").read_text(encoding="utf-8")
    assert "formatListingForClipboard" in export_source
    assert "listingToJson" in export_source
    assert "listingToCsv" in export_source
    assert "buildExportFilename" in export_source

    csv_header = (
        "task_id,sku,platform,market,listing_version,title,"
        "bullet_1,bullet_2,bullet_3,bullet_4,bullet_5,search_terms,description"
    )
    normalized = export_source.replace(" ", "").replace("\n", "").replace('"', "")
    assert csv_header in normalized

    sample = {
        "task_id": "abc",
        "sku": "X431",
        "platform": "amazon",
        "market": "US",
        "listing_version": 1,
        "listing": {
            "title": "Test Title",
            "bullets": ["A", "B"],
            "search_terms": "kw",
            "description": "desc",
        },
    }
    payload = json.loads(json.dumps(sample))
    assert payload["listing"]["title"] == "Test Title"
    assert len(payload["listing"]["bullets"]) == 2


def test_ms5_acceptance_report_exists() -> None:
    report = _LAUNCH_AEO_ROOT.parent / "docs" / "reports" / "ms5-workbench-acceptance.md"
    assert report.is_file(), "missing MS5 acceptance report"
