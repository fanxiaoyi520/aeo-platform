from __future__ import annotations

import logging
from decimal import Decimal
from typing import Any, Literal

import requests

from aeo_integrations.google_ads.auth import get_access_token
from aeo_integrations.google_ads.config import GoogleAdsSettings
from aeo_integrations.google_ads.models import GoogleAdCampaign, GoogleAdSpendSnapshot

logger = logging.getLogger(__name__)


def _safe_decimal(value: Any) -> Decimal | None:
    if value is None:
        return None
    try:
        return Decimal(str(value))
    except Exception:
        return None


class GoogleAdsApiAdapter:
    def __init__(self, settings: GoogleAdsSettings) -> None:
        self._settings = settings
        self._base_url = f"https://googleads.googleapis.com/{settings.api_version}"
        self._customer_id = settings.clean_customer_id

    @property
    def data_source(self) -> str:
        return "google"

    def _get_headers(self) -> dict[str, str]:
        token = get_access_token(
            self._settings.client_id,
            self._settings.client_secret,
            self._settings.refresh_token,
        )
        return {
            "Authorization": f"Bearer {token.access_token}",
            "developer-token": self._settings.developer_token,
            "Content-Type": "application/json",
        }

    def _search(self, query: str) -> list[dict[str, Any]]:
        url = f"{self._base_url}/customers/{self._customer_id}/googleAds:searchStream"
        response = requests.post(
            url,
            headers=self._get_headers(),
            json={"query": query},
            timeout=self._settings.request_timeout,
        )
        response.raise_for_status()
        data = response.json()
        results: list[dict[str, Any]] = []
        for batch in data:
            results.extend(batch.get("results", []))
        return results

    def get_campaign(self, campaign_id: str) -> GoogleAdCampaign:
        query = f"""
            SELECT
                campaign.id,
                campaign.name,
                campaign.status,
                campaign.advertising_channel_type,
                campaign_budget.amount_micros,
                campaign.start_date,
                campaign.end_date
            FROM campaign
            WHERE campaign.id = {campaign_id}
        """
        results = self._search(query)
        if not results:
            msg = f"Campaign not found: {campaign_id}"
            raise KeyError(msg)
        return self._map_campaign(results[0])

    def list_campaigns(
        self, *, status: str | None = None, limit: int = 20
    ) -> list[GoogleAdCampaign]:
        query = """
            SELECT
                campaign.id,
                campaign.name,
                campaign.status,
                campaign.advertising_channel_type,
                campaign_budget.amount_micros,
                campaign.start_date,
                campaign.end_date
            FROM campaign
            ORDER BY campaign.id
        """
        results = self._search(query)
        campaigns = [self._map_campaign(r) for r in results]
        if status:
            campaigns = [c for c in campaigns if c.status == status]
        return campaigns[:limit]

    def list_spend_snapshots(
        self, *, campaign_id: str | None = None, limit: int = 50
    ) -> list[GoogleAdSpendSnapshot]:
        where_clause = ""
        if campaign_id:
            where_clause = f"WHERE campaign.id = {campaign_id}"
        query = f"""
            SELECT
                campaign.id,
                segments.date,
                metrics.cost_micros,
                metrics.impressions,
                metrics.clicks,
                metrics.conversions,
                metrics.conversions_value
            FROM customer
            WHERE segments.date DURING LAST_30_DAYS
            {where_clause}
            ORDER BY segments.date DESC
        """
        results = self._search(query)
        return [self._map_snapshot(r) for r in results[:limit]]

    def _map_campaign(self, data: dict[str, Any]) -> GoogleAdCampaign:
        campaign = data.get("campaign", {})
        budget = data.get("campaignBudget", {})
        status_map: dict[str, Literal["ENABLED", "PAUSED", "REMOVED"]] = {
            "ENABLED": "ENABLED",
            "PAUSED": "PAUSED",
            "REMOVED": "REMOVED",
        }
        raw_status = campaign.get("status", "ENABLED")
        channel_type = campaign.get("advertisingChannelType", "SEARCH")
        amount_micros = budget.get("amountMicros", 0)
        daily_budget = _safe_decimal(amount_micros / 1_000_000) if amount_micros else None
        return GoogleAdCampaign(
            campaign_id=str(campaign.get("id", "")),
            name=campaign.get("name", ""),
            status=status_map.get(raw_status, "ENABLED"),
            campaign_type=channel_type,
            daily_budget=daily_budget,
            currency="USD",
            start_date=campaign.get("startDate", ""),
            end_date=campaign.get("endDate") or None,
        )

    def _map_snapshot(self, data: dict[str, Any]) -> GoogleAdSpendSnapshot:
        campaign = data.get("campaign", {})
        segments = data.get("segments", {})
        metrics = data.get("metrics", {})
        cost_micros = metrics.get("costMicros", 0)
        return GoogleAdSpendSnapshot(
            campaign_id=str(campaign.get("id", "")),
            snapshot_date=segments.get("date", ""),
            spend=_safe_decimal(cost_micros / 1_000_000) if cost_micros else None,
            impressions=int(metrics.get("impressions", 0)),
            clicks=int(metrics.get("clicks", 0)),
            conversions=int(metrics.get("conversions", 0)),
            attributed_gmv=_safe_decimal(metrics.get("conversionsValue")),
            currency="USD",
        )
