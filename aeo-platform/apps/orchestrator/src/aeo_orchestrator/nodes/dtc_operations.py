"""dtc_operations_agent — P3-04 Shopify store health monitoring + ops recommendations."""

from __future__ import annotations

import json
from typing import Any

from aeo_integrations.shopify.store import get_store_client
from aeo_llm.openai_compatible import get_llm_provider
from aeo_llm.provider import Message

from aeo_orchestrator.nodes._helpers import with_started_trace
from aeo_orchestrator.state import AgentTraceStatus, TaskState, make_trace_event


def calculate_dtc_health(
    metrics: list[dict[str, Any]],
    abandoned_carts: list[dict[str, Any]],
    customers: list[dict[str, Any]],
    discounts: list[dict[str, Any]],
) -> dict[str, Any]:
    total_sessions = sum(int(m.get("sessions", 0)) for m in metrics)
    total_orders = sum(int(m.get("orders", 0)) for m in metrics)
    total_revenue = sum(float(m["revenue"]) for m in metrics if m.get("revenue") is not None)

    avg_conversion = (
        sum(float(m["conversion_rate"]) for m in metrics if m.get("conversion_rate") is not None)
        / len(metrics)
        if metrics
        else 0.0
    )
    avg_abandonment = (
        sum(
            float(m["cart_abandonment_rate"])
            for m in metrics
            if m.get("cart_abandonment_rate") is not None
        )
        / len(metrics)
        if metrics
        else 0.0
    )
    avg_order_value = (
        sum(float(m["avg_order_value"]) for m in metrics if m.get("avg_order_value") is not None)
        / len(metrics)
        if metrics
        else 0.0
    )

    total_cart_value = sum(
        float(c["total_value"]) for c in abandoned_carts if c.get("total_value") is not None
    )
    unrecovered_carts = [c for c in abandoned_carts if not c.get("recovery_email_sent", False)]

    total_customers = len(customers)
    marketing_opt_in = sum(1 for c in customers if c.get("accepts_marketing", False))
    total_customer_spend = sum(
        float(c["total_spent"]) for c in customers if c.get("total_spent") is not None
    )

    active_discounts = [d for d in discounts if d.get("is_active", False)]
    total_discount_usage = sum(int(d.get("times_used", 0)) for d in discounts)

    return {
        "avg_conversion_rate": round(avg_conversion, 4),
        "avg_cart_abandonment_rate": round(avg_abandonment, 4),
        "avg_order_value": round(avg_order_value, 2),
        "total_sessions": total_sessions,
        "total_orders": total_orders,
        "total_revenue": round(total_revenue, 2),
        "abandoned_cart_value": round(total_cart_value, 2),
        "unrecovered_cart_count": len(unrecovered_carts),
        "total_customers": total_customers,
        "marketing_opt_in_rate": (
            round(marketing_opt_in / total_customers, 4) if total_customers else 0.0
        ),
        "avg_customer_lifetime_value": (
            round(total_customer_spend / total_customers, 2) if total_customers else 0.0
        ),
        "active_discount_count": len(active_discounts),
        "total_discount_redemptions": total_discount_usage,
        "metric_days": len(metrics),
    }


def _build_prompt(
    state: TaskState,
    health: dict[str, Any],
) -> str:
    sku = state.get("sku", "")
    product_info = state.get("product_info") or {}

    return (
        f"You are a Shopify DTC operations specialist.\n"
        f"Primary SKU: {sku}\n"
        f"Product: {product_info.get('title', 'N/A')}\n"
        f"Price: {product_info.get('price', 'N/A')}\n\n"
        f"Store health metrics ({health['metric_days']} days):\n"
        f"{json.dumps(health, indent=2)}\n\n"
        "Provide DTC operations recommendations in JSON format:\n"
        '{"inventory_alerts": [{"sku": "...", "level": "critical|warning|info", '
        '"message": "..."}], '
        '"pricing_suggestions": [{"sku": "...", "current_price": ..., '
        '"suggested_price": ..., "reason": "..."}], '
        '"restock_recommendations": [{"sku": "...", "recommended_quantity": ..., '
        '"urgency": "high|medium|low"}], '
        '"abandoned_cart_strategy": {"recommendation": "...", "expected_recovery": ...}, '
        '"report": "concise operations summary (3-5 sentences)"}'
    )


def _parse_llm_json(content: str) -> dict[str, Any]:
    text = content.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        text = "\n".join(lines[1:-1]) if lines[-1].strip() == "```" else "\n".join(lines[1:])
    try:
        return json.loads(text)  # type: ignore[no-any-return]
    except json.JSONDecodeError:
        return {
            "inventory_alerts": [],
            "pricing_suggestions": [],
            "restock_recommendations": [],
            "abandoned_cart_strategy": {},
            "report": text,
        }


async def dtc_operations_node(state: TaskState) -> dict[str, object]:
    """dtc_operations_agent — Shopify store health + ops recommendations."""
    trace = [with_started_trace(state, "dtc_operations_agent")]

    try:
        store = get_store_client()
        metrics = [m.model_dump() for m in store.get_store_metrics(limit=7)]
        carts = [c.model_dump() for c in store.list_abandoned_carts()]
        customers = [c.model_dump() for c in store.list_customers()]
        discounts = [d.model_dump() for d in store.list_discount_codes()]

        health = calculate_dtc_health(metrics, carts, customers, discounts)

        prompt = _build_prompt(state, health)
        provider = get_llm_provider()
        response = await provider.chat(
            [
                Message(
                    role="system",
                    content=(
                        "You are a Shopify DTC operations specialist. "
                        "Analyze store health metrics and provide actionable "
                        "recommendations for inventory, pricing, restocking, and "
                        "abandoned cart recovery. Output valid JSON only."
                    ),
                ),
                Message(role="user", content=prompt),
            ],
            temperature=0.3,
        )

        parsed = _parse_llm_json(response.content)

        result = {
            "health_metrics": health,
            "inventory_alerts": parsed.get("inventory_alerts", []),
            "pricing_suggestions": parsed.get("pricing_suggestions", []),
            "restock_recommendations": parsed.get("restock_recommendations", []),
            "abandoned_cart_strategy": parsed.get("abandoned_cart_strategy", {}),
            "report": parsed.get("report", ""),
        }

        trace.append(
            make_trace_event(
                "dtc_operations_agent",
                AgentTraceStatus.COMPLETED,
                detail={
                    "metric_days": health["metric_days"],
                    "total_orders": health["total_orders"],
                    "unrecovered_carts": health["unrecovered_cart_count"],
                    "alert_count": len(result["inventory_alerts"]),
                },
            )
        )

    except Exception as exc:
        result = {
            "health_metrics": {},
            "inventory_alerts": [],
            "pricing_suggestions": [],
            "restock_recommendations": [],
            "abandoned_cart_strategy": {},
            "report": f"DTC operations analysis failed: {exc}",
            "error": str(exc),
        }
        trace.append(
            make_trace_event(
                "dtc_operations_agent",
                AgentTraceStatus.FAILED,
                detail={"error": str(exc)},
            )
        )

    return {"dtc_ops": result, "trace": trace}
