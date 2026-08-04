from __future__ import annotations

import datetime as dt
import functools
import uuid
from typing import Any

from components.content_repository_store import get_repository_item
from components.storage_backend import load_state, save_state


_INSTALLED = False


def _text(value: object) -> str:
    return str(value or "").strip()


def _now_iso() -> str:
    return dt.datetime.now().isoformat(timespec="seconds")


def _member_row(state: dict[str, Any], member_id: str) -> dict[str, Any]:
    return next(
        (
            dict(row)
            for row in state.get("users", []) or []
            if _text((row or {}).get("id")) == _text(member_id)
        ),
        {},
    )


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
) -> tuple[str, str, str, dict[str, str]]:
    stopped = _text(saved.get("status")).lower() in {
        "stopped",
        "inactive",
        "archived",
    }
    action = "stopped" if stopped else "updated"
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
    member = _member_row(state, member_id)
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
        "member_email": _text(member.get("email")),
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
            "member_email": _text(member.get("email")),
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
        _upsert_visible_delivery(
            "exercise",
            saved,
            actor_id=_text(kwargs.get("actor_id")) or "admin",
        )
        return saved

    exercise_api.save_exercise_member_allocation = save_exercise_member_allocation

    base_supplement_save = supplement_api.save_supplement_member_allocation

    @functools.wraps(base_supplement_save)
    def save_supplement_member_allocation(*args, **kwargs):
        saved = base_supplement_save(*args, **kwargs)
        _upsert_visible_delivery(
            "supplement",
            saved,
            actor_id=_text(kwargs.get("actor_id")) or "admin",
        )
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
