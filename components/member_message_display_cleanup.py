from __future__ import annotations

from typing import Any


# Scheduling already has a dedicated Upcoming Schedule area on Member Home.
# Keeping the same events in the generic message feed repeats the same action and
# makes genuine Nutritionist guidance harder to find. The records remain stored,
# auditable and eligible for email delivery; this wrapper changes display only.
_MEMBER_HOME_DUPLICATED_SCHEDULE_SOURCES = {
    "schedule",
    "schedule_48h_acknowledgement_reminder",
}


def _text(value: Any) -> str:
    return str(value or "").strip()


def _display_key(row: dict[str, Any]) -> str:
    source = _text(row.get("source")).lower()
    schedule_id = _text(row.get("schedule_id")).lower()
    request_id = _text(row.get("reschedule_request_id")).lower()
    note_id = _text(row.get("note_id")).lower()
    subject = " ".join(_text(row.get("subject")).split()).lower()
    message = " ".join(_text(row.get("message")).split()).lower()
    return "|".join((source, schedule_id, request_id, note_id, subject, message))


def member_home_visible_messages(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Return one actionable Member Home card per non-schedule message event."""

    visible: list[dict[str, Any]] = []
    seen: set[str] = set()
    for source_row in rows or []:
        row = dict(source_row or {})
        if _text(row.get("source")).lower() in _MEMBER_HOME_DUPLICATED_SCHEDULE_SOURCES:
            continue
        key = _display_key(row)
        if key in seen:
            continue
        seen.add(key)
        visible.append(row)
    return visible


def install_member_message_display_cleanup() -> None:
    """Filter only the normal unread Member Home feed; preserve stored history."""

    from components import db as db_api

    current = db_api.get_member_messages
    if getattr(current, "_hm_member_message_display_cleanup", False):
        return

    base = getattr(db_api, "_hm_member_message_display_cleanup_base", current)
    db_api._hm_member_message_display_cleanup_base = base

    def get_member_messages_without_schedule_repetition(member_id, limit=10):
        # Fetch extra rows first because schedule messages are removed after loading.
        resolved_limit = int(limit or 10)
        fetch_limit = max(resolved_limit * 4, 40)
        rows = base(member_id, limit=fetch_limit)
        return member_home_visible_messages(list(rows or []))[:resolved_limit]

    get_member_messages_without_schedule_repetition._hm_member_message_display_cleanup = True
    db_api.get_member_messages = get_member_messages_without_schedule_repetition
