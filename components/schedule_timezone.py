from __future__ import annotations

from datetime import date, datetime, time, timedelta, timezone
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
import uuid

import pytz

from components import db as db_api
from components.member_timezone import (
    DEFAULT_MEMBER_TIMEZONE,
    member_timezone_name,
)


DEFAULT_PRACTITIONER_TIMEZONE = DEFAULT_MEMBER_TIMEZONE
SCHEDULE_TIMEZONE_VERSION = "cross-timezone-v1"
UTC = timezone.utc
_CLOSED_STATUSES = {"cancelled", "completed", "rescheduled"}


def _text(value: object) -> str:
    return str(value or "").strip()


def _utc_now() -> datetime:
    return datetime.now(UTC)


def _now_iso() -> str:
    return _utc_now().isoformat(timespec="seconds").replace("+00:00", "Z")


def _valid_timezone_name(value: object, fallback: str = "") -> str:
    candidate = _text(value)
    if candidate:
        try:
            ZoneInfo(candidate)
            return candidate
        except (ZoneInfoNotFoundError, ValueError):
            pass
    return fallback


def timezone_options() -> list[str]:
    """Return stable IANA timezone choices with the HealthyMe default first."""
    values = sorted({str(value) for value in pytz.common_timezones})
    if DEFAULT_PRACTITIONER_TIMEZONE in values:
        values.remove(DEFAULT_PRACTITIONER_TIMEZONE)
    return [DEFAULT_PRACTITIONER_TIMEZONE] + values


def practitioner_timezone_name(user_id: object, persist: bool = True) -> str:
    """Resolve a practitioner/Admin IANA timezone without using IP or server locale."""
    user_key = _text(user_id) or "admin"
    db = db_api.load_db()
    stored = db.setdefault("user_timezones", {}).get(user_key, {}) or {}
    profile = db.setdefault("profiles", {}).get(user_key, {}) or {}
    user_row = next(
        (
            row
            for row in db.get("users", []) or []
            if _text(row.get("id")) == user_key
        ),
        {},
    )
    resolved = _valid_timezone_name(
        stored.get("timezone_name")
        or profile.get("timezone_name")
        or user_row.get("timezone_name"),
        DEFAULT_PRACTITIONER_TIMEZONE,
    )
    if persist and (
        stored.get("timezone_name") != resolved
        or stored.get("timezone_role") != "practitioner"
    ):
        db.setdefault("user_timezones", {})[user_key] = {
            **stored,
            "timezone_name": resolved,
            "timezone_role": "practitioner",
            "timezone_source": stored.get("timezone_source") or "healthyme_fallback",
            "updated_at": _now_iso(),
        }
        db_api.save_db(db)
    return resolved


def persist_practitioner_timezone(user_id: object, timezone_name: object) -> str:
    user_key = _text(user_id) or "admin"
    resolved = _valid_timezone_name(timezone_name)
    if not resolved:
        raise ValueError("Select a valid IANA timezone.")
    db = db_api.load_db()
    current = db.setdefault("user_timezones", {}).get(user_key, {}) or {}
    db["user_timezones"][user_key] = {
        **current,
        "timezone_name": resolved,
        "timezone_role": "practitioner",
        "timezone_source": "practitioner_selected",
        "updated_at": _now_iso(),
    }
    db_api.save_db(db)
    return resolved


def today_in_timezone(timezone_name: object) -> date:
    zone_name = _valid_timezone_name(timezone_name, DEFAULT_MEMBER_TIMEZONE)
    return datetime.now(ZoneInfo(zone_name)).date()


def _parse_date(value: object) -> date | None:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    text = _text(value)
    if not text:
        return None
    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%d-%m-%Y", "%d/%m/%Y"):
        try:
            return datetime.strptime(text[:10], fmt).date()
        except ValueError:
            pass
    try:
        return date.fromisoformat(text[:10])
    except ValueError:
        return None


def _parse_time(value: object) -> time | None:
    if isinstance(value, datetime):
        return value.time().replace(tzinfo=None)
    if isinstance(value, time):
        return value.replace(tzinfo=None)
    text = _text(value).upper()
    if not text:
        return None
    for fmt in ("%I:%M %p", "%H:%M", "%I %p", "%H"):
        try:
            return datetime.strptime(text, fmt).time()
        except ValueError:
            pass
    return None


def _parse_utc(value: object) -> datetime | None:
    text = _text(value)
    if not text:
        return None
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def _aware_local(local_date: date, local_time: time, timezone_name: str) -> tuple[datetime, str]:
    zone = ZoneInfo(timezone_name)
    naive = datetime.combine(local_date, local_time)
    first = naive.replace(tzinfo=zone, fold=0)
    round_trip = first.astimezone(UTC).astimezone(zone).replace(tzinfo=None)
    if round_trip != naive:
        raise ValueError(
            "The selected local time does not exist because of a daylight-saving clock change. "
            "Choose another time."
        )
    second = naive.replace(tzinfo=zone, fold=1)
    warning = ""
    if first.utcoffset() != second.utcoffset():
        warning = (
            "This local time occurs twice because of a daylight-saving clock change. "
            "HealthyMe will use the first occurrence."
        )
    return first, warning


def _format_offset(value: datetime) -> str:
    offset = value.utcoffset() or timedelta(0)
    minutes = int(offset.total_seconds() // 60)
    sign = "+" if minutes >= 0 else "-"
    minutes = abs(minutes)
    return f"UTC{sign}{minutes // 60:02d}:{minutes % 60:02d}"


def _format_date(value: datetime) -> str:
    return value.strftime("%d %b %Y")


def _format_time(value: datetime) -> str:
    return value.strftime("%I:%M %p")


def _local_view(start_utc: datetime, end_utc: datetime, timezone_name: str) -> dict[str, Any]:
    zone = ZoneInfo(timezone_name)
    start_local = start_utc.astimezone(zone)
    end_local = end_utc.astimezone(zone)
    same_date = start_local.date() == end_local.date()
    date_label = _format_date(start_local)
    if not same_date:
        date_label = f"{_format_date(start_local)} → {_format_date(end_local)}"
    return {
        "timezone_name": timezone_name,
        "offset": _format_offset(start_local),
        "date_iso": start_local.date().isoformat(),
        "end_date_iso": end_local.date().isoformat(),
        "date_label": date_label,
        "start_time": _format_time(start_local),
        "end_time": _format_time(end_local),
        "time_window": f"{_format_time(start_local)} – {_format_time(end_local)}",
        "start_iso": start_local.isoformat(timespec="seconds"),
        "end_iso": end_local.isoformat(timespec="seconds"),
    }


def _context_from_utc(
    start_utc: datetime,
    end_utc: datetime,
    *,
    source_timezone_name: str,
    member_timezone: str,
    practitioner_timezone: str,
    source_fold_warning: str = "",
    legacy_inferred: bool = False,
) -> dict[str, Any]:
    start_utc = start_utc.astimezone(UTC)
    end_utc = end_utc.astimezone(UTC)
    member_view = _local_view(start_utc, end_utc, member_timezone)
    practitioner_view = _local_view(start_utc, end_utc, practitioner_timezone)
    utc_view = _local_view(start_utc, end_utc, "UTC")
    return {
        "start_at_utc": start_utc.isoformat(timespec="seconds").replace("+00:00", "Z"),
        "end_at_utc": end_utc.isoformat(timespec="seconds").replace("+00:00", "Z"),
        "source_timezone_name": source_timezone_name,
        "member_timezone_name": member_timezone,
        "practitioner_timezone_name": practitioner_timezone,
        "member": member_view,
        "practitioner": practitioner_view,
        "utc": utc_view,
        "same_timezone": member_timezone == practitioner_timezone,
        "crosses_party_date_boundary": member_view["date_iso"] != practitioner_view["date_iso"],
        "dst_warning": source_fold_warning,
        "legacy_inferred": bool(legacy_inferred),
    }


def build_dual_time_context(
    local_date: object,
    start_time: object,
    end_time: object,
    *,
    source_timezone_name: object,
    member_timezone: object,
    practitioner_timezone: object,
) -> dict[str, Any]:
    """Convert a source-local appointment window into canonical UTC and both local views."""
    parsed_date = _parse_date(local_date)
    parsed_start = _parse_time(start_time)
    parsed_end = _parse_time(end_time)
    source_tz = _valid_timezone_name(source_timezone_name)
    member_tz = _valid_timezone_name(member_timezone, DEFAULT_MEMBER_TIMEZONE)
    practitioner_tz = _valid_timezone_name(
        practitioner_timezone, DEFAULT_PRACTITIONER_TIMEZONE
    )
    if not parsed_date or not parsed_start or not parsed_end:
        raise ValueError("Date, start time and end time are required.")
    if not source_tz:
        raise ValueError("Select the timezone in which the date and time are being entered.")
    if parsed_end <= parsed_start:
        raise ValueError("End time must be after start time on the selected date.")

    aware_start, warning_start = _aware_local(parsed_date, parsed_start, source_tz)
    aware_end, warning_end = _aware_local(parsed_date, parsed_end, source_tz)
    start_utc = aware_start.astimezone(UTC)
    end_utc = aware_end.astimezone(UTC)
    if end_utc <= start_utc:
        raise ValueError("End time must be after start time.")
    warning = warning_start or warning_end
    return _context_from_utc(
        start_utc,
        end_utc,
        source_timezone_name=source_tz,
        member_timezone=member_tz,
        practitioner_timezone=practitioner_tz,
        source_fold_warning=warning,
    )


def _member_tokens(db: dict[str, Any], member_id: object) -> set[str]:
    raw = _text(member_id)
    tokens = {raw, raw.lower()} if raw else set()
    for user in db.get("users", []) or []:
        uid = _text(user.get("id"))
        email = _text(user.get("email")).lower()
        if raw and (raw == uid or raw.lower() == email):
            if uid:
                tokens.add(uid)
            if email:
                tokens.add(email)
    return {value for value in tokens if value}


def _schedule_matches_member(db: dict[str, Any], row: dict[str, Any], member_id: object) -> bool:
    tokens = _member_tokens(db, member_id)
    values = {
        _text(row.get("member_id")),
        _text(row.get("member_id")).lower(),
        _text(row.get("member_email")).lower(),
    }
    return bool(tokens.intersection({value for value in values if value}))


def schedule_time_context(
    row: dict[str, Any],
    *,
    member_id: object = "",
    practitioner_id: object = "",
) -> dict[str, Any]:
    member_key = _text(member_id) or _text(row.get("member_id"))
    practitioner_key = _text(practitioner_id) or _text(row.get("created_by")) or "admin"
    member_tz = _valid_timezone_name(
        row.get("member_timezone_name"),
        member_timezone_name(member_key, persist=True),
    )
    practitioner_tz = _valid_timezone_name(
        row.get("practitioner_timezone_name"),
        practitioner_timezone_name(practitioner_key, persist=True),
    )
    source_tz = _valid_timezone_name(
        row.get("source_timezone_name"),
        member_tz,
    )
    start_utc = _parse_utc(row.get("start_at_utc"))
    end_utc = _parse_utc(row.get("end_at_utc"))
    legacy_inferred = False

    if not start_utc:
        parsed_date = _parse_date(row.get("schedule_date"))
        parsed_start = _parse_time(row.get("start_time"))
        if not parsed_date or not parsed_start:
            return {}
        legacy_inferred = True
        source_tz = member_tz
        aware_start, _warning = _aware_local(parsed_date, parsed_start, source_tz)
        start_utc = aware_start.astimezone(UTC)

    if not end_utc:
        parsed_date = _parse_date(row.get("schedule_date"))
        parsed_end = _parse_time(row.get("end_time"))
        if parsed_date and parsed_end:
            aware_end, _warning = _aware_local(parsed_date, parsed_end, source_tz)
            end_utc = aware_end.astimezone(UTC)
        if not end_utc or end_utc <= start_utc:
            end_utc = start_utc + timedelta(minutes=30)

    return _context_from_utc(
        start_utc,
        end_utc,
        source_timezone_name=source_tz,
        member_timezone=member_tz,
        practitioner_timezone=practitioner_tz,
        legacy_inferred=legacy_inferred,
    )


def dual_time_text(context: dict[str, Any]) -> str:
    if not context:
        return ""
    member = context["member"]
    practitioner = context["practitioner"]
    if context.get("same_timezone"):
        return (
            f"{member['date_label']} · {member['time_window']} "
            f"({member['timezone_name']}, {member['offset']})"
        )
    return (
        f"Member: {member['date_label']} · {member['time_window']} "
        f"({member['timezone_name']}, {member['offset']}); "
        f"Practitioner: {practitioner['date_label']} · {practitioner['time_window']} "
        f"({practitioner['timezone_name']}, {practitioner['offset']})"
    )


def _apply_context_to_schedule(
    row: dict[str, Any],
    context: dict[str, Any],
    *,
    actor_id: object,
) -> None:
    member = context["member"]
    practitioner = context["practitioner"]
    row.update(
        {
            "schedule_date": member["date_iso"],
            "start_time": member["start_time"],
            "end_time": member["end_time"],
            "start_at_utc": context["start_at_utc"],
            "end_at_utc": context["end_at_utc"],
            "source_timezone_name": context["source_timezone_name"],
            "member_timezone_name": context["member_timezone_name"],
            "practitioner_timezone_name": context["practitioner_timezone_name"],
            "member_local_date": member["date_iso"],
            "member_local_start_time": member["start_time"],
            "member_local_end_time": member["end_time"],
            "practitioner_local_date": practitioner["date_iso"],
            "practitioner_local_start_time": practitioner["start_time"],
            "practitioner_local_end_time": practitioner["end_time"],
            "timezone_version": SCHEDULE_TIMEZONE_VERSION,
            "timezone_updated_at": _now_iso(),
            "timezone_updated_by": _text(actor_id) or "system",
        }
    )


def _append_timezone_audit(
    db: dict[str, Any],
    *,
    event: str,
    schedule_id: object,
    member_id: object,
    actor_id: object,
    context: dict[str, Any],
    reschedule_request_id: object = "",
) -> None:
    db.setdefault("schedule_timezone_audit", []).append(
        {
            "id": str(uuid.uuid4())[:8],
            "ts": _now_iso(),
            "event": event,
            "schedule_id": _text(schedule_id),
            "reschedule_request_id": _text(reschedule_request_id),
            "member_id": _text(member_id),
            "actor_id": _text(actor_id) or "system",
            "start_at_utc": context.get("start_at_utc", ""),
            "end_at_utc": context.get("end_at_utc", ""),
            "source_timezone_name": context.get("source_timezone_name", ""),
            "member_timezone_name": context.get("member_timezone_name", ""),
            "practitioner_timezone_name": context.get(
                "practitioner_timezone_name", ""
            ),
            "member_local": context.get("member", {}),
            "practitioner_local": context.get("practitioner", {}),
            "timezone_version": SCHEDULE_TIMEZONE_VERSION,
        }
    )


def _rewrite_schedule_notifications(
    db: dict[str, Any],
    schedule: dict[str, Any],
    context: dict[str, Any],
) -> None:
    schedule_id = schedule.get("id")
    title = schedule.get("title") or "Scheduled session"
    message = f"{title} is scheduled. {dual_time_text(context)}."
    if schedule.get("mode"):
        message += f" Mode: {schedule.get('mode')}."
    if schedule.get("location_or_link"):
        message += f" Link/location: {schedule.get('location_or_link')}."
    if schedule.get("notes"):
        message += f" Note: {schedule.get('notes')}"
    for row in db.get("messages", []) or []:
        if row.get("schedule_id") == schedule_id and row.get("source") == "schedule":
            row["message"] = message
            row["timezone_version"] = SCHEDULE_TIMEZONE_VERSION
    for row in db.get("notifications", []) or []:
        if row.get("schedule_id") == schedule_id and row.get("kind") == "schedule_created":
            row["message"] = f"Schedule: {title}: {message[:300]}"
            row["timezone_version"] = SCHEDULE_TIMEZONE_VERSION


def create_timezone_aware_member_schedule(
    *,
    member_id: object,
    title: object,
    schedule_type: object,
    local_date: object,
    start_time: object,
    end_time: object,
    source_timezone_name: object,
    practitioner_id: object,
    mode: object = "",
    location_or_link: object = "",
    notes: object = "",
    session_cost: object = None,
) -> dict[str, Any]:
    practitioner_id_text = _text(practitioner_id) or "admin"
    member_tz = member_timezone_name(member_id, persist=True)
    practitioner_tz = practitioner_timezone_name(practitioner_id_text, persist=True)
    context = build_dual_time_context(
        local_date,
        start_time,
        end_time,
        source_timezone_name=source_timezone_name,
        member_timezone=member_tz,
        practitioner_timezone=practitioner_tz,
    )
    member_view = context["member"]
    created = db_api.create_member_schedule(
        member_id=_text(member_id),
        title=_text(title),
        schedule_type=_text(schedule_type),
        schedule_date=member_view["date_iso"],
        start_time=member_view["start_time"],
        end_time=member_view["end_time"],
        mode=_text(mode),
        location_or_link=_text(location_or_link),
        notes=_text(notes),
        actor_id=practitioner_id_text,
        session_cost=session_cost,
    )
    if not created or created.get("error"):
        return created or {"error": "Schedule could not be created."}

    db = db_api.load_db()
    schedule_row = next(
        (row for row in db.get("schedules", []) if row.get("id") == created.get("id")),
        None,
    )
    if not schedule_row:
        return {"error": "Schedule was created but its stored row could not be reloaded."}
    _apply_context_to_schedule(schedule_row, context, actor_id=practitioner_id_text)
    _rewrite_schedule_notifications(db, schedule_row, context)
    _append_timezone_audit(
        db,
        event="schedule_created",
        schedule_id=schedule_row.get("id"),
        member_id=member_id,
        actor_id=practitioner_id_text,
        context=context,
    )
    db_api.save_db(db)
    output = dict(schedule_row)
    output["_time_context"] = context
    return output


def timezone_enriched_schedule_rows(
    member_id: object,
    *,
    include_cancelled: bool = True,
    limit: int = 50,
) -> list[dict[str, Any]]:
    rows = db_api.list_member_schedules(
        member_id=_text(member_id),
        include_cancelled=include_cancelled,
        limit=0,
    )
    output = []
    for row in rows:
        enriched = dict(row)
        enriched["_time_context"] = schedule_time_context(
            enriched, member_id=member_id
        )
        output.append(enriched)
    output.sort(
        key=lambda row: (
            _parse_utc((row.get("_time_context") or {}).get("start_at_utc"))
            or datetime.max.replace(tzinfo=UTC),
            _text(row.get("created_at")),
        )
    )
    return output[:limit] if limit else output


def _schedule_is_upcoming(row: dict[str, Any]) -> bool:
    status = _text(row.get("status") or "scheduled").lower()
    if status in _CLOSED_STATUSES:
        return False
    context = row.get("_time_context") or schedule_time_context(row)
    end_utc = _parse_utc(context.get("end_at_utc")) if context else None
    start_utc = _parse_utc(context.get("start_at_utc")) if context else None
    if end_utc:
        return end_utc >= _utc_now()
    if start_utc:
        return start_utc + timedelta(hours=2) >= _utc_now()
    return True


def list_timezone_aware_member_schedules(
    member_id: object, limit: int = 30
) -> list[dict[str, Any]]:
    db = db_api.load_db()
    rows = []
    for source in db.get("schedules", []) or []:
        if not _schedule_matches_member(db, source, member_id):
            continue
        row = dict(source)
        row["_time_context"] = schedule_time_context(row, member_id=member_id)
        if _schedule_is_upcoming(row):
            rows.append(row)
    rows.sort(
        key=lambda row: (
            _parse_utc((row.get("_time_context") or {}).get("start_at_utc"))
            or datetime.max.replace(tzinfo=UTC),
            _text(row.get("created_at")),
        )
    )
    return rows[:limit] if limit else rows


def list_timezone_aware_admin_open_schedules(
    member_id: object, limit: int = 0
) -> list[dict[str, Any]]:
    rows = [
        row
        for row in timezone_enriched_schedule_rows(
            member_id, include_cancelled=True, limit=0
        )
        if _text(row.get("status") or "scheduled").lower()
        in {"scheduled", "acknowledged"}
        and _schedule_is_upcoming(row)
    ]
    return rows[:limit] if limit else rows


def schedule_within_hours(row: dict[str, Any], hours: int) -> bool:
    context = row.get("_time_context") or schedule_time_context(row)
    start_utc = _parse_utc(context.get("start_at_utc")) if context else None
    if not start_utc:
        return False
    delta = start_utc - _utc_now()
    return timedelta(0) <= delta <= timedelta(hours=hours)


def queue_timezone_aware_schedule_acknowledgement_reminders(
    member_id: object, actor_id: object = "system"
) -> list[dict[str, Any]]:
    db = db_api.load_db()
    queued = []
    rows_by_id = {row.get("id"): row for row in db.get("schedules", []) or []}
    for enriched in list_timezone_aware_member_schedules(member_id, limit=0):
        if _text(enriched.get("status") or "scheduled").lower() != "scheduled":
            continue
        if _text(enriched.get("reschedule_request_status")).lower() == "pending":
            continue
        if enriched.get("ack_reminder_48h_sent_at"):
            continue
        if not schedule_within_hours(enriched, 48):
            continue
        context = enriched.get("_time_context") or {}
        title = enriched.get("title") or "Scheduled session"
        notice = (
            "Please acknowledge this scheduled session or submit a reschedule request as soon as possible. "
            "Reschedule requests raised within 24 hours may not be accepted and may use an additional meeting count."
        )
        message = f"Reminder: {title}. {dual_time_text(context)}. {notice}"
        schedule_id = enriched.get("id")
        stored = rows_by_id.get(schedule_id)
        if not stored:
            continue
        member_email = _text(enriched.get("member_email"))
        db.setdefault("messages", []).append(
            {
                "id": str(uuid.uuid4())[:8],
                "ts": _now_iso(),
                "member_id": _text(member_id),
                "sender_role": "admin",
                "actor_id": _text(actor_id) or "system",
                "subject": "Action required: Scheduled session acknowledgement",
                "message": message,
                "status": "queued",
                "email_required": True,
                "source": "schedule_48h_acknowledgement_reminder",
                "schedule_id": schedule_id,
                "timezone_version": SCHEDULE_TIMEZONE_VERSION,
            }
        )
        db.setdefault("notifications", []).append(
            {
                "ts": _now_iso(),
                "kind": "schedule_48h_acknowledgement_reminder",
                "user_id": _text(member_id),
                "member_id": _text(member_id),
                "message": message,
                "status": "queued",
                "email_required": True,
                "email_to": member_email,
                "created_by": _text(actor_id) or "system",
                "schedule_id": schedule_id,
                "timezone_version": SCHEDULE_TIMEZONE_VERSION,
            }
        )
        stored["ack_reminder_48h_sent_at"] = _now_iso()
        stored["updated_at"] = _now_iso()
        stored["updated_by"] = _text(actor_id) or "system"
        queued.append(dict(stored))
    if queued:
        db_api.save_db(db)
    return queued


def request_timezone_aware_reschedule(
    *,
    schedule_id: object,
    member_id: object,
    requested_date: object,
    requested_start_time: object,
    requested_end_time: object,
    reason: object = "",
) -> dict[str, Any]:
    db = db_api.load_db()
    db.setdefault("reschedule_requests", [])
    schedule = next(
        (
            row
            for row in db.get("schedules", []) or []
            if row.get("id") == _text(schedule_id)
            and _schedule_matches_member(db, row, member_id)
        ),
        None,
    )
    if not schedule:
        return {"error": "The selected schedule could not be found."}
    for existing in db.get("reschedule_requests", []) or []:
        if (
            existing.get("schedule_id") == _text(schedule_id)
            and existing.get("status") == "pending"
        ):
            return dict(existing)

    current_context = schedule_time_context(schedule, member_id=member_id)
    member_tz = current_context.get("member_timezone_name") or member_timezone_name(
        member_id, persist=True
    )
    practitioner_tz = current_context.get(
        "practitioner_timezone_name"
    ) or practitioner_timezone_name(schedule.get("created_by") or "admin", persist=True)
    requested_context = build_dual_time_context(
        requested_date,
        requested_start_time,
        requested_end_time,
        source_timezone_name=member_tz,
        member_timezone=member_tz,
        practitioner_timezone=practitioner_tz,
    )
    requested_start_utc = _parse_utc(requested_context["start_at_utc"])
    if not requested_start_utc or requested_start_utc <= _utc_now():
        return {"error": "Choose a future member-local date and time."}

    within_24 = schedule_within_hours({**schedule, "_time_context": current_context}, 24)
    request_id = str(uuid.uuid4())[:8]
    member_view = requested_context["member"]
    request_row = {
        "id": request_id,
        "schedule_id": _text(schedule_id),
        "member_id": _text(member_id),
        "member_name": schedule.get("member_name", ""),
        "member_email": schedule.get("member_email", ""),
        "current_title": schedule.get("title", ""),
        "current_date": (current_context.get("member") or {}).get("date_iso", schedule.get("schedule_date", "")),
        "current_start_time": (current_context.get("member") or {}).get("start_time", schedule.get("start_time", "")),
        "current_end_time": (current_context.get("member") or {}).get("end_time", schedule.get("end_time", "")),
        "current_start_at_utc": current_context.get("start_at_utc", ""),
        "current_end_at_utc": current_context.get("end_at_utc", ""),
        "requested_date": member_view["date_iso"],
        "requested_start_time": member_view["start_time"],
        "requested_end_time": member_view["end_time"],
        "requested_start_at_utc": requested_context["start_at_utc"],
        "requested_end_at_utc": requested_context["end_at_utc"],
        "member_timezone_name": member_tz,
        "practitioner_timezone_name": practitioner_tz,
        "source_timezone_name": member_tz,
        "reason": _text(reason),
        "within_24_hours": bool(within_24),
        "prior_session_counted_if_approved": bool(within_24),
        "status": "pending",
        "created_at": _now_iso(),
        "updated_at": _now_iso(),
        "timezone_version": SCHEDULE_TIMEZONE_VERSION,
    }
    db["reschedule_requests"].append(request_row)
    schedule["reschedule_request_status"] = "pending"
    schedule["latest_reschedule_request_id"] = request_id
    schedule["updated_at"] = _now_iso()
    schedule["updated_by"] = _text(member_id)

    message = (
        f"Reschedule requested for {schedule.get('title') or 'Scheduled session'}. "
        f"Current: {dual_time_text(current_context)}. Requested: {dual_time_text(requested_context)}."
    )
    if within_24:
        message += " This request is within 24 hours; the prior session may be counted as consumed."
    db.setdefault("notifications", []).append(
        {
            "ts": _now_iso(),
            "kind": "reschedule_requested",
            "user_id": "admin",
            "member_id": _text(member_id),
            "message": message,
            "status": "queued",
            "email_required": False,
            "schedule_id": _text(schedule_id),
            "reschedule_request_id": request_id,
            "timezone_version": SCHEDULE_TIMEZONE_VERSION,
        }
    )
    _append_timezone_audit(
        db,
        event="reschedule_requested",
        schedule_id=schedule_id,
        member_id=member_id,
        actor_id=member_id,
        context=requested_context,
        reschedule_request_id=request_id,
    )
    db_api.save_db(db)
    output = dict(request_row)
    output["_current_time_context"] = current_context
    output["_requested_time_context"] = requested_context
    return output


def _request_context(req: dict[str, Any]) -> dict[str, Any]:
    start_utc = _parse_utc(req.get("requested_start_at_utc"))
    end_utc = _parse_utc(req.get("requested_end_at_utc"))
    member_tz = _valid_timezone_name(
        req.get("member_timezone_name"), DEFAULT_MEMBER_TIMEZONE
    )
    practitioner_tz = _valid_timezone_name(
        req.get("practitioner_timezone_name"), DEFAULT_PRACTITIONER_TIMEZONE
    )
    if start_utc:
        if not end_utc or end_utc <= start_utc:
            end_utc = start_utc + timedelta(minutes=30)
        return _context_from_utc(
            start_utc,
            end_utc,
            source_timezone_name=_valid_timezone_name(
                req.get("source_timezone_name"), member_tz
            ),
            member_timezone=member_tz,
            practitioner_timezone=practitioner_tz,
        )
    parsed_date = _parse_date(req.get("requested_date"))
    parsed_start = _parse_time(req.get("requested_start_time"))
    parsed_end = _parse_time(req.get("requested_end_time"))
    if not parsed_date or not parsed_start:
        raise ValueError("Requested schedule date/time is incomplete.")
    if not parsed_end or parsed_end <= parsed_start:
        parsed_end = (
            datetime.combine(parsed_date, parsed_start) + timedelta(minutes=30)
        ).time()
    return build_dual_time_context(
        parsed_date,
        parsed_start,
        parsed_end,
        source_timezone_name=member_tz,
        member_timezone=member_tz,
        practitioner_timezone=practitioner_tz,
    )


def list_timezone_aware_reschedule_requests(
    *,
    member_id: object = "",
    status: object = None,
    limit: int = 100,
) -> list[dict[str, Any]]:
    rows = db_api.list_reschedule_requests(
        member_id=_text(member_id) or None,
        status=status,
        limit=0,
    )
    db = db_api.load_db()
    schedules = {row.get("id"): row for row in db.get("schedules", []) or []}
    output = []
    for source in rows:
        row = dict(source)
        schedule = schedules.get(row.get("schedule_id"), {})
        row["_current_time_context"] = schedule_time_context(
            schedule, member_id=row.get("member_id")
        ) if schedule else {}
        try:
            row["_requested_time_context"] = _request_context(row)
        except ValueError:
            row["_requested_time_context"] = {}
        requested_start = _parse_utc(
            (row.get("_requested_time_context") or {}).get("start_at_utc")
        )
        row["_requested_in_past"] = bool(
            requested_start and requested_start <= _utc_now()
        )
        output.append(row)
    output.sort(key=lambda row: _text(row.get("created_at")), reverse=True)
    return output[:limit] if limit else output


def decide_timezone_aware_reschedule_request(
    request_id: object,
    decision: object,
    *,
    admin_note: object = "",
    actor_id: object = "admin",
) -> dict[str, Any]:
    db = db_api.load_db()
    db.setdefault("reschedule_requests", [])
    req = next(
        (row for row in db["reschedule_requests"] if row.get("id") == _text(request_id)),
        None,
    )
    if not req:
        return {"error": "The reschedule request could not be found."}
    if req.get("status") != "pending":
        return {"error": "This reschedule request is already closed."}
    schedule = next(
        (row for row in db.get("schedules", []) or [] if row.get("id") == req.get("schedule_id")),
        None,
    )
    normalized_decision = "approved" if _text(decision).lower() == "approved" else "rejected"
    req["status"] = normalized_decision
    req["admin_note"] = _text(admin_note)
    req["updated_at"] = _now_iso()
    req["decided_at"] = _now_iso()
    req["decided_by"] = _text(actor_id) or "admin"
    new_schedule = None
    requested_context = _request_context(req)

    if normalized_decision == "approved":
        requested_start = _parse_utc(requested_context.get("start_at_utc"))
        if not requested_start or requested_start <= _utc_now():
            req["status"] = "pending"
            req["decision_error"] = "Requested reschedule time must be in the future."
            db_api.save_db(db)
            return {"error": req["decision_error"], "request": dict(req)}
        if not schedule:
            req["status"] = "pending"
            req["decision_error"] = "Original schedule could not be found."
            db_api.save_db(db)
            return {"error": req["decision_error"], "request": dict(req)}

        schedule["status"] = "rescheduled"
        schedule["reschedule_request_status"] = "approved"
        schedule["rescheduled_at"] = _now_iso()
        schedule["updated_at"] = _now_iso()
        schedule["updated_by"] = _text(actor_id) or "admin"
        schedule["session_counted"] = bool(req.get("within_24_hours"))

        new_schedule = dict(schedule)
        new_schedule.update(
            {
                "id": str(uuid.uuid4())[:8],
                "status": "scheduled",
                "created_at": _now_iso(),
                "created_by": _text(actor_id) or "admin",
                "updated_at": _now_iso(),
                "updated_by": _text(actor_id) or "admin",
                "acknowledged_at": "",
                "completed_at": "",
                "cancelled_at": "",
                "rescheduled_from_schedule_id": schedule.get("id"),
                "reschedule_request_id": _text(request_id),
                "reschedule_request_status": "",
                "latest_reschedule_request_id": "",
                "session_counted": False,
                "ack_reminder_48h_sent_at": "",
            }
        )
        _apply_context_to_schedule(
            new_schedule, requested_context, actor_id=actor_id
        )
        db.setdefault("schedules", []).append(new_schedule)
        req["new_schedule_id"] = new_schedule["id"]
        title = schedule.get("title") or "Scheduled session"
        member_message = (
            f"Your reschedule request for {title} has been approved. "
            f"{dual_time_text(requested_context)}."
        )
        if req.get("within_24_hours"):
            member_message += (
                " This request was within 24 hours; the previous session may be counted as consumed."
            )
        _append_timezone_audit(
            db,
            event="reschedule_approved",
            schedule_id=new_schedule["id"],
            member_id=req.get("member_id"),
            actor_id=actor_id,
            context=requested_context,
            reschedule_request_id=request_id,
        )
    else:
        if schedule:
            schedule["reschedule_request_status"] = "rejected"
            schedule["updated_at"] = _now_iso()
            schedule["updated_by"] = _text(actor_id) or "admin"
        member_message = (
            f"Your reschedule request for {req.get('current_title') or 'scheduled session'} was not approved."
        )
        if _text(admin_note):
            member_message += f" Note: {_text(admin_note)}"

    db.setdefault("messages", []).append(
        {
            "id": str(uuid.uuid4())[:8],
            "ts": _now_iso(),
            "member_id": req.get("member_id"),
            "sender_role": "admin",
            "actor_id": _text(actor_id) or "admin",
            "subject": "Reschedule request update",
            "message": member_message,
            "status": "queued",
            "email_required": True,
            "source": "reschedule",
            "schedule_id": req.get("schedule_id"),
            "reschedule_request_id": _text(request_id),
            "timezone_version": SCHEDULE_TIMEZONE_VERSION,
        }
    )
    db.setdefault("notifications", []).append(
        {
            "ts": _now_iso(),
            "kind": f"reschedule_{normalized_decision}",
            "user_id": req.get("member_id"),
            "member_id": req.get("member_id"),
            "message": member_message,
            "status": "queued",
            "email_required": True,
            "email_to": req.get("member_email", ""),
            "created_by": _text(actor_id) or "admin",
            "schedule_id": req.get("schedule_id"),
            "reschedule_request_id": _text(request_id),
            "timezone_version": SCHEDULE_TIMEZONE_VERSION,
        }
    )
    db_api.save_db(db)
    return {
        "request": dict(req),
        "new_schedule": dict(new_schedule) if new_schedule else None,
    }


def context_start_is_future(context: dict[str, Any]) -> bool:
    start_utc = _parse_utc((context or {}).get("start_at_utc"))
    return bool(start_utc and start_utc > _utc_now())
