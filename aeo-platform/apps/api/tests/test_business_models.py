"""Tests for MV1-06 business data model skeleton."""

from aeo_api.db.models import AdCampaign, AdSpendSnapshot, OrderRecord
from sqlalchemy import inspect


def test_order_record_table_metadata() -> None:
    mapper = inspect(OrderRecord)
    columns = {col.key for col in mapper.columns}
    assert "external_order_id" in columns
    assert "sku" in columns
    assert "data_source" in columns
    assert OrderRecord.__tablename__ == "order_records"


def test_ad_campaign_table_metadata() -> None:
    mapper = inspect(AdCampaign)
    columns = {col.key for col in mapper.columns}
    assert "external_campaign_id" in columns
    assert "daily_budget" in columns
    assert AdCampaign.__tablename__ == "ad_campaigns"


def test_ad_spend_snapshot_table_metadata() -> None:
    mapper = inspect(AdSpendSnapshot)
    columns = {col.key for col in mapper.columns}
    assert "campaign_id" in columns
    assert "attributed_gmv" in columns
    assert AdSpendSnapshot.__tablename__ == "ad_spend_snapshots"


def test_business_models_have_mock_data_source_default() -> None:
    order_mapper = inspect(OrderRecord)
    campaign_mapper = inspect(AdCampaign)
    order_default = order_mapper.columns["data_source"].default
    campaign_default = campaign_mapper.columns["data_source"].default
    assert order_default is not None and order_default.arg == "mock"
    assert campaign_default is not None and campaign_default.arg == "mock"
