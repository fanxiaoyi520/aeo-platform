"""5-field cron expression parser (minute hour dom month dow).

Supports: ``*``, specific values, ranges (``1-5``), lists (``1,3,5``),
steps (``*/5``, ``1-10/2``).  Day-of-week uses 0=Monday … 6=Sunday
(Python ``weekday()`` convention).  All times are UTC.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

_FIELD_BOUNDS: list[tuple[int, int]] = [
    (0, 59),  # minute
    (0, 23),  # hour
    (1, 31),  # day of month
    (1, 12),  # month
    (0, 6),  # day of week (0=Monday)
]

_MONTH_NAMES = {
    "jan": 1,
    "feb": 2,
    "mar": 3,
    "apr": 4,
    "may": 5,
    "jun": 6,
    "jul": 7,
    "aug": 8,
    "sep": 9,
    "oct": 10,
    "nov": 11,
    "dec": 12,
}

_DOW_NAMES = {
    "mon": 0,
    "tue": 1,
    "wed": 2,
    "thu": 3,
    "fri": 4,
    "sat": 5,
    "sun": 6,
}


@dataclass(frozen=True)
class CronSchedule:
    """Parsed cron schedule — each field is a frozenset of valid values."""

    minutes: frozenset[int]
    hours: frozenset[int]
    days_of_month: frozenset[int]
    months: frozenset[int]
    days_of_week: frozenset[int]


def _resolve_name(token: str, field_index: int) -> int:
    low = token.lower()
    if field_index == 3 and low in _MONTH_NAMES:
        return _MONTH_NAMES[low]
    if field_index == 4 and low in _DOW_NAMES:
        return _DOW_NAMES[low]
    raise ValueError(f"unknown name {token!r} in field {field_index}")


def _parse_field(raw: str, field_index: int) -> frozenset[int]:
    lo, hi = _FIELD_BOUNDS[field_index]
    values: set[int] = set()

    for part in raw.split(","):
        step: int | None = None
        if "/" in part:
            range_part, step_part = part.split("/", 1)
            try:
                step = int(step_part)
            except ValueError:
                raise ValueError(f"invalid step {step_part!r}") from None
            if step <= 0:
                raise ValueError(f"step must be positive, got {step}")
        else:
            range_part = part

        if range_part == "*":
            start, end = lo, hi
        elif "-" in range_part:
            parts = range_part.split("-", 1)
            start = _parse_value(parts[0], field_index)
            end = _parse_value(parts[1], field_index)
            if start > end:
                raise ValueError(f"invalid range {range_part}: start > end")
        else:
            val = _parse_value(range_part, field_index)
            if step is not None:
                start, end = val, hi
            else:
                values.add(val)
                continue

        if step is None:
            step = 1
        values.update(range(start, end + 1, step))

    if not values:
        raise ValueError(f"empty field {field_index}")
    return frozenset(values)


def _parse_value(token: str, field_index: int) -> int:
    lo, hi = _FIELD_BOUNDS[field_index]
    try:
        val = int(token)
    except ValueError:
        val = _resolve_name(token, field_index)
    if val < lo or val > hi:
        raise ValueError(f"value {val} out of range [{lo}, {hi}] for field {field_index}")
    return val


def parse_cron(expression: str) -> CronSchedule:
    """Parse a 5-field cron expression into a :class:`CronSchedule`."""
    fields = expression.strip().split()
    if len(fields) != 5:
        raise ValueError(f"expected 5 fields, got {len(fields)}: {expression!r}")
    minutes = _parse_field(fields[0], 0)
    hours = _parse_field(fields[1], 1)
    days_of_month = _parse_field(fields[2], 2)
    months = _parse_field(fields[3], 3)
    days_of_week = _parse_field(fields[4], 4)
    return CronSchedule(
        minutes=minutes,
        hours=hours,
        days_of_month=days_of_month,
        months=months,
        days_of_week=days_of_week,
    )


def matches(schedule: CronSchedule, dt: datetime) -> bool:
    """Check whether *dt* (UTC) falls on the schedule (minute precision)."""
    return (
        dt.minute in schedule.minutes
        and dt.hour in schedule.hours
        and dt.month in schedule.months
        and dt.day in schedule.days_of_month
        and dt.weekday() in schedule.days_of_week
    )


def next_run(schedule: CronSchedule, after: datetime) -> datetime:
    """Return the next matching UTC datetime after *after* (minute granularity).

    Searches up to 366 days ahead; raises ``ValueError`` if no match is found.
    """
    if after.tzinfo is None:
        after = after.replace(tzinfo=UTC)
    candidate = after.replace(second=0, microsecond=0) + timedelta(minutes=1)
    limit = after + timedelta(days=366)
    while candidate <= limit:
        if candidate.month not in schedule.months:
            candidate = _skip_to_next_month(candidate, schedule)
            continue
        if (
            candidate.day not in schedule.days_of_month
            or candidate.weekday() not in schedule.days_of_week
        ):
            candidate = candidate.replace(hour=0, minute=0) + timedelta(days=1)
            continue
        if candidate.hour not in schedule.hours:
            candidate = candidate.replace(minute=0) + timedelta(hours=1)
            continue
        if candidate.minute not in schedule.minutes:
            candidate += timedelta(minutes=1)
            continue
        return candidate
    raise ValueError("no matching time within 366 days")


def _skip_to_next_month(candidate: datetime, schedule: CronSchedule) -> datetime:
    month = candidate.month
    year = candidate.year
    while True:
        month += 1
        if month > 12:
            month = 1
            year += 1
        if month in schedule.months:
            return datetime(year, month, 1, 0, 0, tzinfo=UTC)
        if year > candidate.year + 1:
            return candidate + timedelta(days=366)
