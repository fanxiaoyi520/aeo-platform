"""MV2-01 acceptance — selection scoring model and competitor pool."""

from __future__ import annotations

from pathlib import Path

import pytest

_AEO_PLATFORM_ROOT = Path(__file__).resolve().parents[3]
_SHARED_SRC = _AEO_PLATFORM_ROOT / "packages" / "shared" / "src" / "aeo_shared"

_SCORING_ARTIFACTS = [
    "packages/shared/src/aeo_shared/selection_scoring.py",
    "apps/api/src/aeo_api/routers/selection.py",
    "apps/api/src/aeo_api/schemas/selection.py",
    "apps/api/alembic/versions/0003_selection_scoring.py",
]


@pytest.mark.parametrize("relative_path", _SCORING_ARTIFACTS)
def test_mv2_01_artifacts_exist(relative_path: str) -> None:
    path = _AEO_PLATFORM_ROOT / relative_path
    assert path.is_file(), f"missing MV2-01 artifact: {relative_path}"


def test_mv2_01_selection_router_registered() -> None:
    main_source = (_AEO_PLATFORM_ROOT / "apps" / "api" / "src" / "aeo_api" / "main.py").read_text(
        encoding="utf-8"
    )
    assert "selection" in main_source


def test_mv2_01_db_models_exist() -> None:
    models_source = (
        _AEO_PLATFORM_ROOT / "apps" / "api" / "src" / "aeo_api" / "db" / "models.py"
    ).read_text(encoding="utf-8")
    assert "CompetitorListing" in models_source
    assert "SelectionScore" in models_source
    assert "competitor_listings" in models_source
    assert "selection_scores" in models_source


def test_mv2_01_migration_exists() -> None:
    migration = (
        _AEO_PLATFORM_ROOT / "apps" / "api" / "alembic" / "versions" / "0003_selection_scoring.py"
    ).read_text(encoding="utf-8")
    assert "competitor_listings" in migration
    assert "selection_scores" in migration
    assert "down_revision" in migration
    assert '"0002"' in migration


def test_mv2_01_score_product_basic() -> None:
    from aeo_shared.selection_scoring import SelectionInput, score_product

    result = score_product(
        SelectionInput(
            sku="TEST-001",
            price=29.99,
            rating=4.2,
            review_count=150,
            has_title=True,
            has_bullets=True,
            has_keywords=True,
            has_images=False,
        )
    )
    assert result.sku == "TEST-001"
    assert 0 <= result.total_score <= 100
    assert 0 <= result.demand_score <= 100
    assert 0 <= result.competition_score <= 100
    assert 0 <= result.profitability_score <= 100
    assert result.completeness_score == 75.0
    assert result.recommendation in ("proceed", "review", "skip")


def test_mv2_01_score_with_competitors() -> None:
    from aeo_shared.selection_scoring import CompetitorData, SelectionInput, score_product

    competitors = [
        CompetitorData(asin="B001", price=25.0, rating=4.0, review_count=200),
        CompetitorData(asin="B002", price=35.0, rating=3.8, review_count=100),
    ]
    result = score_product(
        SelectionInput(
            sku="TEST-002",
            price=29.99,
            rating=4.5,
            review_count=50,
            has_title=True,
            has_bullets=True,
            has_keywords=True,
            has_images=True,
            competitors=competitors,
        )
    )
    assert result.competitor_count == 2
    assert result.competition_score > 50
    assert result.total_score > 0


def test_mv2_01_recommendation_thresholds() -> None:
    from aeo_shared.selection_scoring import SelectionInput, score_product

    high_score = score_product(
        SelectionInput(
            sku="HIGH",
            price=30.0,
            rating=4.8,
            review_count=500,
            has_title=True,
            has_bullets=True,
            has_keywords=True,
            has_images=True,
        )
    )
    assert high_score.recommendation == "proceed"

    low_score = score_product(
        SelectionInput(
            sku="LOW",
            has_title=False,
            has_bullets=False,
            has_keywords=False,
            has_images=False,
        )
    )
    assert low_score.recommendation in ("review", "skip")
    assert low_score.completeness_score == 0.0


def test_mv2_01_shared_exports() -> None:
    from aeo_shared import SelectionInput, SelectionResult, score_product

    assert callable(score_product)
    result = score_product(SelectionInput(sku="EXPORT-TEST"))
    assert isinstance(result, SelectionResult)
