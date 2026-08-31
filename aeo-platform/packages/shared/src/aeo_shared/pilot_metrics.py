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


def load_pilot_summary(path: Path) -> dict[str, Any]:
    data: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    return data


def evaluate_pilot_targets(summary: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Map MS7 summary to master plan §1.4 targets."""
    p95_seconds = summary.get("p95_duration_ms", 0) / 1000
    first_pass = float(summary.get("first_pass_rate", 0))
    adoption = float(summary.get("adoption_rate", 0))
    return {
        "p95_duration": {
            "metric": "P-BIZ-01 端到端耗时 p95",
            "target": "≤ 180s",
            "actual": f"{p95_seconds:.1f}s",
            "passed": p95_seconds <= 180 if summary.get("completed", 0) else None,
        },
        "first_pass_rate": {
            "metric": "人工审核一次通过率",
            "target": "≥ 60%",
            "actual": f"{first_pass * 100:.1f}%",
            "passed": first_pass >= 0.6 if summary.get("completed", 0) else None,
        },
        "adoption_rate": {
            "metric": "Listing 采纳率",
            "target": "≥ 85% 编辑距离",
            "actual": f"{adoption * 100:.1f}%",
            "passed": adoption >= 0.6 if summary.get("completed", 0) else None,
        },
    }


def render_pilot_report_markdown(
    summary: dict[str, Any],
    *,
    title: str,
    testset_path: str,
    batch_csv_path: str,
    generated_at: str,
    video_script_path: str | None = None,
    notes: str | None = None,
) -> str:
    targets = evaluate_pilot_targets(summary)
    lines = [
        f"# {title}",
        "",
        "| 属性 | 值 |",
        "|------|-----|",
        f"| **生成时间** | {generated_at} |",
        f"| **测试集** | `{testset_path}` |",
        f"| **批跑 CSV** | `{batch_csv_path}` |",
        f"| **批跑模式** | {summary.get('mode', 'live')} |",
        "",
        "## 1. 执行摘要",
        "",
        f"- 任务总数：**{summary.get('total', 0)}**",
        f"- 完成：**{summary.get('completed', 0)}**；失败：**{summary.get('failed', 0)}**",
        f"- HITL 介入率：**{float(summary.get('hitl_rate', 0)) * 100:.1f}%**",
        f"- 一次通过率：**{float(summary.get('first_pass_rate', 0)) * 100:.1f}%**",
        f"- 采纳率：**{float(summary.get('adoption_rate', 0)) * 100:.1f}%**",
        f"- 平均耗时：**{summary.get('avg_duration_ms', 0)} ms**",
        f"- p95 耗时：**{summary.get('p95_duration_ms', 0)} ms**",
        "",
        "## 2. 成功标准对照（总计划 §1.4）",
        "",
        "| 指标 | 目标 | 实测 | 结果 |",
        "|------|------|------|------|",
    ]
    for item in targets.values():
        passed = item["passed"]
        result = "⏳ 待 live 批跑" if passed is None else ("✅ 达标" if passed else "❌ 未达标")
        lines.append(f"| {item['metric']} | {item['target']} | {item['actual']} | {result} |")

    lines.extend(
        [
            "",
            "## 3. 批跑命令",
            "",
            "```powershell",
            "cd aeo-platform",
            ".\\scripts\\batch_pilot.ps1 --auto-approve",
            ".\\scripts\\generate_pilot_report.ps1 `",
            "  --summary pilot/reports/batch-<timestamp>.summary.json `",
            "  --csv pilot/reports/batch-<timestamp>.csv",
            "```",
            "",
            "## 4. 演示视频",
            "",
        ]
    )
    if video_script_path:
        lines.append(f"脚本：[`{video_script_path}`]({video_script_path})")
    else:
        lines.append("脚本：见 `docs/pilot/demo-video-script.md`")
    lines.append("")
    lines.append("> 视频文件由运营本地录制后归档（本仓库不包含视频二进制）。")
    if notes:
        lines.extend(["", "## 5. 备注", "", notes])
    lines.append("")
    return "\n".join(lines)
