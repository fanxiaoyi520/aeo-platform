"""Pilot batch metrics — MS7 S7-02 per M07 §2."""

from __future__ import annotations

import csv
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class PilotRunRecord:
    pilot_id: str
    sku: str
    platform: str
    market: str
    status: str
    duration_ms: int
    hitl_required: bool
    hitl_approved_first_try: bool
    compliance_retries: int
    degraded_mode: bool
    adoption_score: float | None
    error: str | None = None


PILOT_CSV_FIELDS: tuple[str, ...] = tuple(PilotRunRecord.__dataclass_fields__.keys())


def load_pilot_testset(path: Path) -> list[dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    items = data.get("items")
    if not isinstance(items, list) or not items:
        raise ValueError(f"invalid pilot testset: {path}")
    return items


def build_product_info(item: dict[str, Any]) -> dict[str, Any]:
    product_info: dict[str, Any] = {}
    competitors = item.get("competitor_asins")
    if isinstance(competitors, list) and competitors:
        product_info["competitor_asins"] = competitors
    keywords = item.get("keywords")
    if isinstance(keywords, list) and keywords:
        product_info["keywords"] = keywords
    return product_info


def compute_adoption_score(
    generated: dict[str, Any] | None,
    final_output: dict[str, Any] | None,
) -> float | None:
    if final_output is None:
        return None
    if not generated:
        return 1.0
    gen_title = str(generated.get("title", ""))
    fin_title = str(final_output.get("title", ""))
    if not gen_title or not fin_title:
        return None
    if gen_title == fin_title:
        return 1.0
    max_len = max(len(gen_title), len(fin_title), 1)
    # Simple character overlap ratio as a lightweight edit-distance proxy.
    common = sum(1 for left, right in zip(gen_title, fin_title, strict=False) if left == right)
    return round(common / max_len, 4)


def extract_pilot_record(
    item: dict[str, Any],
    *,
    duration_ms: int,
    status: str,
    hitl_required: bool,
    auto_approved: bool,
    degraded_mode: bool,
    compliance_retries: int,
    generated: dict[str, Any] | None,
    final_output: dict[str, Any] | None,
    error: str | None = None,
) -> PilotRunRecord:
    hitl_first_try = hitl_required and auto_approved and status == "completed" and error is None
    return PilotRunRecord(
        pilot_id=str(item["id"]),
        sku=str(item["sku"]),
        platform=str(item["platform"]),
        market=str(item.get("market", "US")),
        status=status,
        duration_ms=duration_ms,
        hitl_required=hitl_required,
        hitl_approved_first_try=hitl_first_try,
        compliance_retries=compliance_retries,
        degraded_mode=degraded_mode,
        adoption_score=compute_adoption_score(generated, final_output),
        error=error,
    )


def summarize_pilot_runs(records: list[PilotRunRecord]) -> dict[str, Any]:
    total = len(records)
    if total == 0:
        return {"total": 0}

    completed = [record for record in records if record.status == "completed"]
    hitl = [record for record in records if record.hitl_required]
    degraded = [record for record in records if record.degraded_mode]
    adopted = [
        record
        for record in records
        if record.adoption_score is not None and record.adoption_score >= 0.85
    ]
    durations = [record.duration_ms for record in completed]

    p95_duration_ms = 0
    if durations:
        sorted_durations = sorted(durations)
        p95_index = max(0, int(len(sorted_durations) * 0.95) - 1)
        p95_duration_ms = sorted_durations[p95_index]

    return {
        "total": total,
        "completed": len(completed),
        "failed": sum(1 for record in records if record.status == "failed"),
        "hitl_rate": round(len(hitl) / total, 4),
        "first_pass_rate": round(
            sum(1 for record in records if record.hitl_approved_first_try) / total,
            4,
        ),
        "degraded_rate": round(len(degraded) / total, 4),
        "adoption_rate": round(len(adopted) / total, 4) if total else 0.0,
        "avg_duration_ms": round(sum(durations) / len(durations)) if durations else 0,
        "p95_duration_ms": p95_duration_ms,
    }


def write_pilot_csv(records: list[PilotRunRecord], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(PILOT_CSV_FIELDS))
        writer.writeheader()
        for record in records:
            writer.writerow(asdict(record))


def write_pilot_summary(summary: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
