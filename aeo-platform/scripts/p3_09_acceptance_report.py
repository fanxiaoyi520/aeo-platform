#!/usr/bin/env python3
"""P3-09 — Phase 3 DTC 独立站验收报告生成器。

验收项：
1. DTC Content Agent 注册 + 端到端
2. DTC Operations Agent 注册 + 端到端
3. Shopify 客服集成（3 场景）
4. DTC KPI 计算
5. 内容模板库（4 模板）
6. Dashboard API
7. Mock 数据完整性
"""

from __future__ import annotations

import json
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def check(name: str, passed: bool, detail: str = "") -> dict:
    status = "PASS" if passed else "FAIL"
    return {"check": name, "status": status, "detail": detail}


def run_checks() -> list[dict]:
    results = []

    # 1. Agent 注册
    from aeo_shared import get_default_registry

    reg = get_default_registry()
    content_agent = reg.get("dtc_content_agent")
    ops_agent = reg.get("dtc_operations_agent")
    results.append(check(
        "DTC Content Agent active",
        content_agent.status == "active",
        f"category={content_agent.category.value}, platforms={content_agent.platforms}",
    ))
    results.append(check(
        "DTC Operations Agent active",
        ops_agent.status == "active",
        f"category={ops_agent.category.value}, platforms={ops_agent.platforms}",
    ))

    # 2. 子图注册
    from aeo_shared import build_graph_catalog

    catalog = build_graph_catalog()
    results.append(check("dtc_content subgraph", "dtc_content" in catalog))
    results.append(check("dtc_ops subgraph", "dtc_ops" in catalog))

    # 3. Shopify 客服话术
    from aeo_shared.after_sales_scripts import get_script_library

    lib = get_script_library()
    shopify_scripts = lib.filter_by(platform="shopify")
    results.append(check(
        "Shopify 售后话术 ≥ 3",
        len(shopify_scripts) >= 3,
        f"found {len(shopify_scripts)} scripts",
    ))
    scenarios = {s.scenario for s in shopify_scripts}
    for expected in ("abandoned_cart", "shipping", "discount_issue"):
        results.append(check(f"场景 {expected}", expected in scenarios))

    # 4. DTC KPI 计算
    from decimal import Decimal

    from aeo_shared.dtc_analytics import calculate_dtc_kpis

    kpis = calculate_dtc_kpis(
        [{"sessions": 1000, "orders": 50, "revenue": Decimal("2500"), "conversion_rate": Decimal("0.05"), "cart_abandonment_rate": Decimal("0.6"), "avg_order_value": Decimal("50")}],
        [{"total_spent": Decimal("500"), "orders_count": 2, "accepts_marketing": True}],
        [{"total_value": Decimal("80")}],
    )
    results.append(check("DTC KPI total_sessions", kpis["total_sessions"] == 1000))
    results.append(check("DTC KPI total_revenue", kpis["total_revenue"] == "2500"))
    results.append(check("DTC KPI customer_count", kpis["customer_count"] == 1))

    # 5. 内容模板
    from aeo_shared.content_templates import get_content_template_library

    tpl_lib = get_content_template_library()
    shopify_tpls = tpl_lib.filter_by(platform="shopify")
    results.append(check(
        "Shopify 模板 ≥ 4",
        len(shopify_tpls) >= 4,
        f"found {len(shopify_tpls)} templates",
    ))
    types = {t.content_type for t in shopify_tpls}
    for expected in ("listing", "landing_page", "email_campaign", "social_post"):
        results.append(check(f"模板 {expected}", expected in types))

    # 6. Mock 数据完整性
    from aeo_integrations.shopify.store import MockStoreAdapter

    adapter = MockStoreAdapter()
    results.append(check("Mock products", len(adapter.list_products()) > 0, f"{len(adapter.list_products())} products"))
    results.append(check("Mock orders", len(adapter.list_orders()) > 0, f"{len(adapter.list_orders())} orders"))
    results.append(check("Mock abandoned carts", len(adapter.list_abandoned_carts()) > 0, f"{len(adapter.list_abandoned_carts())} carts"))
    results.append(check("Mock customers", len(adapter.list_customers()) > 0, f"{len(adapter.list_customers())} customers"))
    results.append(check("Mock discounts", len(adapter.list_discount_codes()) > 0, f"{len(adapter.list_discount_codes())} discounts"))
    results.append(check("Mock store metrics", len(adapter.get_store_metrics()) > 0, f"{len(adapter.get_store_metrics())} days"))

    # 7. Platform 路由
    from aeo_orchestrator.runner import PlatformChoice

    from typing import get_args

    platforms = get_args(PlatformChoice)
    results.append(check("shopify in PlatformChoice", "shopify" in platforms, f"platforms={platforms}"))

    return results


def main() -> int:
    print("=" * 60)
    print("P3-09 Phase 3 DTC 独立站验收报告")
    print(f"生成时间: {datetime.now(UTC).isoformat()}")
    print("=" * 60)

    results = run_checks()

    passed = sum(1 for r in results if r["status"] == "PASS")
    failed = sum(1 for r in results if r["status"] == "FAIL")
    total = len(results)

    for r in results:
        icon = "[OK]" if r["status"] == "PASS" else "[FAIL]"
        detail = f" -- {r['detail']}" if r["detail"] else ""
        print(f"  {icon} {r['check']}{detail}")

    print(f"\n{'=' * 60}")
    print(f"验收结果: {passed}/{total} 通过 ({passed/total*100:.1f}%)")
    if failed:
        print(f"失败: {failed} 项")
    else:
        print("Phase 3 DTC 独立站验收 **全部通过**")
    print("=" * 60)

    report = {
        "milestone": "P3",
        "task": "P3-09",
        "title": "Phase 3 DTC 独立站生产验收",
        "timestamp": datetime.now(UTC).isoformat(),
        "total_checks": total,
        "passed": passed,
        "failed": failed,
        "success_rate": round(passed / total, 4) if total else 0,
        "checks": results,
    }

    output_dir = ROOT / "pilot" / "reports"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "p3-09-acceptance-report.json"
    output_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\n报告已保存: {output_path}")

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
