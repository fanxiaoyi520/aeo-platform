"""operations_agent — MV3-04 inventory monitoring + pricing/restock suggestions."""

from __future__ import annotations

import json
from typing import Any

from aeo_integrations.amazon.inventory import get_inventory_client
from aeo_llm.openai_compatible import get_llm_provider
from aeo_llm.provider import Message

from aeo_orchestrator.nodes._helpers import with_started_trace
from aeo_orchestrator.state import AgentTraceStatus, TaskState, make_trace_event

LOW_STOCK_THRESHOLD = 25


def calculate_inventory_health(
    inventory: list[dict[str, Any]],
    low_stock_threshold: int = LOW_STOCK_THRESHOLD,
) -> dict[str, Any]:
    total_available = sum(int(i.get("available_quantity", 0)) for i in inventory)
    total_inbound = sum(int(i.get("inbound_quantity", 0)) for i in inventory)
    total_reserved = sum(int(i.get("reserved_quantity", 0)) for i in inventory)

    low_stock_items = [
        {
            "sku": i.get("sku", ""),
            "available_quantity": int(i.get("available_quantity", 0)),
            "inbound_quantity": int(i.get("inbound_quantity", 0)),
        }
        for i in inventory
        if int(i.get("available_quantity", 0)) < low_stock_threshold
    ]

    return {
        "total_available": total_available,
        "total_inbound": total_inbound,
        "total_reserved": total_reserved,
        "low_stock_count": len(low_stock_items),
        "low_stock_items": low_stock_items,
        "item_count": len(inventory),
    }


def _build_inventory_summary(
    inventory: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    return [
        {
            "sku": i.get("sku", ""),
            "fulfillment_channel": i.get("fulfillment_channel", ""),
            "available_quantity": int(i.get("available_quantity", 0)),
            "inbound_quantity": int(i.get("inbound_quantity", 0)),
            "reserved_quantity": int(i.get("reserved_quantity", 0)),
            "warehouse": i.get("warehouse", ""),
        }
        for i in inventory
    ]


def _build_user_prompt(
    state: TaskState,
    inventory_summary: list[dict[str, Any]],
    health: dict[str, Any],
) -> str:
    sku = state.get("sku", "")
    product_info = state.get("product_info") or {}

    return (
        f"You are an Amazon operations specialist.\n"
        f"Primary SKU: {sku}\n"
        f"Product: {product_info.get('title', 'N/A')}\n"
        f"Current price: {product_info.get('price', 'N/A')}\n\n"
        f"Inventory health:\n{json.dumps(health, indent=2)}\n\n"
        f"Inventory details:\n{json.dumps(inventory_summary, indent=2)}\n\n"
        "Provide operations recommendations in JSON format:\n"
        '{"inventory_alerts": [{"sku": "...", "level": "critical|warning|info", '
        '"message": "..."}], '
        '"pricing_suggestions": [{"sku": "...", "current_price": ..., '
        '"suggested_price": ..., "reason": "..."}], '
        '"restock_recommendations": [{"sku": "...", "recommended_quantity": ..., '
        '"urgency": "high|medium|low"}], '
        '"report": "concise narrative summary (3-5 sentences)"}'
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
            "report": text,
        }


async def operations_node(state: TaskState) -> dict[str, object]:
    """operations_agent — monitor inventory + generate pricing/restock suggestions."""
    trace = [with_started_trace(state, "operations_agent")]

    try:
        inv_client = get_inventory_client()
        inventory_items = inv_client.list_inventory()

        inventory_dicts = [item.model_dump() for item in inventory_items]
        health = calculate_inventory_health(inventory_dicts)
        inventory_summary = _build_inventory_summary(inventory_dicts)

        prompt = _build_user_prompt(state, inventory_summary, health)
        provider = get_llm_provider()
        response = await provider.chat(
            [
                Message(
                    role="system",
                    content=(
                        "You are an Amazon operations specialist. "
                        "Analyze inventory levels and provide actionable suggestions "
                        "for pricing adjustments, restocking, and inventory management. "
                        "All write operations require L1 human review. "
                        "Output valid JSON only."
                    ),
                ),
                Message(role="user", content=prompt),
            ],
            temperature=0.3,
        )

        parsed = _parse_llm_json(response.content)

        result = {
            "inventory": inventory_summary,
            "health_metrics": health,
            "inventory_alerts": parsed.get("inventory_alerts", []),
            "pricing_suggestions": parsed.get("pricing_suggestions", []),
            "restock_recommendations": parsed.get("restock_recommendations", []),
            "report": parsed.get("report", ""),
        }

        trace.append(
            make_trace_event(
                "operations_agent",
                AgentTraceStatus.COMPLETED,
                detail={
                    "item_count": len(inventory_items),
                    "low_stock_count": health["low_stock_count"],
                    "alert_count": len(result["inventory_alerts"]),
                    "pricing_suggestion_count": len(result["pricing_suggestions"]),
                },
            )
        )

    except Exception as exc:
        result = {
            "inventory": [],
            "health_metrics": {},
            "inventory_alerts": [],
            "pricing_suggestions": [],
            "restock_recommendations": [],
            "report": f"Operations analysis failed: {exc}",
            "error": str(exc),
        }
        trace.append(
            make_trace_event(
                "operations_agent",
                AgentTraceStatus.FAILED,
                detail={"error": str(exc)},
            )
        )

    return {"ops": result, "trace": trace}
