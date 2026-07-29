from __future__ import annotations

import datetime as dt
from functools import wraps
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


_DEFAULT_MEMBER_TIMEZONE = "Asia/Kolkata"
_PATCH_MARKER = "_hm_member_home_schedule_presentation_v1"
_CLOSED_STATUSES = {"cancelled", "completed", "rescheduled"}


def _text(value: object) -> str:
    return str(value or "").strip()


def _parse_utc(value: object) -> dt.datetime | None:
    text = _text(value)
    if not text:
        return None
    try:
        parsed = dt.datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=dt.timezone.utc)
    return parsed.astimezone(dt.timezone.utc)


def _parse_date(value: object) -> dt.date | None:
    text = _text(value)
    if not text:
        return None
    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%d-%m-%Y", "%d/%m/%Y"):
        try:
            return dt.datetime.strptime(text[:10], fmt).date()
        except ValueError:
            pass
    return None


def _parse_time(value: object) -> dt.time | None:
    text = _text(value).upper()
    if not text:
        return None
    for fmt in ("%I:%M %p", "%H:%M", "%I %p", "%H"):
        try:
            return dt.datetime.strptime(text, fmt).time()
        except ValueError:
            pass
    return None


def _zone(value: object) -> ZoneInfo:
    candidate = _text(value) or _DEFAULT_MEMBER_TIMEZONE
    try:
        return ZoneInfo(candidate)
    except (ZoneInfoNotFoundError, ValueError):
        return ZoneInfo(_DEFAULT_MEMBER_TIMEZONE)


def _local_schedule_utc(row: dict[str, Any], *, use_end: bool) -> dt.datetime | None:
    schedule_date = _parse_date(row.get("schedule_date"))
    selected_time = _parse_time(row.get("end_time" if use_end else "start_time"))
    if not schedule_date or not selected_time:
        return None
    timezone_name = (
        row.get("member_timezone_name")
        or row.get("source_timezone_name")
        or _DEFAULT_MEMBER_TIMEZONE
    )
    local_value = dt.datetime.combine(schedule_date, selected_time).replace(
        tzinfo=_zone(timezone_name)
    )
    return local_value.astimezone(dt.timezone.utc)


def _schedule_start_utc(row: dict[str, Any]) -> dt.datetime | None:
    return _parse_utc(row.get("start_at_utc")) or _local_schedule_utc(
        row, use_end=False
    )


def _schedule_end_utc(row: dict[str, Any]) -> dt.datetime | None:
    end_value = _parse_utc(row.get("end_at_utc")) or _local_schedule_utc(
        row, use_end=True
    )
    if end_value is not None:
        return end_value
    start_value = _schedule_start_utc(row)
    return start_value + dt.timedelta(minutes=30) if start_value else None


def prepare_member_home_upcoming_schedules(
    rows: list[dict[str, Any]],
    *,
    now_utc: dt.datetime | None = None,
    limit: int = 5,
) -> list[dict[str, Any]]:
    """Hide ended Member Home cards and show the latest future slot first.

    This is presentation-only. It never changes schedule status, session_counted,
    package usage, notifications or stored schedule data.
    """

    now_value = now_utc or dt.datetime.now(dt.timezone.utc)
    if now_value.tzinfo is None:
        now_value = now_value.replace(tzinfo=dt.timezone.utc)
    now_value = now_value.astimezone(dt.timezone.utc)

    visible: list[dict[str, Any]] = []
    for raw in rows or []:
        row = dict(raw or {})
        status = _text(row.get("status") or "scheduled").lower()
        if status in _CLOSED_STATUSES:
            continue
        end_value = _schedule_end_utc(row)
        if end_value is not None and end_value <= now_value:
            continue
        visible.append(row)

    minimum = dt.datetime.min.replace(tzinfo=dt.timezone.utc)
    visible.sort(
        key=lambda row: (
            _schedule_start_utc(row) or minimum,
            _text(row.get("created_at")),
        ),
        reverse=True,
    )
    return visible[:limit] if limit else visible


def install_member_home_schedule_presentation() -> None:
    """Patch only the Member Home upcoming-schedule read presentation."""

    from components import db as db_api

    current = db_api.list_upcoming_member_schedules
    if getattr(current, _PATCH_MARKER, False):
        return

    @wraps(current)
    def latest_visible_member_home_schedules(member_id: object, limit: int = 3):
        rows = current(member_id, limit=0)
        return prepare_member_home_upcoming_schedules(rows, limit=limit)

    setattr(latest_visible_member_home_schedules, _PATCH_MARKER, True)
    latest_visible_member_home_schedules._hm_original = current
    db_api.list_upcoming_member_schedules = latest_visible_member_home_schedules
