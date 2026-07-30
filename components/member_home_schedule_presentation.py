from __future__ import annotations

import datetime as dt
from functools import wraps
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


_DEFAULT_MEMBER_TIMEZONE = "Asia/Kolkata"
_PATCH_MARKER = "_hm_member_home_schedule_presentation_v1"
_MARKDOWN_PATCH_MARKER = "_hm_member_home_compact_polish_v1"
_MEMBER_HOME_STYLE_MARKER = 'id="hm-member-home-local-style-v2"'
_CLOSED_STATUSES = {"cancelled", "completed", "rescheduled"}
_MEMBER_HOME_COMPACT_CSS = """
/* hm-member-home-compact-polish-v1 */
div[data-testid="stElementContainer"]:has(#hm-member-home-local-style-v2){
  display:none!important;height:0!important;min-height:0!important;
  margin:0!important;padding:0!important;overflow:hidden!important;
}
div[data-testid="stHorizontalBlock"]:has(.hm-member-identity-pill){
  position:relative!important;top:-2.75rem!important;
  margin-bottom:-2.25rem!important;
}
div[data-testid="stExpander"]:has(.hm-upcoming-schedule-anchor){
  border:0!important;background:transparent!important;box-shadow:none!important;
  margin:.20rem 0 .55rem 0!important;
}
div[data-testid="stExpander"]:has(.hm-upcoming-schedule-anchor) details{
  border:0!important;background:transparent!important;box-shadow:none!important;
}
div[data-testid="stExpander"]:has(.hm-upcoming-schedule-anchor) summary{
  width:max-content!important;max-width:100%!important;min-height:2.30rem!important;
  padding:.36rem .68rem!important;border:1px solid #E3C98E!important;
  border-radius:999px!important;background:#FFFDF8!important;
  box-shadow:0 4px 10px rgba(6,78,59,.06)!important;
  display:flex!important;align-items:center!important;gap:.42rem!important;
}
div[data-testid="stExpander"]:has(.hm-upcoming-schedule-anchor) summary,
div[data-testid="stExpander"]:has(.hm-upcoming-schedule-anchor) summary *{
  white-space:nowrap!important;overflow-wrap:normal!important;
  word-break:keep-all!important;line-height:1.10!important;
}
div[data-testid="stExpander"]:has(.hm-upcoming-schedule-anchor) summary p{
  margin:0!important;font-size:.90rem!important;font-weight:900!important;
}
div[data-testid="stExpander"]:has(.hm-upcoming-schedule-anchor) summary svg{
  width:.82rem!important;height:.82rem!important;min-width:.82rem!important;
  flex:0 0 .82rem!important;
}
@media(max-width:640px){
  div[data-testid="stHorizontalBlock"]:has(.hm-member-identity-pill){
    top:-1.75rem!important;margin-bottom:-1.30rem!important;
  }
}
"""


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


def _install_member_home_compact_polish() -> None:
    """Append Member Home-only CSS to the existing local style block."""

    import streamlit as st

    current_markdown = st.markdown
    if getattr(current_markdown, _MARKDOWN_PATCH_MARKER, False):
        return

    @wraps(current_markdown)
    def polished_markdown(body, *args, **kwargs):
        if (
            isinstance(body, str)
            and _MEMBER_HOME_STYLE_MARKER in body
            and "hm-member-home-compact-polish-v1" not in body
        ):
            body = body.replace(
                "</style>",
                f"{_MEMBER_HOME_COMPACT_CSS}</style>",
                1,
            )
        return current_markdown(body, *args, **kwargs)

    setattr(polished_markdown, _MARKDOWN_PATCH_MARKER, True)
    polished_markdown._hm_original_markdown = current_markdown
    st.markdown = polished_markdown


def install_member_home_schedule_presentation() -> None:
    """Install Member Home schedule filtering and presentation-only polish."""

    from components import db as db_api

    _install_member_home_compact_polish()

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
