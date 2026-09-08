"""MV4-03: After-sales script library for customer service reply templates."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class AfterSalesScript:
    """A scenario-specific reply template for customer service."""

    script_id: str
    scenario: str
    platform: str
    template_text: str
    keywords: list[str] = field(default_factory=list)
    escalation_conditions: list[dict[str, Any]] = field(default_factory=list)
    confidence_threshold: float = 0.6

    def to_dict(self) -> dict[str, Any]:
        return {
            "script_id": self.script_id,
            "scenario": self.scenario,
            "platform": self.platform,
            "template_text": self.template_text,
            "keywords": list(self.keywords),
            "escalation_conditions": list(self.escalation_conditions),
            "confidence_threshold": self.confidence_threshold,
        }


_AMAZON_RETURN = AfterSalesScript(
    script_id="amazon-return-001",
    scenario="return",
    platform="amazon",
    template_text=(
        "Thank you for reaching out. We're sorry to hear you'd like to return this item. "
        "You can initiate a return through Your Orders on Amazon.com. "
        "Please ensure the item is in its original packaging. "
        "Once we receive the return, your refund will be processed within 3-5 business days."
    ),
    keywords=["return", "send back", "give back", "return item"],
    confidence_threshold=0.6,
)

_AMAZON_REFUND = AfterSalesScript(
    script_id="amazon-refund-001",
    scenario="refund",
    platform="amazon",
    template_text=(
        "We understand you'd like a refund. Let us look into your order right away. "
        "Refunds are typically processed to the original payment method within 5-7 business days "
        "after the return is received. If you haven't received your refund after this period, "
        "please contact us again and we'll investigate."
    ),
    keywords=["refund", "money back", "charge back", "reimburse"],
    confidence_threshold=0.5,
)

_AMAZON_SHIPPING = AfterSalesScript(
    script_id="amazon-shipping-001",
    scenario="shipping",
    platform="amazon",
    template_text=(
        "Thank you for your patience. Let me check the status of your shipment. "
        "You can track your order through Your Orders on Amazon.com. "
        "Standard shipping typically takes 3-5 business days. "
        "If your package hasn't arrived within the estimated delivery window, "
        "please let us know and we'll file a trace with the carrier."
    ),
    keywords=["shipping", "delivery", "track", "package", "where is my order"],
    confidence_threshold=0.6,
)

_AMAZON_COMPLAINT = AfterSalesScript(
    script_id="amazon-complaint-001",
    scenario="complaint",
    platform="amazon",
    template_text=(
        "We sincerely apologize for the inconvenience. Your feedback is important to us. "
        "We'd like to make this right. Could you please share more details about the issue? "
        "We'll review your case and provide a resolution as quickly as possible."
    ),
    keywords=["complaint", "unhappy", "terrible", "awful", "defective", "broken"],
    confidence_threshold=0.4,
)

_AMAZON_INQUIRY = AfterSalesScript(
    script_id="amazon-inquiry-001",
    scenario="inquiry",
    platform="amazon",
    template_text=(
        "Thank you for your inquiry! We're happy to help. "
        "Could you please provide your order number so we can look up the details? "
        "In the meantime, you can find product information on the product detail page."
    ),
    keywords=["question", "ask", "inquiry", "info", "detail"],
    confidence_threshold=0.7,
)

_AMAZON_EXCHANGE = AfterSalesScript(
    script_id="amazon-exchange-001",
    scenario="exchange",
    platform="amazon",
    template_text=(
        "We'd be happy to help with an exchange. "
        "Please initiate a return for the original item through Your Orders, "
        "then place a new order for the replacement. "
        "If the exchange is due to a defect, we can arrange a replacement at no extra cost."
    ),
    keywords=["exchange", "swap", "replace", "different size", "different color"],
    confidence_threshold=0.6,
)

_BUILTIN_SCRIPTS: list[AfterSalesScript] = [
    _AMAZON_RETURN,
    _AMAZON_REFUND,
    _AMAZON_SHIPPING,
    _AMAZON_COMPLAINT,
    _AMAZON_INQUIRY,
    _AMAZON_EXCHANGE,
]


class ScriptLibrary:
    """Registry of after-sales scripts indexed by (scenario, platform)."""

    def __init__(self, scripts: list[AfterSalesScript] | None = None) -> None:
        self._scripts = scripts if scripts is not None else list(_BUILTIN_SCRIPTS)

    def match(self, *, scenario: str, platform: str) -> list[AfterSalesScript]:
        return [s for s in self._scripts if s.scenario == scenario and s.platform == platform]

    def get_best(self, *, scenario: str, platform: str) -> AfterSalesScript | None:
        results = self.match(scenario=scenario, platform=platform)
        return results[0] if results else None

    def filter_by(
        self,
        *,
        scenario: str | None = None,
        platform: str | None = None,
    ) -> list[AfterSalesScript]:
        results = self._scripts
        if scenario is not None:
            results = [s for s in results if s.scenario == scenario]
        if platform is not None:
            results = [s for s in results if s.platform == platform]
        return results

    def list_all(self) -> list[AfterSalesScript]:
        return list(self._scripts)

    def list_scenarios(self) -> list[str]:
        return sorted({s.scenario for s in self._scripts})

    def list_platforms(self) -> list[str]:
        return sorted({s.platform for s in self._scripts})


_LIBRARY_INSTANCE: ScriptLibrary | None = None


def get_script_library() -> ScriptLibrary:
    global _LIBRARY_INSTANCE
    if _LIBRARY_INSTANCE is None:
        _LIBRARY_INSTANCE = ScriptLibrary()
    return _LIBRARY_INSTANCE
