from __future__ import annotations

import datetime as dt
from typing import Any


INCLUSIONS_RULE = (
    "Package inclusions are informational only and do not grant, hide, block or "
    "enforce access to HealthyMe modules."
)
COMMERCIAL_SNAPSHOT_NOTE = (
    "Package Library changes apply to future subscriptions only. Existing member "
    "subscriptions retain their saved commercial snapshot."
)
CURRENT_STATUSES = {"active", "paused"}
CONSUMED_STATUSES = {"completed"}


def _text(value: object) -> str:
    return str(value or "").strip()


def _number(value: object, default: float = 0.0) -> float:
    try:
        return float(value if value not in (None, "") else default)
    except Exception:
        return float(default)


def _integer(value: object, default: int = 0) -> int:
    try:
        return int(value if value not in (None, "") else default)
    except Exception:
        return int(default)


def _date_text(value: object) -> str | None:
    if value in (None, ""):
        return None
    if isinstance(value, (dt.date, dt.datetime)):
        return value.date().isoformat() if isinstance(value, dt.datetime) else value.isoformat()
    return _text(value)[:10] or None


def _client():
    from supabase import create_client
    from components.storage_backend import _get_secret

    url = _get_secret("SUPABASE_URL")
    key = _get_secret("SUPABASE_SERVICE_ROLE_KEY")
    if not url or not key:
        raise RuntimeError(
            "Package Hardening requires SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY."
        )
    return create_client(url, key)


def _rows(response) -> list[dict[str, Any]]:
    return [dict(row) for row in (getattr(response, "data", None) or [])]


def _rpc(name: str, params: dict[str, Any]) -> dict[str, Any]:
    response = _client().rpc(name, params).execute()
    data = getattr(response, "data", None)
    if isinstance(data, dict):
        return dict(data)
    if isinstance(data, list) and data and isinstance(data[0], dict):
        return dict(data[0])
    return {}


def list_packages(active_only: bool = False) -> list[dict[str, Any]]:
    query = _client().table("hm_packages").select("*")
    if active_only:
        query = query.eq("status", "active")
    return _rows(query.order("updated_at", desc=True).execute())


def save_package(
    *,
    package_id: object = "",
    package_name: object,
    session_count: object,
    cost_per_session: object,
    total_value: object = None,
    currency: object = "INR",
    inclusions: dict[str, object] | None = None,
    status: object = "active",
    actor_id: object = "admin",
) -> dict[str, Any]:
    sessions = max(_integer(session_count, 1), 1)
    cost = max(_number(cost_per_session), 0.0)
    total = max(_number(total_value, sessions * cost), 0.0)
    result = _rpc(
        "hm_admin_save_package",
        {
            "p_package_id": _text(package_id),
            "p_package_name": _text(package_name),
            "p_session_count": sessions,
            "p_cost_per_session": cost,
            "p_total_value": total,
            "p_currency": _text(currency) or "INR",
            "p_inclusions": dict(inclusions or {}),
            "p_status": _text(status).lower() or "active",
            "p_actor_id": _text(actor_id),
        },
    )
    _sync_legacy_package_state()
    return result


def get_subscription_metrics(subscription_id: object) -> dict[str, Any]:
    return _rpc(
        "hm_package_subscription_metrics",
        {"p_subscription_id": _text(subscription_id)},
    )


def get_member_package_summary(member_id: object) -> dict[str, Any]:
    result = _rpc("hm_package_member_summary", {"p_member_id": _text(member_id)})
    result.setdefault("package", {})
    result.setdefault("metrics", {})
    return result


def list_member_subscriptions(member_id: object = "") -> list[dict[str, Any]]:
    query = _client().table("hm_member_package_subscriptions").select("*")
    if _text(member_id):
        query = query.eq("member_id", _text(member_id))
    rows = _rows(query.order("subscribed_at", desc=True).execute())
    for row in rows:
        row["metrics"] = get_subscription_metrics(row.get("id"))
        row["inclusions_informational_only"] = True
    return rows


def list_subscription_events(subscription_id: object) -> list[dict[str, Any]]:
    return _rows(
        _client()
        .table("hm_package_subscription_events")
        .select("*")
        .eq("subscription_id", _text(subscription_id))
        .order("created_at", desc=True)
        .execute()
    )


def list_subscription_payments(subscription_id: object) -> list[dict[str, Any]]:
    return _rows(
        _client()
        .table("hm_package_payments")
        .select("*")
        .eq("subscription_id", _text(subscription_id))
        .order("created_at", desc=True)
        .execute()
    )


def list_usage_events(subscription_id: object) -> list[dict[str, Any]]:
    return _rows(
        _client()
        .table("hm_package_usage_events")
        .select("*")
        .eq("subscription_id", _text(subscription_id))
        .order("created_at", desc=True)
        .execute()
    )


def assign_or_replace_member_package(
    *,
    member_id: object,
    package_id: object,
    start_date: object = None,
    expiry_date: object = None,
    payment_status: object = "not_recorded",
    amount_paid: object = 0,
    payment_date: object = None,
    payment_reference: object = "",
    assignment_type: object = "replacement",
    unused_sessions_decision: object = "",
    replacement_reason: object = "",
    manual_adjustment_sessions: object = 0,
    actor_id: object = "admin",
) -> dict[str, Any]:
    result = _rpc(
        "hm_admin_assign_member_package",
        {
            "p_member_id": _text(member_id),
            "p_package_id": _text(package_id),
            "p_start_date": _date_text(start_date) or dt.date.today().isoformat(),
            "p_expiry_date": _date_text(expiry_date),
            "p_payment_status": _text(payment_status).lower() or "not_recorded",
            "p_amount_paid": max(_number(amount_paid), 0.0),
            "p_payment_date": _date_text(payment_date),
            "p_payment_reference": _text(payment_reference),
            "p_assignment_type": _text(assignment_type).lower() or "replacement",
            "p_unused_sessions_decision": _text(unused_sessions_decision).lower(),
            "p_replacement_reason": _text(replacement_reason),
            "p_manual_adjustment_sessions": max(_integer(manual_adjustment_sessions), 0),
            "p_actor_id": _text(actor_id),
        },
    )
    _sync_legacy_package_state()
    if result.get("assigned"):
        _notify_package_assignment(result, actor_id=actor_id)
    return result


def adjust_subscription_sessions(
    *,
    subscription_id: object,
    adjustment_type: object,
    session_delta: object,
    reason: object,
    actor_id: object = "admin",
) -> dict[str, Any]:
    result = _rpc(
        "hm_admin_adjust_package_sessions",
        {
            "p_subscription_id": _text(subscription_id),
            "p_adjustment_type": _text(adjustment_type).lower(),
            "p_session_delta": _integer(session_delta),
            "p_reason": _text(reason),
            "p_actor_id": _text(actor_id),
        },
    )
    _sync_legacy_package_state()
    return result


def update_subscription(
    *,
    subscription_id: object,
    action: object,
    reason: object = "",
    expiry_date: object = None,
    payment_status: object = "",
    amount: object = 0,
    payment_date: object = None,
    reference: object = "",
    actor_id: object = "admin",
) -> dict[str, Any]:
    result = _rpc(
        "hm_admin_update_package_subscription",
        {
            "p_subscription_id": _text(subscription_id),
            "p_action": _text(action).lower(),
            "p_reason": _text(reason),
            "p_expiry_date": _date_text(expiry_date),
            "p_payment_status": _text(payment_status).lower(),
            "p_amount": max(_number(amount), 0.0),
            "p_payment_date": _date_text(payment_date),
            "p_reference": _text(reference),
            "p_actor_id": _text(actor_id),
        },
    )
    _sync_legacy_package_state()
    _notify_subscription_update(result, actor_id=actor_id)
    return result


def schedule_capacity(member_id: object, schedule_date: object = None) -> dict[str, Any]:
    summary = get_member_package_summary(member_id)
    package = dict(summary.get("package") or {})
    metrics = dict(summary.get("metrics") or {})
    reasons: list[str] = []
    has_package = bool(summary.get("has_current_package") and package.get("id"))
    if not has_package:
        reasons.append("No active package is assigned to this member.")
    if _text(package.get("status")).lower() == "paused":
        reasons.append("The member package is paused.")
    target_date = _date_text(schedule_date)
    if target_date and _date_text(package.get("start_date")):
        if target_date < _date_text(package.get("start_date")):
            reasons.append("The selected date is before the package start date.")
    if target_date and _date_text(package.get("expiry_date")):
        if target_date > _date_text(package.get("expiry_date")):
            reasons.append("The selected date is after the package expiry date.")
    available = _integer(metrics.get("sessions_available_to_schedule"))
    if has_package and available <= 0:
        reasons.append("No package sessions are available for another scheduled session.")
    return {
        "allowed": not reasons,
        "requires_override": bool(reasons),
        "reasons": reasons,
        "message": " ".join(reasons),
        "package": package,
        "metrics": metrics,
        "summary": summary,
    }


def record_schedule_limit_override(
    *, member_id: object, schedule_id: object, reason: object, actor_id: object
) -> dict[str, Any]:
    return _rpc(
        "hm_admin_record_schedule_limit_override",
        {
            "p_member_id": _text(member_id),
            "p_schedule_id": _text(schedule_id),
            "p_reason": _text(reason),
            "p_actor_id": _text(actor_id),
        },
    )


def historical_schedule_cost(schedule: dict[str, Any]) -> float:
    result = _client().rpc(
        "hm_package_schedule_cost", {"p_schedule": dict(schedule or {})}
    ).execute()
    return _number(getattr(result, "data", 0))


def historical_schedule_subscription_id(schedule: dict[str, Any]) -> str:
    result = _client().rpc(
        "hm_package_schedule_subscription_id", {"p_schedule": dict(schedule or {})}
    ).execute()
    return _text(getattr(result, "data", ""))


def member_session_ledger(member_id: object) -> dict[str, Any]:
    from components import db as db_api

    summary = get_member_package_summary(member_id)
    package = dict(summary.get("package") or {})
    metrics = dict(summary.get("metrics") or {})
    rows = []
    consumed_cost = 0.0
    for schedule in db_api.list_member_schedules(
        member_id=_text(member_id), include_cancelled=True, limit=0
    ):
        status = _text(schedule.get("status") or "scheduled").lower()
        consumed = status == "completed" or bool(schedule.get("session_counted"))
        cost = historical_schedule_cost(schedule)
        subscription_id = historical_schedule_subscription_id(schedule)
        if consumed:
            consumed_cost += cost
        time_text = _text(schedule.get("start_time"))
        if _text(schedule.get("end_time")):
            time_text += f" - {_text(schedule.get('end_time'))}"
        rows.append(
            {
                "id": schedule.get("id", ""),
                "title": schedule.get("title")
                or schedule.get("schedule_type")
                or "Scheduled session",
                "date": schedule.get("schedule_date", ""),
                "time": time_text,
                "status": db_api.schedule_display_status_label_v104b11(schedule),
                "raw_status": status,
                "cost": cost,
                "currency": _subscription_currency(subscription_id)
                or package.get("currency", "INR"),
                "member_package_id": subscription_id,
                "consumed": consumed,
                "count_note": "Consumed" if consumed else "Not consumed",
            }
        )
    rows.sort(key=lambda row: (_text(row.get("date")), _text(row.get("time"))), reverse=True)
    return {
        "rows": rows,
        "consumed_count": _integer(metrics.get("sessions_consumed")),
        "reserved_count": _integer(metrics.get("sessions_reserved")),
        "consumed_cost": consumed_cost,
        "package": package or None,
        "package_sessions": _integer(metrics.get("package_sessions")),
        "remaining_sessions": _integer(metrics.get("sessions_remaining")),
        "available_to_schedule": _integer(
            metrics.get("sessions_available_to_schedule")
        ),
        "overbooked_sessions": _integer(metrics.get("overbooked_sessions")),
        "metrics": metrics,
    }


def record_schedule_consumption_event(
    schedule: dict[str, Any], *, actor_id: object = "system"
) -> None:
    if not schedule or not (
        _text(schedule.get("status")).lower() == "completed"
        or bool(schedule.get("session_counted"))
    ):
        return
    subscription_id = historical_schedule_subscription_id(schedule)
    if not subscription_id:
        return
    payload = {
        "subscription_id": subscription_id,
        "member_id": _text(schedule.get("member_id")),
        "schedule_id": _text(schedule.get("id")),
        "event_type": "schedule_consumed",
        "allowance_delta": 0,
        "consumption_delta": 0,
        "reason": "Schedule reached the canonical consumed state.",
        "source": "streamlit_schedule",
        "dedupe_key": f"schedule_consumed|{_text(schedule.get('id'))}",
        "metadata": {
            "status": schedule.get("status", ""),
            "session_counted": bool(schedule.get("session_counted")),
            "historical_cost": historical_schedule_cost(schedule),
        },
        "created_by": _text(actor_id) or "system",
    }
    try:
        _client().table("hm_package_usage_events").upsert(
            payload, on_conflict="dedupe_key"
        ).execute()
    except Exception:
        pass


def _subscription_currency(subscription_id: object) -> str:
    if not _text(subscription_id):
        return ""
    rows = _rows(
        _client()
        .table("hm_member_package_subscriptions")
        .select("currency")
        .eq("id", _text(subscription_id))
        .limit(1)
        .execute()
    )
    return _text((rows[0] if rows else {}).get("currency"))


def _sync_legacy_package_state() -> None:
    """Mirror normalized masters/snapshots for rollback and older read paths."""
    try:
        from components import db as db_api

        packages = list_packages(active_only=False)
        subscriptions = list_member_subscriptions()
        db = db_api.load_db()
        db["packages"] = [
            {
                **row,
                "number_of_people": 1,
                "inclusions_informational_only": True,
            }
            for row in packages
        ]
        db["member_packages"] = [
            {
                **{key: value for key, value in row.items() if key != "metrics"},
                "number_of_people": 1,
                "inclusions_informational_only": True,
            }
            for row in subscriptions
        ]
        db_api.save_db(db)
    except Exception:
        # Normalized tables remain authoritative. A failed compatibility mirror must
        # not roll back the accepted normalized write.
        pass


def _notify_package_assignment(result: dict[str, Any], *, actor_id: object) -> None:
    subscription = dict(result.get("subscription") or {})
    member_id = _text(subscription.get("member_id"))
    if not member_id:
        return
    try:
        from components import db as db_api
        from components.member_email import queue_member_event_email

        db = db_api.load_db()
        metrics = dict(result.get("metrics") or {})
        delivery = queue_member_event_email(
            db,
            member_id=member_id,
            kind="package_assigned",
            subject="Your HealthyMe package is ready",
            message=(
                f"Your {subscription.get('package_name') or 'HealthyMe package'} is now active. "
                "Please sign in to review the package dates, session balance and payment status."
            ),
            actor_id=actor_id,
            source="normalized_member_package",
            source_id=subscription.get("id", ""),
            details={
                "Package": subscription.get("package_name", ""),
                "Start date": subscription.get("start_date", ""),
                "Expiry date": subscription.get("expiry_date", ""),
                "Session allowance": metrics.get("package_sessions", subscription.get("session_count", 0)),
                "Payment status": subscription.get("payment_status", ""),
            },
            dedupe_key=f"normalized_package_assigned|{subscription.get('id', '')}",
            append_message=True,
            append_notification=True,
        )
        db_api.save_db(db)
        result["email_delivery"] = delivery
    except Exception:
        pass


def _notify_subscription_update(result: dict[str, Any], *, actor_id: object) -> None:
    subscription = dict(result.get("subscription") or {})
    event_type = _text(result.get("event_type"))
    member_id = _text(subscription.get("member_id"))
    if not member_id or event_type == "payment_updated":
        return
    subjects = {
        "extended": "Your HealthyMe package has been extended",
        "paused": "Your HealthyMe package has been paused",
        "resumed": "Your HealthyMe package has resumed",
        "cancelled": "Your HealthyMe package has been cancelled",
        "completed": "Your HealthyMe package is complete",
        "refunded": "Your HealthyMe package refund has been recorded",
    }
    subject = subjects.get(event_type)
    if not subject:
        return
    try:
        from components import db as db_api
        from components.member_email import queue_member_event_email

        db = db_api.load_db()
        delivery = queue_member_event_email(
            db,
            member_id=member_id,
            kind=f"package_{event_type}",
            subject=subject,
            message=(
                f"There is an update to your {subscription.get('package_name') or 'HealthyMe package'}. "
                "Please sign in to review the latest status and dates."
            ),
            actor_id=actor_id,
            source="normalized_member_package",
            source_id=subscription.get("id", ""),
            details={
                "Package": subscription.get("package_name", ""),
                "Status": subscription.get("status", ""),
                "Expiry date": subscription.get("expiry_date", ""),
                "Payment status": subscription.get("payment_status", ""),
            },
            dedupe_key=(
                f"normalized_package_{event_type}|{subscription.get('id', '')}|"
                f"{subscription.get('updated_at', '')}"
            ),
            append_message=True,
            append_notification=True,
        )
        db_api.save_db(db)
        result["email_delivery"] = delivery
    except Exception:
        pass
