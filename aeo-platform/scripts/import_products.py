#!/usr/bin/env python3
"""Import product catalog CSV → knowledge/products/*.md (P1-02).

Patterns integrated from open-source projects:
- CatalogMetrix-Mini: column auto-mapping, completeness scoring
- importline: row-level validation, idempotent upsert by SKU
- ecommerce-rag / Branch8: SKU-keyed docs for per-variant RAG chunks

Usage:
  uv run python scripts/import_products.py knowledge/templates/pilot-sku-batch.csv
  uv run python scripts/import_products.py path/to.csv --sync-testset --ingest
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

# scripts/ is not a package; add packages/rag to path when run directly
_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "packages" / "rag" / "src"))

from aeo_rag.product_catalog import (  # noqa: E402
    import_csv_to_products,
    sync_testset_knowledge_docs,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Import product CSV to knowledge/products/")
    parser.add_argument("csv", type=Path, help="CSV file path")
    parser.add_argument(
        "--products-dir",
        type=Path,
        default=_ROOT / "knowledge" / "products",
        help="Output directory for Markdown files",
    )
    parser.add_argument(
        "--testset",
        type=Path,
        default=_ROOT / "pilot" / "sample-sku-testset.json",
        help="Pilot testset JSON to update knowledge_doc links",
    )
    parser.add_argument(
        "--sync-testset",
        action="store_true",
        help="Link SKUs in testset to new docs",
    )
    parser.add_argument("--ingest", action="store_true", help="Run ingest.ps1 after import")
    parser.add_argument("--dry-run", action="store_true", help="Validate only, do not write files")
    parser.add_argument(
        "--min-completeness",
        type=int,
        default=0,
        help="Skip rows below this completeness score (0-100)",
    )
    args = parser.parse_args()

    if not args.csv.is_file():
        print(f"error: CSV not found: {args.csv}", file=sys.stderr)
        return 1

    results = import_csv_to_products(
        args.csv,
        args.products_dir,
        dry_run=args.dry_run,
        min_completeness=args.min_completeness,
    )

    created = updated = skipped = errors = 0
    sku_to_doc: dict[str, str] = {}
    for row in results:
        if row.status == "created":
            created += 1
        elif row.status == "updated":
            updated += 1
        elif row.status == "skipped":
            skipped += 1
        else:
            errors += 1
        prefix = {"created": "+", "updated": "~", "skipped": "-", "error": "!"}.get(row.status, "?")
        print(f"{prefix} row {row.row_number} [{row.sku or '-'}] {row.status}: {row.message}")
        if row.source_file and row.sku:
            sku_to_doc[row.sku] = row.source_file

    print(f"\nSummary: created={created} updated={updated} skipped={skipped} errors={errors}")

    if errors:
        return 1

    if args.sync_testset and sku_to_doc:
        n = sync_testset_knowledge_docs(args.testset, sku_to_doc, dry_run=args.dry_run)
        print(f"testset knowledge_doc links updated: {n}")

    if args.ingest and not args.dry_run:
        ingest_ps1 = _ROOT / "scripts" / "ingest.ps1"
        if ingest_ps1.is_file():
            print("\nRunning ingest.ps1 ...")
            subprocess.run(
                [
                    "powershell",
                    "-NoProfile",
                    "-ExecutionPolicy",
                    "Bypass",
                    "-File",
                    str(ingest_ps1),
                ],
                cwd=_ROOT,
                check=True,
            )
        else:
            print("warn: ingest.ps1 not found, skip reindex", file=sys.stderr)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
