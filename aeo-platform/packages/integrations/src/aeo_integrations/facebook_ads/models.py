"""Facebook Ads integration models."""

from __future__ import annotations

from decimal import Decimal

from pydantic import BaseModel, Field


class FacebookAdCampaign(BaseModel):
    """Normalized Facebook Ads campaign."""

    campaign_id: str
    name: str = ""
    status: str = "ACTIVE"
    campaign_type: str = "CONVERSIONS"
    daily_budget: Decimal | None = None
    currency: str = "USD"
    start_date: str = ""
    end_date: str | None = None
    associated_skus: list[str] = Field(default_factory=list)


class FacebookAdSpendSnapshot(BaseModel):
    """Daily Facebook Ads performance snapshot."""

    campaign_id: str
    snapshot_date: str = ""
    spend: Decimal | None = None
    impressions: int = 0
    clicks: int = 0
    conversions: int = 0
    attributed_gmv: Decimal | None = None
    currency: str = "USD"
