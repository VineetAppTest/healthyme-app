from __future__ import annotations

import datetime as dt
import functools
import hashlib
import json
import uuid
from typing import Any

from components.content_repository_store import get_repository_item
from components.member_email import queue_member_event_email
from components.storage_backend import load_state, save_state


_INSTALLED = False


def _text(value: object) -> str:
    return str(value or "").strip()


def _now_iso() -> str:
    return dt.datetime.now().isoformat(timespec="seconds")


def _stable_digest(payload: object) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _repository_payload(item_type: str, source_id: str) -> dict[str, Any]:
    if not _text(source_id):
        return {}
    try:
        row = get_repository_item(item_type, source_id) or {}
        return dict(row.get("payload") or {})
    except Exception:
        return {}


def _benefits(domain: str, saved: dict[str, Any]) -> str:
    snapshot = dict(saved.get("source_snapshot") or {})
    payload = _repository_payload(domain, _text(saved.get("source_id")))
    benefit = _text(
        snapshot.get("benefits")
        or payload.get("benefits")
        or payload.get("purpose")
        or payload.get("health_benefits")
    )
    if benefit:
        return benefit
    guidance = _text(snapshot.get("instructions") or payload.get("instructions"))
    return guidance or "Follow the guidance shared by your HealthyMe nutritionist."


def _date_window(saved: dict[str, Any]) -> str:
    start = _text(saved.get("start_date"))
    end = _text(saved.get("end_date"))
    if start and end:
        return f"{start} to {end}"
    return start or end or "As advised"


def _message_payload(
    domain: str,
    saved: dict[str, Any],
    *,
    actor_id: str,
    event_action: str = "",
) -> tuple[str, str, str, dict[str, str]]:
    stopped = _text(saved.get("status")).lower() in {
        "stopped",
        "inactive",
        "archived",
    }
    action = event_action or ("stopped" if stopped else "updated")
    benefits = _benefits(domain, saved)
    if domain == "exercise":
        name = _text(saved.get("exercise_name") or saved.get("title")) or "Exercise"
        subject = (
            f"Exercise allocation stopped: {name}"
            if stopped
            else f"Exercise added to your HealthyMe plan: {name}"
        )
        details = {
            "Exercise": name,
            "Schedule": _date_window(saved),
            "Benefits": benefits,
            "Member instructions": _text(saved.get("instructions")) or "Not provided",
        }
    else:
        name = _text(saved.get("supplement_name") or saved.get("title")) or "Supplement"
        subject = (
            f"Supplement allocation stopped: {name}"
            if stopped
            else f"Supplement added to your HealthyMe plan: {name}"
        )
        details = {
            "Supplement": name,
            "Dosage": _text(saved.get("dosage")) or "As advised",
            "Frequency": _text(saved.get("frequency")) or "As advised",
            "Timing": _text(saved.get("timing")) or "As advised",
            "Schedule": _date_window(saved),
            "Benefits": benefits,
            "Member instructions": _text(saved.get("instructions")) or "Not provided",
        }
    detail_text = " · ".join(f"{key}: {value}" for key, value in details.items())
    message = (
        f"Your {domain} allocation has been {action}. {detail_text}. "
        "Please review it in your Current Member Plan."
    )
    return subject, message, benefits, details


def _allocation_dedupe_key(domain: str, saved: dict[str, Any]) -> str:
    common = {
        "domain": domain,
        "member_id": _text(saved.get("member_id")),
        "source_id": _text(saved.get("source_id")),
        "start_date": _text(saved.get("start_date")),
        "end_date": _text(saved.get("end_date")),
        "instructions": _text(saved.get("instructions")),
        "status": _text(saved.get("status")).lower(),
    }
    if domain == "exercise":
        common.update(
            {
                "name": _text(saved.get("exercise_name") or saved.get("title")),
                "notes": _text(saved.get("notes")),
            }
        )
    else:
        common.update(
            {
                "name": _text(saved.get("supplement_name") or saved.get("title")),
                "dosage": _text(saved.get("dosage")),
                "frequency": _text(saved.get("frequency")),
                "timing": _text(saved.get("timing")),
            }
        )
    return f"member-allocation-email-v2|{domain}|{_stable_digest(common)}"


def _supplement_placeholder_notification(
    state: dict[str, Any],
    member_id: str,
) -> dict[str, Any] | None:
    return next(
        (
            row
            for row in reversed(state.get("notifications", []) or [])
            if isinstance(row, dict)
            and _text(row.get("kind")) == "supplement_regimen_updated"
            and _text(row.get("user_id") or row.get("member_id")) == member_id
            and not _text(row.get("dedupe_key"))
        ),
        None,
    )


def _queue_allocated_delivery(
    domain: str,
    saved: dict[str, Any],
    *,
    actor_id: str,
) -> dict[str, Any]:
    """Send one idempotent email and retain one visible in-app allocation event."""
    member_id = _text(saved.get("member_id"))
    if not member_id:
        return {
            "status": "member_missing",
            "error": "The allocation has no member identity.",
        }

    state = load_state()
    stable_key = _allocation_dedupe_key(domain, saved)
    existing = next(
        (
            row
            for row in state.get("email_delivery_logs", []) or []
            if isinstance(row, dict) and _text(row.get("dedupe_key")) == stable_key
        ),
        None,
    )
    placeholder = (
        _supplement_placeholder_notification(state, member_id)
        if domain == "supplement"
        else None
    )
    subject, message, benefits, details = _message_payload(
        domain,
        saved,
        actor_id=actor_id,
        event_action="allocated",
    )
    source = f"member_{domain}_allocation"
    delivery = queue_member_event_email(
        state,
        member_id=member_id,
        kind=f"{domain}_allocated",
        subject=subject,
        message=message,
        actor_id=_text(actor_id) or "admin",
        source=source,
        source_id=_text(saved.get("id")),
        email_to=_text(saved.get("member_email")),
        details=details,
        dedupe_key=stable_key,
        append_message=True,
        append_notification=placeholder is None,
    )

    if placeholder is not None:
        if existing:
            state["notifications"] = [
                row
                for row in state.get("notifications", []) or []
                if row is not placeholder
            ]
        else:
            placeholder.update(
                {
                    "id": _text(placeholder.get("id")) or str(uuid.uuid4())[:8],
                    "kind": f"{domain}_allocated",
                    "user_id": member_id,
                    "member_id": member_id,
                    "member_email": _text(saved.get("member_email")),
                    "message": message[:500],
                    "status": "queued",
                    "email_required": True,
                    "created_by": _text(actor_id) or "admin",
                    "source": source,
                    "source_id": _text(saved.get("id")),
                    "allocation_id": _text(saved.get("id")),
                    "source_message_id": _text(delivery.get("message_id")),
                    "benefits": benefits,
                    "details": details,
                    "email_event_id": _text(delivery.get("id")),
                    "email_delivery_version": _text(
                        delivery.get("email_delivery_version")
                    ),
                    "email_delivery_status": _text(delivery.get("status")),
                    "email_provider": _text(delivery.get("provider")),
                    "email_provider_id": _text(delivery.get("provider_id")),
                    "email_delivery_error": _text(delivery.get("error")),
                    "email_attempted_at": _text(delivery.get("attempted_at")),
                    "email_to": _text(delivery.get("email_to")),
                    "email_subject": subject,
                    "dedupe_key": stable_key,
                }
            )
    save_state(state)
    return {**dict(delivery), "in_app_created": True}


def queue_meal_plan_allocation(
    member_plan: dict[str, Any],
    *,
    source_profile_id: str,
    meal_rows: list[dict[str, Any]],
    actor_id: str,
) -> dict[str, Any]:
    """Notify once after a reusable Meal Profile is successfully published."""
    member_id = _text(member_plan.get("assigned_member_id"))
    if not member_id:
        return {
            "status": "member_missing",
            "error": "The published Meal Plan has no member identity.",
        }

    profile_name = _text(member_plan.get("profile_name")) or "Meal Plan"
    start_date = _text(member_plan.get("start_date")) or "As advised"
    fingerprint_rows = [
        {
            "day": row.get("day_number"),
            "slot": _text(row.get("slot_name")),
            "order": row.get("item_order"),
            "meal": _text(row.get("reference_label")),
            "portion": _text(row.get("portion")),
            "instruction": _text(row.get("instruction")),
        }
        for row in meal_rows
        if _text(row.get("item_type")).lower() == "meal"
    ]
    stable_key = "meal-plan-allocation-email-v2|" + _stable_digest(
        {
            "member_id": member_id,
            "source_profile_id": _text(source_profile_id),
            "start_date": start_date,
            "meals": fingerprint_rows,
        }
    )
    subject = f"Meal Plan added to your HealthyMe plan: {profile_name}"
    message = (
        "Your Meal Plan has been allocated by your HealthyMe nutritionist. "
        "Please review the complete schedule in your Current Member Plan."
    )
    details = {
        "Meal Profile": profile_name,
        "Plan Start Date": start_date,
        "Meal Schedule": f"{len(fingerprint_rows)} saved meal item(s) across 7 days",
    }
    state = load_state()
    delivery = queue_member_event_email(
        state,
        member_id=member_id,
        kind="meal_plan_allocated",
        subject=subject,
        message=message,
        actor_id=_text(actor_id) or "admin",
        source="meal_profile_publish",
        source_id=_text(member_plan.get("id")),
        details=details,
        dedupe_key=stable_key,
        append_message=True,
        append_notification=True,
    )
    save_state(state)
    return {**dict(delivery), "in_app_created": True}


def delivery_summary(delivery: dict[str, Any] | None) -> str:
    status = _text((delivery or {}).get("status"))
    if (delivery or {}).get("in_app_created") is False:
        return "Allocation saved; notification delivery needs review."
    if status == "sent":
        return "In-app notification created and member email sent."
    if status:
        return f"In-app notification created; member email status: {status}."
    return "In-app notification created."


def _upsert_visible_delivery(
    domain: str,
    saved: dict[str, Any],
    *,
    actor_id: str,
) -> None:
    member_id = _text(saved.get("member_id"))
    allocation_id = _text(saved.get("id"))
    if not member_id or not allocation_id:
        return
    state = load_state()
    member_email = _text(
        saved.get("member_email")
        or saved.get("assigned_member_email")
        or saved.get("email")
    )
    timestamp = _now_iso()
    source_updated_at = _text(saved.get("updated_at") or saved.get("stopped_at"))
    dedupe_key = f"{domain}_allocation_visible|{allocation_id}|{source_updated_at}"
    if any(
        _text(row.get("dedupe_key")) == dedupe_key
        for row in state.get("messages", []) or []
        if isinstance(row, dict)
    ):
        return

    subject, message, benefits, details = _message_payload(
        domain,
        saved,
        actor_id=actor_id,
    )
    kind = f"{domain}_allocation_updated"
    message_row = {
        "id": str(uuid.uuid4())[:8],
        "ts": timestamp,
        "member_id": member_id,
        "member_email": member_email,
        "sender_role": "admin",
        "actor_id": _text(actor_id) or "admin",
        "subject": subject,
        "message": message,
        "status": "queued",
        "email_required": False,
        "source": f"member_{domain}_allocation",
        "allocation_id": allocation_id,
        "source_id": _text(saved.get("source_id")),
        "benefits": benefits,
        "details": details,
        "dedupe_key": dedupe_key,
    }
    state.setdefault("messages", []).append(message_row)

    notification = None
    if domain == "supplement":
        notification = next(
            (
                row
                for row in reversed(state.get("notifications", []) or [])
                if isinstance(row, dict)
                and _text(row.get("kind")) == "supplement_regimen_updated"
                and _text(row.get("user_id") or row.get("member_id")) == member_id
                and not _text(row.get("allocation_id"))
            ),
            None,
        )
    if notification is None:
        notification = {}
        state.setdefault("notifications", []).append(notification)
    notification.update(
        {
            "ts": timestamp,
            "kind": kind,
            "user_id": member_id,
            "member_id": member_id,
            "member_email": member_email,
            "message": message,
            "status": "queued",
            "email_required": False,
            "created_by": _text(actor_id) or "admin",
            "source": f"member_{domain}_allocation",
            "allocation_id": allocation_id,
            "source_id": _text(saved.get("source_id")),
            "benefits": benefits,
            "details": details,
            "dedupe_key": dedupe_key,
        }
    )
    save_state(state)


def install_member_allocation_notifications() -> None:
    global _INSTALLED
    if _INSTALLED:
        return
    _INSTALLED = True

    from components import exercise_member_allocation as exercise_api
    from components import supplement_member_allocation as supplement_api

    base_exercise_save = exercise_api.save_exercise_member_allocation

    @functools.wraps(base_exercise_save)
    def save_exercise_member_allocation(*args, **kwargs):
        saved = base_exercise_save(*args, **kwargs)
        actor_id = _text(kwargs.get("actor_id")) or "admin"
        try:
            if not _text(kwargs.get("allocation_id")):
                saved["notification_delivery"] = _queue_allocated_delivery(
                    "exercise", saved, actor_id=actor_id
                )
            else:
                _upsert_visible_delivery("exercise", saved, actor_id=actor_id)
        except Exception as exc:
            saved["notification_delivery"] = {
                "status": "failed",
                "error": str(exc)[:500],
                "in_app_created": False,
            }
        return saved

    exercise_api.save_exercise_member_allocation = save_exercise_member_allocation

    base_supplement_save = supplement_api.save_supplement_member_allocation

    @functools.wraps(base_supplement_save)
    def save_supplement_member_allocation(*args, **kwargs):
        saved = base_supplement_save(*args, **kwargs)
        actor_id = _text(kwargs.get("actor_id")) or "admin"
        try:
            if not _text(kwargs.get("allocation_id")):
                saved["notification_delivery"] = _queue_allocated_delivery(
                    "supplement", saved, actor_id=actor_id
                )
            else:
                _upsert_visible_delivery("supplement", saved, actor_id=actor_id)
        except Exception as exc:
            saved["notification_delivery"] = {
                "status": "failed",
                "error": str(exc)[:500],
                "in_app_created": False,
            }
        return saved

    supplement_api.save_supplement_member_allocation = (
        save_supplement_member_allocation
    )

    base_supplement_stop = supplement_api.stop_supplement_member_allocation

    @functools.wraps(base_supplement_stop)
    def stop_supplement_member_allocation(*args, **kwargs):
        saved = base_supplement_stop(*args, **kwargs)
        _upsert_visible_delivery(
            "supplement",
            saved,
            actor_id=_text(kwargs.get("actor_id")) or "admin",
        )
        return saved

    supplement_api.stop_supplement_member_allocation = (
        stop_supplement_member_allocation
    )
