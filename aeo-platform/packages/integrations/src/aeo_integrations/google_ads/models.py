"""Google Ads integration models."""

from __future__ import annotations

from decimal import Decimal

from pydantic import BaseModel, Field


class GoogleAdCampaign(BaseModel):
    """Normalized Google Ads campaign."""

    campaign_id: str
    name: str = ""
    status: str = "ENABLED"
    campaign_type: str = "SEARCH"
    daily_budget: Decimal | None = None
    currency: str = "USD"
    start_date: str = ""
    end_date: str | None = None
    associated_skus: list[str] = Field(default_factory=list)


class GoogleAdSpendSnapshot(BaseModel):
    """Daily Google Ads performance snapshot."""

    campaign_id: str
    snapshot_date: str = ""
    spend: Decimal | None = None
    impressions: int = 0
    clicks: int = 0
    conversions: int = 0
    attributed_gmv: Decimal | None = None
    currency: str = "USD"
