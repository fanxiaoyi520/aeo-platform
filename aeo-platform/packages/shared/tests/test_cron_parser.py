"""MV2-03 — cron expression parser tests."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from aeo_shared.cron_parser import CronSchedule, matches, next_run, parse_cron


def test_parse_all_stars() -> None:
    s = parse_cron("* * * * *")
    assert s.minutes == frozenset(range(60))
    assert s.hours == frozenset(range(24))
    assert s.days_of_month == frozenset(range(1, 32))
    assert s.months == frozenset(range(1, 13))
    assert s.days_of_week == frozenset(range(7))


def test_parse_specific_values() -> None:
    s = parse_cron("30 2 15 6 3")
    assert s.minutes == {30}
    assert s.hours == {2}
    assert s.days_of_month == {15}
    assert s.months == {6}
    assert s.days_of_week == {3}


def test_parse_ranges() -> None:
    s = parse_cron("1-5 9-17 * * *")
    assert s.minutes == {1, 2, 3, 4, 5}
    assert s.hours == frozenset(range(9, 18))


def test_parse_lists() -> None:
    s = parse_cron("0,15,30,45 * * * *")
    assert s.minutes == {0, 15, 30, 45}


def test_parse_steps() -> None:
    s = parse_cron("*/15 * * * *")
    assert s.minutes == {0, 15, 30, 45}


def test_parse_range_with_step() -> None:
    s = parse_cron("1-10/3 * * * *")
    assert s.minutes == {1, 4, 7, 10}


def test_parse_combined_list_and_range() -> None:
    s = parse_cron("1,5,10-15 * * * *")
    assert s.minutes == {1, 5, 10, 11, 12, 13, 14, 15}


def test_parse_month_names() -> None:
    s = parse_cron("0 0 1 jan *")
    assert s.months == {1}


def test_parse_dow_names() -> None:
    s = parse_cron("0 9 * * mon-fri")
    assert s.days_of_week == {0, 1, 2, 3, 4}


def test_parse_single_step_value() -> None:
    s = parse_cron("5/20 * * * *")
    assert s.minutes == {5, 25, 45}


def test_invalid_field_count() -> None:
    with pytest.raises(ValueError, match="expected 5 fields"):
        parse_cron("* *")


def test_invalid_value_out_of_range() -> None:
    with pytest.raises(ValueError, match="out of range"):
        parse_cron("60 * * * *")


def test_invalid_characters() -> None:
    with pytest.raises(ValueError):
        parse_cron("abc * * * *")


def test_invalid_range_reversed() -> None:
    with pytest.raises(ValueError, match="start > end"):
        parse_cron("10-5 * * * *")


def test_invalid_step_zero() -> None:
    with pytest.raises(ValueError, match="step must be positive"):
        parse_cron("*/0 * * * *")


def test_matches_exact() -> None:
    s = parse_cron("30 14 18 3 2")
    dt = datetime(2026, 3, 18, 14, 30, tzinfo=UTC)
    assert matches(s, dt)


def test_matches_non_matching() -> None:
    s = parse_cron("0 9 * * *")
    dt = datetime(2026, 3, 15, 10, 0, tzinfo=UTC)
    assert not matches(s, dt)


def test_next_run_basic() -> None:
    s = parse_cron("0 9 * * *")
    after = datetime(2026, 3, 15, 8, 0, tzinfo=UTC)
    result = next_run(s, after)
    assert result == datetime(2026, 3, 15, 9, 0, tzinfo=UTC)


def test_next_run_next_day() -> None:
    s = parse_cron("0 9 * * *")
    after = datetime(2026, 3, 15, 10, 0, tzinfo=UTC)
    result = next_run(s, after)
    assert result == datetime(2026, 3, 16, 9, 0, tzinfo=UTC)


def test_next_run_specific_minute() -> None:
    s = parse_cron("*/15 * * * *")
    after = datetime(2026, 3, 15, 10, 16, tzinfo=UTC)
    result = next_run(s, after)
    assert result == datetime(2026, 3, 15, 10, 30, tzinfo=UTC)


def test_next_run_naive_datetime() -> None:
    s = parse_cron("0 12 * * *")
    after = datetime(2026, 3, 15, 10, 0)
    result = next_run(s, after)
    assert result.tzinfo == UTC
    assert result.hour == 12


def test_next_run_wraps_year() -> None:
    s = parse_cron("0 0 1 1 *")
    after = datetime(2026, 12, 31, 23, 59, tzinfo=UTC)
    result = next_run(s, after)
    assert result.month == 1
    assert result.day == 1
    assert result.year == 2027


def test_cron_schedule_is_frozen() -> None:
    s = parse_cron("* * * * *")
    assert isinstance(s, CronSchedule)
    with pytest.raises(AttributeError):
        s.minutes = frozenset()  # type: ignore[misc]
