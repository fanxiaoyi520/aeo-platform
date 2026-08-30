#!/usr/bin/env python3
"""Generate MS7 pilot report markdown from batch_pilot summary JSON (S7-03)."""

from __future__ import annotations

import argparse
import sys
from datetime import UTC, datetime
from pathlib import Path

from aeo_shared.pilot_metrics import load_pilot_summary, render_pilot_report_markdown

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT.parent / "docs" / "reports" / "ms7-pilot-report.md"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate MS7 pilot report from batch summary.")
    parser.add_argument("--summary", type=Path, required=True, help="batch_*.summary.json path")
    parser.add_argument("--csv", type=Path, required=True, help="batch_*.csv path")
    parser.add_argument(
        "--testset",
        type=Path,
        default=ROOT / "pilot" / "yuanzheng-sku-testset.json",
        help="Pilot SKU test set JSON",
    )
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT, help="Report output path")
    parser.add_argument(
        "--title",
        default="MS7 元征 SKU 试点报告",
        help="Report title",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    summary_path = args.summary if args.summary.is_absolute() else ROOT / args.summary
    csv_path = args.csv if args.csv.is_absolute() else ROOT / args.csv
    testset_path = args.testset if args.testset.is_absolute() else ROOT / args.testset
    output_path = args.output if args.output.is_absolute() else ROOT / args.output

    repo_root = ROOT.parent
    try:
        testset_display = str(testset_path.relative_to(repo_root))
    except ValueError:
        testset_display = str(testset_path)
    try:
        csv_display = str(csv_path.relative_to(repo_root))
    except ValueError:
        csv_display = str(csv_path)

    summary = load_pilot_summary(summary_path)
    report = render_pilot_report_markdown(
        summary,
        title=args.title,
        testset_path=testset_display,
        batch_csv_path=csv_display,
        generated_at=datetime.now(UTC).strftime("%Y-%m-%d %H:%M UTC"),
        video_script_path="../pilot/demo-video-script.md",
        notes="本报告由 `generate_pilot_report.py` 根据 `batch_pilot` 输出自动生成。",
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(report, encoding="utf-8")
    print(f"Report written: {output_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
