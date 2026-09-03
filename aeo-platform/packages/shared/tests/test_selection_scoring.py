"""MV2-01 — selection scoring model unit tests."""

from __future__ import annotations

from aeo_shared.selection_scoring import (
    CompetitorData,
    SelectionInput,
    SelectionResult,
    score_product,
)


def test_score_minimal_input() -> None:
    result = score_product(SelectionInput(sku="MIN-001"))
    assert isinstance(result, SelectionResult)
    assert result.sku == "MIN-001"
    assert result.total_score >= 0
    assert result.competitor_count == 0


def test_score_full_input() -> None:
    competitors = [
        CompetitorData(asin="B001", price=20.0, rating=4.0, review_count=300),
        CompetitorData(asin="B002", price=30.0, rating=3.5, review_count=100),
        CompetitorData(asin="B003", price=25.0, rating=4.2, review_count=500),
    ]
    result = score_product(
        SelectionInput(
            sku="FULL-001",
            platform="amazon",
            marketplace="US",
            price=25.0,
            rating=4.5,
            review_count=200,
            category="Home & Kitchen",
            brand="TestBrand",
            has_title=True,
            has_bullets=True,
            has_keywords=True,
            has_images=True,
            competitors=competitors,
        )
    )
    assert result.total_score > 60
    assert result.demand_score > 50
    assert result.competitor_count == 3
    assert result.recommendation == "proceed"


def test_score_no_competitors_high_competition_score() -> None:
    result = score_product(
        SelectionInput(
            sku="NO-COMP",
            price=30.0,
            has_title=True,
            has_bullets=True,
        )
    )
    assert result.competition_score == 80.0


def test_score_many_competitors_low_score() -> None:
    competitors = [CompetitorData(asin=f"B{i:03d}") for i in range(50)]
    result = score_product(
        SelectionInput(
            sku="MANY-COMP",
            price=30.0,
            competitors=competitors,
        )
    )
    assert result.competition_score == 10.0


def test_score_completeness_partial() -> None:
    result = score_product(
        SelectionInput(
            sku="PARTIAL",
            has_title=True,
            has_bullets=False,
            has_keywords=True,
            has_images=False,
        )
    )
    assert result.completeness_score == 50.0


def test_score_profitability_no_price() -> None:
    result = score_product(SelectionInput(sku="NO-PRICE"))
    assert result.profitability_score == 30.0


def test_score_profitability_premium_price() -> None:
    competitors = [CompetitorData(asin="B001", price=20.0)]
    result = score_product(
        SelectionInput(
            sku="PREMIUM",
            price=50.0,
            competitors=competitors,
        )
    )
    assert result.profitability_score < 50


def test_result_to_dict() -> None:
    result = score_product(SelectionInput(sku="DICT-TEST", has_title=True))
    d = result.to_dict()
    assert "sku" in d
    assert "total_score" in d
    assert "demand_score" in d
    assert "recommendation" in d
    assert isinstance(d["detail"], dict)
