"""H14H normalized schedule row helpers.

The database connection remains in storage_backend.py. This module only converts
legacy Streamlit schedule dictionaries into the shared normalized table shape.
"""

from __future__ import annotations

import hashlib
from typing import Any, Dict


def _text(value: Any) -> str:
    return "" if value is None else str(value).strip()


def _integer(value: Any, fallback: int = 0) -> int:
    try:
        return int(value)
    except Exception:
        return fallback


def _number(value: Any, fallback: float = 0.0) -> float:
    try:
        return float(value)
    except Exception:
        return fallback


def _boolean(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return _text(value).lower() in {"true", "1", "yes"}


def _stable_id(prefix: str, *parts: Any) -> str:
    raw = "|".join(_text(part).lower() for part in parts)
    return f"{prefix}_{hashlib.sha1(raw.encode('utf-8')).hexdigest()[:20]}"


def package_row(raw: Dict[str, Any]) -> Dict[str, Any]:
    raw = dict(raw or {})
    inclusions = raw.get("inclusions")
    if not isinstance(inclusions, (dict, list)):
        inclusions = {}
    return {
        "id": _text(raw.get("id")) or _stable_id("pkg", raw.get("member_id"), raw.get("member_email"), raw.get("package_name") or raw.get("name"), raw.get("subscribed_at")),
        "member_id": _text(raw.get("member_id")),
        "member_email": _text(raw.get("member_email")).lower(),
        "member_name": _text(raw.get("member_name")),
        "package_id": _text(raw.get("package_id")),
        "package_name": _text(raw.get("package_name") or raw.get("name")),
        "session_count": _integer(raw.get("session_count")),
        "cost_per_session": _number(raw.get("cost_per_session")),
        "currency": _text(raw.get("currency")) or "INR",
        "number_of_people": max(1, _integer(raw.get("number_of_people"), 1)),
        "inclusions": inclusions,
        "status": _text(raw.get("status")) or "Active",
        "subscribed_at": _text(raw.get("subscribed_at")),
        "created_at": _text(raw.get("created_at")),
        "updated_at": _text(raw.get("updated_at")),
    }


def schedule_row(raw: Dict[str, Any]) -> Dict[str, Any]:
    raw = dict(raw or {})
    return {
        "id": _text(raw.get("id")) or _stable_id("sch", raw.get("member_id"), raw.get("member_email"), raw.get("schedule_date"), raw.get("start_time"), raw.get("title")),
        "member_id": _text(raw.get("member_id")),
        "member_email": _text(raw.get("member_email")).lower(),
        "member_name": _text(raw.get("member_name")),
        "title": _text(raw.get("title")),
        "schedule_type": _text(raw.get("schedule_type")),
        "schedule_date": _text(raw.get("schedule_date"))[:10],
        "start_time": _text(raw.get("start_time")),
        "end_time": _text(raw.get("end_time")),
        "mode": _text(raw.get("mode")),
        "location_or_link": _text(raw.get("location_or_link")),
        "notes": _text(raw.get("notes")),
        "session_cost": _number(raw.get("session_cost")),
        "package_id": _text(raw.get("package_id")),
        "member_package_id": _text(raw.get("member_package_id")),
        "status": _text(raw.get("status")).lower() or "scheduled",
        "acknowledged_at": _text(raw.get("acknowledged_at")),
        "completed_at": _text(raw.get("completed_at")),
        "cancelled_at": _text(raw.get("cancelled_at")),
        "rescheduled_at": _text(raw.get("rescheduled_at")),
        "rescheduled_from_schedule_id": _text(raw.get("rescheduled_from_schedule_id")),
        "reschedule_request_id": _text(raw.get("reschedule_request_id")),
        "reschedule_request_status": _text(raw.get("reschedule_request_status")),
        "latest_reschedule_request_id": _text(raw.get("latest_reschedule_request_id")),
        "session_counted": _boolean(raw.get("session_counted")),
        "ack_reminder_48h_sent_at": _text(raw.get("ack_reminder_48h_sent_at")),
        "created_at": _text(raw.get("created_at")),
        "created_by": _text(raw.get("created_by")),
        "updated_at": _text(raw.get("updated_at")),
        "updated_by": _text(raw.get("updated_by")),
    }


def request_row(raw: Dict[str, Any]) -> Dict[str, Any]:
    raw = dict(raw or {})
    return {
        "id": _text(raw.get("id")) or _stable_id("req", raw.get("schedule_id"), raw.get("requested_date"), raw.get("requested_start_time")),
        "schedule_id": _text(raw.get("schedule_id")),
        "member_id": _text(raw.get("member_id")),
        "member_email": _text(raw.get("member_email")).lower(),
        "member_name": _text(raw.get("member_name")),
        "current_title": _text(raw.get("current_title")),
        "current_date": _text(raw.get("current_date"))[:10],
        "current_start_time": _text(raw.get("current_start_time")),
        "current_end_time": _text(raw.get("current_end_time")),
        "requested_date": _text(raw.get("requested_date"))[:10],
        "requested_start_time": _text(raw.get("requested_start_time")),
        "requested_end_time": _text(raw.get("requested_end_time")),
        "reason": _text(raw.get("reason")),
        "within_24_hours": _boolean(raw.get("within_24_hours")),
        "late_reschedule_request": _boolean(raw.get("late_reschedule_request")),
        "prior_session_counted_if_approved": _boolean(raw.get("prior_session_counted_if_approved")),
        "status": _text(raw.get("status")).lower() or "pending",
        "admin_note": _text(raw.get("admin_note")),
        "new_schedule_id": _text(raw.get("new_schedule_id")),
        "decision_error": _text(raw.get("decision_error")),
        "created_at": _text(raw.get("created_at")),
        "updated_at": _text(raw.get("updated_at")),
        "decided_at": _text(raw.get("decided_at")),
        "decided_by": _text(raw.get("decided_by")),
    }
