"""MV4-01: Orders API — list orders with filtering and pagination."""

from __future__ import annotations

from typing import Any

from aeo_shared.errors import ErrorCode
from aeo_shared.order_ingest import OrderIngestService, UnifiedOrderRecord
from aeo_shared.responses import error_response, success_response
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api/v1/orders", tags=["orders"])

_ingest_service = OrderIngestService()


class OrderItemResponse(BaseModel):
    order_id: str
    sku: str
    platform: str
    marketplace: str = "US"
    quantity: int = 1
    item_price: str = ""
    currency: str = "USD"
    order_status: str = "Unshipped"
    purchase_date: str = ""
    tracking_number: str = ""
    carrier: str = ""
    ship_date: str = ""
    delivery_date: str = ""
    return_status: str = "none"


class OrdersListResponse(BaseModel):
    orders: list[dict[str, Any]] = Field(default_factory=list)
    total: int = 0
    page: int = 1
    page_size: int = 20


def _ok(request: Request, data: dict[str, Any]) -> dict[str, Any]:
    return success_response(data, request.state.request_id).model_dump()


def _error(request: Request, code: ErrorCode, status: int, detail: str = "") -> JSONResponse:
    body = error_response(code, request.state.request_id, detail).model_dump()
    return JSONResponse(status_code=status, content=body)


def _fetch_orders() -> list[UnifiedOrderRecord]:
    from aeo_integrations.amazon.orders import get_orders_client
    from aeo_integrations.shopify.store import get_store_client

    records: list[UnifiedOrderRecord] = []

    try:
        amazon_client = get_orders_client()
        records.extend(_ingest_service.ingest_amazon(amazon_client))
    except Exception:
        pass

    try:
        shopify_client = get_store_client()
        records.extend(_ingest_service.ingest_shopify(shopify_client))
    except Exception:
        pass

    return records


@router.get("", response_model=None)
async def list_orders(
    request: Request,
    sku: str | None = None,
    platform: str | None = None,
    page: int = 1,
    page_size: int = 20,
) -> dict[str, Any] | JSONResponse:
    try:
        all_orders = _fetch_orders()

        if sku:
            key = sku.strip().upper()
            all_orders = [o for o in all_orders if o.sku.upper() == key]

        if platform:
            key = platform.strip().lower()
            all_orders = [o for o in all_orders if o.platform.lower() == key]

        total = len(all_orders)
        start = (page - 1) * page_size
        end = start + page_size
        page_orders = all_orders[start:end]

        orders_data = [
            OrderItemResponse(
                order_id=o.external_order_id,
                sku=o.sku,
                platform=o.platform,
                marketplace=o.marketplace,
                quantity=o.quantity,
                item_price=o.item_price,
                currency=o.currency,
                order_status=o.order_status,
                purchase_date=o.purchase_date,
                tracking_number=o.tracking_number,
                carrier=o.carrier,
                ship_date=o.ship_date,
                delivery_date=o.delivery_date,
                return_status=o.return_status,
            ).model_dump()
            for o in page_orders
        ]

        return _ok(
            request,
            OrdersListResponse(
                orders=orders_data,
                total=total,
                page=page,
                page_size=page_size,
            ).model_dump(),
        )
    except Exception as exc:
        return _error(request, ErrorCode.INTERNAL_ERROR, 500, str(exc))
