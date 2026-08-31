"""Product catalog import — patterns from CatalogMetrix-Mini, importline, ecommerce-rag.

- CSV column auto-mapping (CatalogMetrix-Mini)
- Row-level validation + completeness scoring (importline / CatalogMetrix)
- One SKU → one Markdown file under knowledge/products/ (Branch8: chunk per variant)
- Optional pilot testset knowledge_doc sync (AEO Platform)
"""

from __future__ import annotations

import csv
import json
import re
from collections.abc import Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

# CatalogMetrix-style column aliases (case-insensitive header match)
COLUMN_ALIASES: dict[str, list[str]] = {
    "sku": ["sku", "product_code", "variant_sku", "seller_sku", "item_sku"],
    "product_name": ["product_name", "title", "name", "item_name", "product name"],
    "brand": ["brand", "manufacturer"],
    "platform": ["platform", "channel"],
    "market": ["market", "marketplace", "region"],
    "category": ["category", "product_type", "product category"],
    "product_line": ["product_line", "line", "collection"],
    "overview": ["overview", "description", "product_description", "intro"],
    "keywords": ["keywords", "keyword", "search_terms", "tags"],
    "bullets": ["bullets", "bullet_points", "selling_points"],
    "competitor_asins": ["competitor_asins", "competitor_asin", "asins", "competitor asins"],
    "compliance_notes": ["compliance_notes", "compliance", "legal_notes"],
}

REQUIRED_FIELDS = ("sku", "product_name")


@dataclass
class ProductRecord:
    sku: str
    product_name: str
    brand: str = ""
    platform: str = "amazon"
    market: str = "US"
    category: str = ""
    product_line: str = ""
    overview: str = ""
    specs: list[str] = field(default_factory=list)
    keywords: list[str] = field(default_factory=list)
    bullets: list[str] = field(default_factory=list)
    competitor_asins: list[str] = field(default_factory=list)
    compliance_notes: str = ""

    def slug(self) -> str:
        base = self.sku.lower().strip()
        base = re.sub(r"[^\w\-]+", "-", base)
        return re.sub(r"-+", "-", base).strip("-") or "product"

    def knowledge_doc_path(self) -> str:
        return f"knowledge/products/{self.slug()}.md"

    def completeness_score(self) -> tuple[int, list[str]]:
        """0–100 score and missing field hints (CatalogMetrix completeness idea)."""
        checks: list[tuple[str, bool]] = [
            ("sku", bool(self.sku.strip())),
            ("product_name", bool(self.product_name.strip())),
            ("brand", bool(self.brand.strip())),
            ("category", bool(self.category.strip())),
            ("overview", bool(self.overview.strip())),
            ("specs", len(self.specs) >= 2),
            ("keywords", len(self.keywords) >= 3),
            ("bullets", len(self.bullets) >= 3),
            ("competitor_asins", len(self.competitor_asins) >= 1),
        ]
        missing = [name for name, ok in checks if not ok]
        score = int(100 * sum(1 for _, ok in checks if ok) / len(checks))
        return score, missing


@dataclass
class ImportRowResult:
    row_number: int
    sku: str
    status: str  # created | updated | skipped | error
    message: str
    source_file: str = ""
    completeness: int = 0


@dataclass
class CsvHeaderMapping:
    canonical: dict[str, str] = field(default_factory=dict)
    spec_cols: list[str] = field(default_factory=list)
    bullet_cols: list[str] = field(default_factory=list)
    keyword_cols: list[str] = field(default_factory=list)


def _normalize_header(header: str) -> str:
    return header.strip().lower().replace("_", " ")


def map_csv_headers(fieldnames: Sequence[str] | None) -> CsvHeaderMapping:
    """Map raw CSV headers to canonical field names."""
    mapping = CsvHeaderMapping()
    if not fieldnames:
        return mapping
    normalized = {_normalize_header(h): h for h in fieldnames if h}
    for canonical, aliases in COLUMN_ALIASES.items():
        for alias in aliases:
            key = _normalize_header(alias)
            if key in normalized:
                mapping.canonical[canonical] = normalized[key]
                break
    for raw in fieldnames:
        if not raw:
            continue
        low = raw.strip().lower()
        if re.match(r"bullet[_\s]?\d+", low):
            mapping.bullet_cols.append(raw)
        elif re.match(r"(param|spec)[_\s]?\d+", low):
            mapping.spec_cols.append(raw)
        elif re.match(r"keyword[_\s]?\d+", low):
            mapping.keyword_cols.append(raw)
    mapping.spec_cols.sort()
    mapping.bullet_cols.sort()
    mapping.keyword_cols.sort()
    return mapping


def _split_list(value: str) -> list[str]:
    if not value or not value.strip():
        return []
    parts = re.split(r"[,|;]", value)
    return [p.strip() for p in parts if p.strip()]


def row_to_product(row: dict[str, str], header_map: CsvHeaderMapping) -> ProductRecord:
    def cell(canonical: str) -> str:
        raw_key = header_map.canonical.get(canonical)
        if not raw_key:
            return ""
        return (row.get(raw_key) or "").strip()

    specs = [(row.get(col) or "").strip() for col in header_map.spec_cols]
    specs = [s for s in specs if s]
    bullets = [(row.get(col) or "").strip() for col in header_map.bullet_cols]
    bullets = [b for b in bullets if b]
    keywords = [(row.get(col) or "").strip() for col in header_map.keyword_cols]
    keywords = [k for k in keywords if k]
    if not keywords:
        keywords = _split_list(cell("keywords"))

    if not bullets:
        bullets = _split_list(cell("bullets"))

    return ProductRecord(
        sku=cell("sku"),
        product_name=cell("product_name"),
        brand=cell("brand"),
        platform=cell("platform") or "amazon",
        market=cell("market") or "US",
        category=cell("category"),
        product_line=cell("product_line"),
        overview=cell("overview"),
        specs=specs,
        keywords=keywords,
        bullets=bullets,
        competitor_asins=_split_list(cell("competitor_asins")),
        compliance_notes=cell("compliance_notes"),
    )


def render_product_markdown(product: ProductRecord) -> str:
    """Render product knowledge doc for per-variant RAG chunk source."""
    lines = [
        f"# {product.product_name}（产品资料）",
        "",
        "| 字段 | 值 |",
        "|------|-----|",
        f"| SKU | {product.sku} |",
    ]
    if product.brand:
        lines.append(f"| 品牌 | {product.brand} |")
    lines.extend(
        [
            f"| 平台 | {product.platform} |",
            f"| 市场 | {product.market} |",
        ]
    )
    if product.category:
        lines.append(f"| 类目 | {product.category} |")
    if product.product_line:
        lines.append(f"| 产品线 | {product.product_line} |")
    lines.append("")

    if product.overview:
        lines.extend(["## 产品概述", "", product.overview, ""])

    if product.specs:
        lines.append("## 核心参数")
        lines.append("")
        for spec in product.specs:
            lines.append(f"- {spec}")
        lines.append("")

    if product.keywords:
        lines.extend(["## 目标市场关键词", ""])
        for kw in product.keywords:
            lines.append(f"- {kw}")
        lines.append("")

    if product.bullets:
        lines.extend(["## 卖点方向", ""])
        for i, bullet in enumerate(product.bullets, 1):
            lines.append(f"{i}. {bullet}")
        lines.append("")

    if product.competitor_asins:
        lines.extend(["## 竞品 ASIN（调研参考）", ""])
        for asin in product.competitor_asins:
            lines.append(f"- {asin}")
        lines.append("")

    if product.compliance_notes:
        lines.extend(["## 合规注意", "", product.compliance_notes, ""])

    return "\n".join(lines).rstrip() + "\n"


def import_csv_to_products(
    csv_path: Path,
    products_dir: Path,
    *,
    dry_run: bool = False,
    min_completeness: int = 0,
) -> list[ImportRowResult]:
    """Import CSV rows to knowledge/products/*.md (importline-style row reports)."""
    results: list[ImportRowResult] = []
    products_dir.mkdir(parents=True, exist_ok=True)

    with csv_path.open(encoding="utf-8-sig", newline="") as fh:
        reader = csv.DictReader(fh)
        header_map = map_csv_headers(reader.fieldnames)

        for row_num, row in enumerate(reader, start=2):
            if not any((v or "").strip() for v in row.values()):
                continue
            try:
                product = row_to_product(row, header_map)
            except Exception as exc:  # noqa: BLE001
                results.append(ImportRowResult(row_num, "", "error", f"parse failed: {exc}"))
                continue

            if not product.sku:
                results.append(ImportRowResult(row_num, "", "error", "missing required field: sku"))
                continue
            if not product.product_name:
                results.append(
                    ImportRowResult(
                        row_num, product.sku, "error", "missing required field: product_name"
                    )
                )
                continue

            score, missing = product.completeness_score()
            if score < min_completeness:
                results.append(
                    ImportRowResult(
                        row_num,
                        product.sku,
                        "skipped",
                        (
                            f"completeness {score}% < {min_completeness}% "
                            f"(missing: {', '.join(missing)})"
                        ),
                        completeness=score,
                    )
                )
                continue

            target = products_dir / f"{product.slug()}.md"
            rel_path = f"knowledge/products/{target.name}"
            content = render_product_markdown(product)
            status = "created"
            if target.exists():
                status = "updated"

            if not dry_run:
                target.write_text(content, encoding="utf-8")

            results.append(
                ImportRowResult(
                    row_num,
                    product.sku,
                    status,
                    f"completeness {score}%",
                    source_file=rel_path,
                    completeness=score,
                )
            )

    return results


def sync_testset_knowledge_docs(
    testset_path: Path,
    sku_to_doc: dict[str, str],
    *,
    dry_run: bool = False,
) -> int:
    """Link pilot testset items to knowledge_doc by SKU (ecommerce-rag SKU as key)."""
    data: dict[str, Any] = json.loads(testset_path.read_text(encoding="utf-8"))
    updated = 0
    items = data.get("items", [])
    for item in items:
        sku = str(item.get("sku", "")).strip()
        if sku in sku_to_doc:
            new_doc = sku_to_doc[sku]
            if item.get("knowledge_doc") != new_doc:
                if not dry_run:
                    item["knowledge_doc"] = new_doc
                updated += 1
    if updated and not dry_run:
        testset_path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    return updated


def product_chunk_header(source_file: str, content: str) -> str:
    """Prepend SKU/title context to product chunks (Branch8 per-variant context)."""
    sku_match = re.search(r"^\|\s*SKU\s*\|\s*([^|]+)\|", content, re.MULTILINE)
    title_match = re.match(r"^#\s+(.+?)（", content)
    parts: list[str] = []
    if sku_match:
        parts.append(f"SKU: {sku_match.group(1).strip()}")
    if title_match:
        parts.append(f"Product: {title_match.group(1).strip()}")
    if not parts:
        parts.append(f"Source: {source_file}")
    return " | ".join(parts)
