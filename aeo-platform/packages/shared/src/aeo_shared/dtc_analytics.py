"""P3-06: DTC analytics helpers — Shopify-specific KPI calculations."""

from __future__ import annotations

from decimal import Decimal
from typing import Any


def calculate_dtc_kpis(
    store_metrics: list[dict[str, Any]],
    customers: list[dict[str, Any]],
    abandoned_carts: list[dict[str, Any]],
) -> dict[str, Any]:
    if not store_metrics:
        return {
            "avg_conversion_rate": None,
            "avg_cart_abandonment_rate": None,
            "avg_order_value": None,
            "total_revenue": "0",
            "total_sessions": 0,
            "total_orders": 0,
            "customer_lifetime_value": None,
            "repeat_purchase_rate": None,
            "email_marketing_opt_in_rate": None,
        }

    conversion_rates = [
        float(m["conversion_rate"]) for m in store_metrics if m.get("conversion_rate") is not None
    ]
    abandonment_rates = [
        float(m["cart_abandonment_rate"])
        for m in store_metrics
        if m.get("cart_abandonment_rate") is not None
    ]
    aovs = [
        float(m["avg_order_value"]) for m in store_metrics if m.get("avg_order_value") is not None
    ]

    total_revenue = sum(
        (Decimal(str(m["revenue"])) for m in store_metrics if m.get("revenue") is not None),
        Decimal("0"),
    )
    total_sessions = sum(int(m.get("sessions", 0)) for m in store_metrics)
    total_orders = sum(int(m.get("orders", 0)) for m in store_metrics)

    total_spent = sum(
        (Decimal(str(c["total_spent"])) for c in customers if c.get("total_spent") is not None),
        Decimal("0"),
    )
    clv = (total_spent / len(customers)).quantize(Decimal("0.01")) if customers else None

    multi_order_customers = sum(1 for c in customers if int(c.get("orders_count", 0)) > 1)
    repeat_rate = (
        Decimal(str(multi_order_customers / len(customers))).quantize(Decimal("0.0001"))
        if customers
        else None
    )

    marketing_opt_in = sum(1 for c in customers if c.get("accepts_marketing", False))
    opt_in_rate = (
        Decimal(str(marketing_opt_in / len(customers))).quantize(Decimal("0.0001"))
        if customers
        else None
    )

    return {
        "avg_conversion_rate": (
            round(sum(conversion_rates) / len(conversion_rates), 4) if conversion_rates else None
        ),
        "avg_cart_abandonment_rate": (
            round(sum(abandonment_rates) / len(abandonment_rates), 4) if abandonment_rates else None
        ),
        "avg_order_value": round(sum(aovs) / len(aovs), 2) if aovs else None,
        "total_revenue": str(total_revenue),
        "total_sessions": total_sessions,
        "total_orders": total_orders,
        "customer_lifetime_value": str(clv) if clv else None,
        "repeat_purchase_rate": str(repeat_rate) if repeat_rate else None,
        "email_marketing_opt_in_rate": str(opt_in_rate) if opt_in_rate else None,
        "metric_days": len(store_metrics),
        "customer_count": len(customers),
        "abandoned_cart_count": len(abandoned_carts),
    }


def build_dtc_metrics_prompt_section(dtc_kpis: dict[str, Any]) -> str:
    return (
        f"\nDTC Shopify KPIs ({dtc_kpis.get('metric_days', 0)} days):\n"
        f"- Avg Conversion Rate: {dtc_kpis.get('avg_conversion_rate', 'N/A')}\n"
        f"- Avg Cart Abandonment Rate: {dtc_kpis.get('avg_cart_abandonment_rate', 'N/A')}\n"
        f"- Avg Order Value: ${dtc_kpis.get('avg_order_value', 'N/A')}\n"
        f"- Total Revenue: ${dtc_kpis.get('total_revenue', '0')}\n"
        f"- Customer Lifetime Value: ${dtc_kpis.get('customer_lifetime_value', 'N/A')}\n"
        f"- Repeat Purchase Rate: {dtc_kpis.get('repeat_purchase_rate', 'N/A')}\n"
        f"- Email Opt-in Rate: {dtc_kpis.get('email_marketing_opt_in_rate', 'N/A')}\n"
        f"- Abandoned Carts: {dtc_kpis.get('abandoned_cart_count', 0)}\n"
    )
