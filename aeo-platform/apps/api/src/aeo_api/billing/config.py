"""P6-01: Stripe billing configuration."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class BillingSettings(BaseSettings):
    model_config = SettingsConfigDict(extra="ignore", env_prefix="STRIPE_")

    api_key: str = ""
    webhook_secret: str = ""
    price_pro_monthly: str = ""
    price_enterprise_monthly: str = ""
    trial_days: int = 14
    success_url: str = "http://localhost:3000/settings?billing=success"
    cancel_url: str = "http://localhost:3000/pricing?billing=cancelled"

    @property
    def enabled(self) -> bool:
        return bool(self.api_key)


@lru_cache
def get_billing_settings() -> BillingSettings:
    return BillingSettings()
