"""MS2 RAG 20-question spot check (M02 §5).

Runs retrieval against ingested knowledge and scores relevance heuristically.
For formal MS2 sign-off, review flagged rows manually.

Usage:
    uv run python scripts/rag_spotcheck.py
    uv run python scripts/rag_spotcheck.py --output docs/reports/ms2-rag-spotcheck-20q.md
"""

from __future__ import annotations

import argparse
import re
import statistics
import time
from dataclasses import dataclass
from pathlib import Path

# 20 questions derived from knowledge/amazon/listing-rules.md
QUESTIONS: list[tuple[str, str, list[str]]] = [
    ("Q01", "Amazon 标题最多多少个字符？", ["200", "字符"]),
    ("Q02", "Amazon 标题应包含哪些核心关键词结构？", ["品牌", "产品类型"]),
    ("Q03", "Amazon 标题禁止哪些促销用语？", ["free shipping", "best", "#1"]),
    ("Q04", "Amazon 标题是否允许全大写？", ["禁止", "全大写"]),
    ("Q05", "Amazon 五点描述每条最多多少字符？", ["500", "字符"]),
    ("Q06", "Amazon 五点描述一共几条？", ["5"]),
    ("Q07", "Amazon Bullet 是否允许 HTML 标签？", ["禁止", "HTML"]),
    ("Q08", "Amazon Bullet 句首是否大写？", ["大写"]),
    ("Q09", "Amazon Search Terms 最多多少 bytes？", ["250", "bytes"]),
    ("Q10", "Search Terms 与标题、Bullet 的关系？", ["不重复"]),
    ("Q11", "Search Terms 用什么分隔？", ["空格", "不用标点"]),
    ("Q12", "汽摩配诊断仪类目必须标明什么兼容性？", ["OBD2", "EOBD"]),
    ("Q13", "诊断仪应写清什么接口信息？", ["OBD-II", "16-pin", "接口"]),
    ("Q14", "诊断仪 Listing 应避免什么绝对化表述？", ["所有车型", "绝对"]),
    ("Q15", "标题是否禁止特殊符号堆砌？", ["禁止", "特殊符号"]),
    ("Q16", "五点描述应突出什么？", ["功能", "场景", "差异化"]),
    ("Q17", "Bullet 结尾是否使用标点？", ["不用", "标点"]),
    ("Q18", "Search Terms 单位是字符还是 bytes？", ["bytes"]),
    ("Q19", "电压信息是否应在 Listing 中写清？", ["电压"]),
    ("Q20", "Amazon Listing 标题规范属于哪个平台？", ["Amazon"]),
]


@dataclass
class SpotCheckRow:
    qid: str
    question: str
    hit: bool
    top_score: float
    top_source: str
    top_snippet: str
    latency_ms: float


def _project_root() -> Path:
    here = Path(__file__).resolve().parent.parent
    return here


def _relevant(content: str, keywords: list[str]) -> bool:
    lowered = content.lower()
    matched = sum(1 for kw in keywords if kw.lower() in lowered)
    return matched >= max(1, len(keywords) // 2 + (1 if len(keywords) > 2 else 0))


def run_spotcheck(*, use_hash: bool = True) -> tuple[list[SpotCheckRow], int]:
    import os

    root = _project_root()
    os.chdir(root)
    os.environ.setdefault("RAG_USE_HASH_EMBEDDINGS", "true" if use_hash else "false")
    os.environ.setdefault("RAG_SCORE_THRESHOLD", "0.0")

    from aeo_rag.config import get_rag_settings
    from aeo_rag.loaders import load_knowledge_dir
    from aeo_rag.store import KnowledgeStore

    get_rag_settings.cache_clear()
    settings = get_rag_settings()
    knowledge_dir = root / settings.knowledge_path
    store = KnowledgeStore(use_hash_embeddings=use_hash)
    store.reset()
    docs = load_knowledge_dir(knowledge_dir)
    indexed = store.ingest_documents(docs)
    if indexed == 0:
        raise RuntimeError(f"No chunks indexed from {knowledge_dir}")

    rows: list[SpotCheckRow] = []
    latencies: list[float] = []
    for qid, question, keywords in QUESTIONS:
        t0 = time.perf_counter()
        results = store.search(
            question,
            platform="amazon",
            score_threshold=-1.0,
            top_k=5,
        )
        latency_ms = (time.perf_counter() - t0) * 1000
        latencies.append(latency_ms)

        hit = False
        top_score = -999.0
        top_source = ""
        top_snippet = "(no results)"
        for result in results:
            if result.score > top_score:
                top_score = result.score
                top_source = result.source_file
                top_snippet = result.content[:120].replace("\n", " ")
            if _relevant(result.content, keywords):
                hit = True
        if top_score < -900:
            top_score = 0.0

        rows.append(
            SpotCheckRow(
                qid=qid,
                question=question,
                hit=hit,
                top_score=top_score,
                top_source=top_source,
                top_snippet=top_snippet,
                latency_ms=round(latency_ms, 2),
            )
        )

    p95 = statistics.quantiles(latencies, n=20)[18] if len(latencies) >= 2 else latencies[0]
    return rows, int(p95)


def _render_markdown(rows: list[SpotCheckRow], p95_ms: int) -> str:
    hits = sum(1 for r in rows if r.hit)
    rate = hits / len(rows) * 100
    lines = [
        "# MS2 RAG 20-Question Spot Check",
        "",
        f"- **Relevance (heuristic):** {hits}/{len(rows)} = {rate:.0f}% (target ≥ 80%)",
        f"- **Search p95 latency:** {p95_ms} ms (target < 500 ms)",
        "",
        "| ID | Question | Relevant | Score | Source | Latency (ms) | Snippet |",
        "|----|----------|----------|-------|--------|--------------|---------|",
    ]
    for r in rows:
        mark = "✅" if r.hit else "❌"
        q = re.sub(r"\|", "/", r.question)
        snip = re.sub(r"\|", "/", r.top_snippet)
        lines.append(
            f"| {r.qid} | {q} | {mark} | {r.top_score:.3f} | {r.top_source} | {r.latency_ms} | {snip} |"
        )
    lines.extend(
        [
            "",
            "## Manual review",
            "",
            "Heuristic keyword match may miss semantic hits. Mark any ❌ row as ✅ if snippet is clearly on-topic.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="MS2 RAG 20-question spot check")
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Write markdown report (default: print to stdout)",
    )
    args = parser.parse_args()

    rows, p95_ms = run_spotcheck()
    report = _render_markdown(rows, p95_ms)

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(report, encoding="utf-8")
        print(f"Wrote {args.output}")
    else:
        print(report)

    hits = sum(1 for r in rows if r.hit)
    rate = hits / len(rows)
    print(f"Relevance: {hits}/{len(rows)} = {rate:.0%}, p95={p95_ms}ms")
    if rate < 0.8:
        raise SystemExit(f"Relevance {rate:.0%} below 80% threshold (hash embeddings are approximate)")
    if p95_ms >= 500:
        raise SystemExit(f"p95 latency {p95_ms}ms exceeds 500ms threshold")


if __name__ == "__main__":
    main()
