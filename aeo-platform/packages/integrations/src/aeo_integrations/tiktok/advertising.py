"""TikTok Shop advertising client with mock fallback."""

from __future__ import annotations

import os

from aeo_integrations.tiktok.models import TikTokAdCampaign, TikTokAdReport


class TikTokAdvertisingClient:
    def __init__(self, access_token: str | None = None, shop_id: str | None = None) -> None:
        self.access_token = access_token or os.environ.get("TIKTOK_ACCESS_TOKEN")
        self.shop_id = shop_id or os.environ.get("TIKTOK_SHOP_ID")
        self._use_mock = not (self.access_token and self.shop_id)

    @property
    def data_source(self) -> str:
        return "mock" if self._use_mock else "api"

    def list_campaigns(
        self, *, status: str | None = None, limit: int = 20
    ) -> list[TikTokAdCampaign]:
        if self._use_mock:
            return self._mock_campaigns(status=status, limit=limit)
        return self._api_list_campaigns(status=status, limit=limit)

    def get_campaign(self, campaign_id: str) -> TikTokAdCampaign:
        if self._use_mock:
            campaigns = self._mock_campaigns(limit=100)
            for c in campaigns:
                if c.campaign_id == campaign_id:
                    return c
            msg = f"Campaign not found: {campaign_id}"
            raise KeyError(msg)
        return self._api_get_campaign(campaign_id)

    def list_spend_snapshots(
        self,
        *,
        campaign_id: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        limit: int = 50,
    ) -> list[TikTokAdReport]:
        if self._use_mock:
            return self._mock_spend_snapshots(
                campaign_id=campaign_id,
                start_date=start_date,
                end_date=end_date,
                limit=limit,
            )
        return self._api_list_spend_snapshots(
            campaign_id=campaign_id,
            start_date=start_date,
            end_date=end_date,
            limit=limit,
        )

    def _api_list_campaigns(self, *, status: str | None, limit: int) -> list[TikTokAdCampaign]:
        raise NotImplementedError("TikTok Advertising API integration pending")

    def _api_get_campaign(self, campaign_id: str) -> TikTokAdCampaign:
        raise NotImplementedError("TikTok Advertising API integration pending")

    def _api_list_spend_snapshots(
        self,
        *,
        campaign_id: str | None,
        start_date: str | None,
        end_date: str | None,
        limit: int,
    ) -> list[TikTokAdReport]:
        raise NotImplementedError("TikTok Advertising API integration pending")

    def _mock_campaigns(
        self, *, status: str | None = None, limit: int = 20
    ) -> list[TikTokAdCampaign]:
        campaigns = [
            TikTokAdCampaign(
                campaign_id="TT-AD-001",
                name="Earbuds Video Promo",
                status="ENABLE",
                budget="100.00",
                currency="USD",
                ad_type="VIDEO_SHOPPING",
                create_time="2026-09-01T00:00:00Z",
                update_time="2026-09-15T10:00:00Z",
            ),
            TikTokAdCampaign(
                campaign_id="TT-AD-002",
                name="Phone Case Live Sale",
                status="ENABLE",
                budget="75.00",
                currency="USD",
                ad_type="LIVE_SHOPPING",
                create_time="2026-09-05T00:00:00Z",
                update_time="2026-09-16T14:30:00Z",
            ),
            TikTokAdCampaign(
                campaign_id="TT-AD-003",
                name="Paused Campaign",
                status="DISABLE",
                budget="50.00",
                currency="USD",
                ad_type="VIDEO_SHOPPING",
                create_time="2026-08-20T00:00:00Z",
                update_time="2026-09-10T09:00:00Z",
            ),
        ]
        if status:
            campaigns = [c for c in campaigns if c.status == status]
        return campaigns[:limit]

    def _mock_spend_snapshots(
        self,
        *,
        campaign_id: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        limit: int = 50,
    ) -> list[TikTokAdReport]:
        reports = [
            TikTokAdReport(
                campaign_id="TT-AD-001",
                date="2026-09-15",
                impressions=5000,
                clicks=250,
                spend="45.50",
                conversions=15,
                gmv="449.85",
                currency="USD",
            ),
            TikTokAdReport(
                campaign_id="TT-AD-001",
                date="2026-09-16",
                impressions=4800,
                clicks=230,
                spend="42.30",
                conversions=12,
                gmv="359.88",
                currency="USD",
            ),
            TikTokAdReport(
                campaign_id="TT-AD-002",
                date="2026-09-15",
                impressions=3200,
                clicks=180,
                spend="38.20",
                conversions=8,
                gmv="399.92",
                currency="USD",
            ),
            TikTokAdReport(
                campaign_id="TT-AD-002",
                date="2026-09-16",
                impressions=3500,
                clicks=195,
                spend="40.10",
                conversions=10,
                gmv="499.90",
                currency="USD",
            ),
        ]
        if campaign_id:
            reports = [r for r in reports if r.campaign_id == campaign_id]
        if start_date:
            reports = [r for r in reports if r.date >= start_date]
        if end_date:
            reports = [r for r in reports if r.date <= end_date]
        return reports[:limit]
