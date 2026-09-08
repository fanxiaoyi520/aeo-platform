"""P3-08: DTC independent site dashboard API — Shopify store overview."""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from aeo_integrations.shopify.store import get_store_client
from aeo_shared.dtc_analytics import calculate_dtc_kpis
from aeo_shared.responses import success_response
from fastapi import APIRouter, Request

router = APIRouter(prefix="/api/v1/dtc", tags=["dtc"])


def _ok(request: Request, data: dict[str, Any]) -> dict[str, Any]:
    return dict(success_response(data, request.state.request_id).model_dump())


def _build_dashboard() -> dict[str, Any]:
    client = get_store_client()

    products = client.list_products()
    orders = client.list_orders()
    inventory = client.list_inventory()
    carts = client.list_abandoned_carts()
    customers = client.list_customers()
    discounts = client.list_discount_codes()
    store_metrics_raw = client.get_store_metrics()

    metrics_dicts = [m.model_dump() for m in store_metrics_raw]
    customer_dicts = [c.model_dump() for c in customers]
    cart_dicts = [c.model_dump() for c in carts]

    kpis = calculate_dtc_kpis(metrics_dicts, customer_dicts, cart_dicts)

    active_products = sum(1 for p in products if p.status == "active")
    paid_orders = sum(1 for o in orders if o.financial_status == "paid")
    low_stock = sum(1 for i in inventory if i.available < 10)
    active_discounts = sum(1 for d in discounts if d.is_active)

    return {
        "storefront": {
            "total_products": len(products),
            "active_products": active_products,
            "total_orders": len(orders),
            "paid_orders": paid_orders,
            "low_stock_items": low_stock,
            "active_discounts": active_discounts,
        },
        "kpis": kpis,
        "recent_orders": [o.model_dump() for o in orders[:5]],
        "top_products": [p.model_dump() for p in products[:5]],
        "abandoned_carts_summary": {
            "total": len(carts),
            "recovery_email_sent": sum(1 for c in carts if c.recovery_email_sent),
            "total_value": str(
                sum(
                    (c.total_value for c in carts if c.total_value is not None),
                    Decimal("0"),
                )
            ),
        },
    }


@router.get("/dashboard")
async def get_dtc_dashboard(request: Request) -> dict[str, Any]:
    """Return DTC Shopify store overview dashboard."""
    dashboard = _build_dashboard()
    return _ok(request, dashboard)
