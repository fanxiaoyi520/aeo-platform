"""MV3-05 — operations_node Seller Central inspection integration tests."""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from aeo_orchestrator.nodes.operations import (
    _build_inspection_context,
    _try_inspect_seller_central,
    operations_node,
)


def test_build_inspection_context_degraded() -> None:
    inspection = {"degraded": True, "degraded_reason": "browser disabled"}
    ctx = _build_inspection_context(inspection)
    assert "unavailable" in ctx
    assert "browser disabled" in ctx


def test_build_inspection_context_with_data() -> None:
    inspection = {
        "degraded": False,
        "account_health": {"detected_indicators": ["policy violation"]},
        "listing_status": {"detected_statuses": ["active", "suppressed"]},
        "notifications": [
            {"text": "Action required: update shipping", "type": "notification"},
        ],
    }
    ctx = _build_inspection_context(inspection)
    assert "policy violation" in ctx
    assert "active" in ctx
    assert "Action required" in ctx


def test_build_inspection_context_empty() -> None:
    inspection = {"degraded": False, "account_health": {}, "listing_status": {}, "notifications": []}
    ctx = _build_inspection_context(inspection)
    assert "no data extracted" in ctx


def test_try_inspect_browser_disabled() -> None:
    with patch("aeo_browser.config.is_browser_enabled", return_value=False):
        result = _try_inspect_seller_central()
    assert result["degraded"] is True
    assert "browser disabled" in result["degraded_reason"]


def test_try_inspect_browser_enabled_no_storage() -> None:
    with patch("aeo_browser.config.is_browser_enabled", return_value=True):
        with patch("aeo_browser.seller_central.seller_central_storage_state", return_value=None):
            result = _try_inspect_seller_central()
    assert result["degraded"] is True


@pytest.mark.asyncio
async def test_operations_node_includes_inspection_in_result() -> None:
    mock_inv_item = MagicMock()
    mock_inv_item.model_dump.return_value = {
        "sku": "TEST-001",
        "fulfillment_channel": "FBA",
        "available_quantity": 100,
        "inbound_quantity": 50,
        "reserved_quantity": 10,
        "warehouse": "US-EAST",
    }

    mock_inv_client = MagicMock()
    mock_inv_client.list_inventory.return_value = [mock_inv_item]

    mock_llm_response = MagicMock()
    mock_llm_response.content = json.dumps({
        "inventory_alerts": [],
        "pricing_suggestions": [],
        "restock_recommendations": [],
        "report": "All good.",
    })

    mock_provider = MagicMock()
    mock_provider.chat = AsyncMock(return_value=mock_llm_response)

    degraded_inspection = {
        "degraded": True,
        "degraded_reason": "browser disabled",
        "account_health": {},
        "listing_status": {},
        "notifications": [],
        "screenshots": {},
        "inspected_at": "2026-09-10T12:00:00",
    }

    state = {
        "sku": "TEST-001",
        "product_info": {"title": "Test Product", "price": "$29.99"},
        "task_id": "test-123",
        "platform": "amazon",
    }

    with patch("aeo_orchestrator.nodes.operations.get_inventory_client", return_value=mock_inv_client):
        with patch("aeo_orchestrator.nodes.operations.get_llm_provider", return_value=mock_provider):
            with patch("aeo_orchestrator.nodes.operations._try_inspect_seller_central", return_value=degraded_inspection):
                result = await operations_node(state)

    ops = result["ops"]
    assert "seller_central_inspection" in ops
    assert ops["seller_central_inspection"]["degraded"] is True
    assert ops["report"] == "All good."

    call_args = mock_provider.chat.call_args
    user_msg = call_args[0][0][1].content
    assert "Seller Central inspection unavailable" in user_msg


@pytest.mark.asyncio
async def test_operations_node_with_successful_inspection() -> None:
    mock_inv_item = MagicMock()
    mock_inv_item.model_dump.return_value = {
        "sku": "TEST-002",
        "fulfillment_channel": "FBA",
        "available_quantity": 50,
        "inbound_quantity": 0,
        "reserved_quantity": 5,
        "warehouse": "US-WEST",
    }

    mock_inv_client = MagicMock()
    mock_inv_client.list_inventory.return_value = [mock_inv_item]

    mock_llm_response = MagicMock()
    mock_llm_response.content = json.dumps({
        "inventory_alerts": [{"sku": "TEST-002", "level": "warning", "message": "Low stock"}],
        "pricing_suggestions": [],
        "restock_recommendations": [],
        "report": "Restock needed.",
    })

    mock_provider = MagicMock()
    mock_provider.chat = AsyncMock(return_value=mock_llm_response)

    successful_inspection = {
        "degraded": False,
        "degraded_reason": "",
        "account_health": {"detected_indicators": ["policy violation"]},
        "listing_status": {"detected_statuses": ["active"]},
        "notifications": [{"text": "Action Required: update listing", "type": "notification"}],
        "screenshots": {"account_health": "/tmp/ah.png"},
        "inspected_at": "2026-09-10T12:00:00",
    }

    state = {
        "sku": "TEST-002",
        "product_info": {"title": "Widget", "price": "$19.99"},
        "task_id": "test-456",
        "platform": "amazon",
    }

    with patch("aeo_orchestrator.nodes.operations.get_inventory_client", return_value=mock_inv_client):
        with patch("aeo_orchestrator.nodes.operations.get_llm_provider", return_value=mock_provider):
            with patch("aeo_orchestrator.nodes.operations._try_inspect_seller_central", return_value=successful_inspection):
                result = await operations_node(state)

    ops = result["ops"]
    assert ops["seller_central_inspection"]["degraded"] is False
    assert "policy violation" in str(ops["seller_central_inspection"]["account_health"])

    call_args = mock_provider.chat.call_args
    user_msg = call_args[0][0][1].content
    assert "policy violation" in user_msg
    assert "Action Required" in user_msg
