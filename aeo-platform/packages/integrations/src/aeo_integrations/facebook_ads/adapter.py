from __future__ import annotations

import logging
from decimal import Decimal
from typing import Any, Literal

import requests

from aeo_integrations.facebook_ads.config import FacebookAdsSettings
from aeo_integrations.facebook_ads.models import FacebookAdCampaign, FacebookAdSpendSnapshot

logger = logging.getLogger(__name__)


def _safe_decimal(value: Any) -> Decimal | None:
    if value is None:
        return None
    try:
        return Decimal(str(value))
    except Exception:
        return None


class FacebookAdsApiAdapter:
    def __init__(self, settings: FacebookAdsSettings) -> None:
        self._settings = settings
        self._base_url = f"https://graph.facebook.com/{settings.api_version}"
        self._ad_account_id = settings.ad_account_id

    @property
    def data_source(self) -> str:
        return "facebook"

    def _get(self, path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        url = f"{self._base_url}/{path}"
        params = params or {}
        params["access_token"] = self._settings.access_token
        response = requests.get(url, params=params, timeout=self._settings.request_timeout)
        response.raise_for_status()
        result: dict[str, Any] = response.json()
        return result

    def get_campaign(self, campaign_id: str) -> FacebookAdCampaign:
        data = self._get(
            f"{campaign_id}",
            {"fields": "id,name,status,objective,daily_budget,start_time,stop_time"},
        )
        return self._map_campaign(data)

    def list_campaigns(
        self, *, status: str | None = None, limit: int = 20
    ) -> list[FacebookAdCampaign]:
        params: dict[str, Any] = {
            "fields": "id,name,status,objective,daily_budget,start_time,stop_time",
            "limit": limit,
        }
        if status:
            params["effective_status"] = f"['{status}']"
        data = self._get(f"act_{self._ad_account_id}/campaigns", params)
        return [self._map_campaign(c) for c in data.get("data", [])[:limit]]

    def list_spend_snapshots(
        self, *, campaign_id: str | None = None, limit: int = 50
    ) -> list[FacebookAdSpendSnapshot]:
        params: dict[str, Any] = {
            "fields": "campaign_id,campaign_name,spend,impressions,clicks,actions,actions_value",
            "level": "campaign",
            "limit": limit,
        }
        if campaign_id:
            params["filtering"] = (
                f"[{{'field':'campaign.id','operator':'IN','value':['{campaign_id}']}}]"
            )
        data = self._get(f"act_{self._ad_account_id}/insights", params)
        return [self._map_snapshot(s) for s in data.get("data", [])[:limit]]

    def _map_campaign(self, data: dict[str, Any]) -> FacebookAdCampaign:
        status_map: dict[str, Literal["ACTIVE", "PAUSED", "ARCHIVED"]] = {
            "ACTIVE": "ACTIVE",
            "PAUSED": "PAUSED",
            "ARCHIVED": "ARCHIVED",
        }
        raw_status = data.get("status", "ACTIVE")
        return FacebookAdCampaign(
            campaign_id=str(data.get("id", "")),
            name=data.get("name", ""),
            status=status_map.get(raw_status, "ACTIVE"),
            campaign_type=data.get("objective", "CONVERSIONS"),
            daily_budget=_safe_decimal(data.get("daily_budget")),
            currency="USD",
            start_date=data.get("start_time", ""),
            end_date=data.get("stop_time"),
        )

    def _map_snapshot(self, data: dict[str, Any]) -> FacebookAdSpendSnapshot:
        actions = data.get("actions", [])
        conversions = sum(
            int(a.get("value", 0))
            for a in actions
            if a.get("action_type") in ("purchase", "offsite_conversion.purchase")
        )
        actions_value = data.get("actions_value", [])
        gmv = sum(
            float(a.get("value", 0))
            for a in actions_value
            if a.get("action_type") in ("purchase", "offsite_conversion.purchase")
        )
        return FacebookAdSpendSnapshot(
            campaign_id=str(data.get("campaign_id", "")),
            snapshot_date=data.get("date_start", ""),
            spend=_safe_decimal(data.get("spend")),
            impressions=int(data.get("impressions", 0)),
            clicks=int(data.get("clicks", 0)),
            conversions=conversions,
            attributed_gmv=_safe_decimal(gmv if gmv > 0 else None),
            currency="USD",
        )
