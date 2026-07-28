from __future__ import annotations

from typing import Any

from components.member_email import (
    DELIVERY_VERSION,
    _send_resend_email,
)


RETRYABLE_STATUSES = {"failed", "configuration_missing"}


def list_member_email_deliveries(
    db: dict[str, Any],
    *,
    member_id: object = "",
    limit: int = 50,
) -> list[dict[str, Any]]:
    wanted = str(member_id or "").strip()
    rows = [
        dict(row)
        for row in db.get("email_delivery_logs", []) or []
        if not wanted or str(row.get("member_id", "")) == wanted
    ]
    rows.sort(key=lambda row: str(row.get("ts", "")), reverse=True)
    return rows[:limit] if limit else rows


def _update_linked_records(db: dict[str, Any], log: dict[str, Any]) -> None:
    fields = {
        "email_delivery_version": DELIVERY_VERSION,
        "email_delivery_status": log.get("status", ""),
        "email_provider": log.get("provider", ""),
        "email_provider_id": log.get("provider_id", ""),
        "email_delivery_error": log.get("error", ""),
        "email_attempted_at": log.get("attempted_at", ""),
        "email_to": log.get("email_to", ""),
        "email_subject": log.get("subject", ""),
        "email_dedupe_key": log.get("dedupe_key", ""),
    }
    message_id = str(log.get("message_id", ""))
    notification_id = str(log.get("notification_id", ""))
    for row in db.get("messages", []) or []:
        if message_id and str(row.get("id", "")) == message_id:
            row.update(fields)
    for row in db.get("notifications", []) or []:
        if notification_id and str(row.get("id", "")) == notification_id:
            row.update(fields)
        elif str(row.get("email_event_id", "")) == str(log.get("id", "")):
            row.update(fields)


def retry_member_email_delivery(
    db: dict[str, Any],
    event_id: object,
) -> dict[str, Any]:
    wanted = str(event_id or "").strip()
    log = next(
        (
            row
            for row in db.get("email_delivery_logs", []) or []
            if str(row.get("id", "")) == wanted
        ),
        None,
    )
    if not log:
        return {"status": "not_found", "error": "Email event was not found."}
    if str(log.get("status", "")) == "sent":
        return dict(log)
    if str(log.get("status", "")) == "recipient_missing":
        return dict(log)

    delivery = _send_resend_email(
        recipient=str(log.get("email_to", "")),
        member_name=str(log.get("member_name", "")),
        subject=str(log.get("subject", "")),
        message=str(log.get("message", "")),
        details=dict(log.get("details", {}) or {}),
        idempotency_key=f"{log.get('dedupe_key', wanted)}|retry",
    )
    log.update(delivery)
    log["email_delivery_version"] = DELIVERY_VERSION
    log["retry_count"] = int(log.get("retry_count", 0) or 0) + 1
    log["last_retry_at"] = delivery.get("attempted_at", "")
    _update_linked_records(db, log)
    return dict(log)


def retry_failed_member_emails(
    db: dict[str, Any],
    *,
    member_id: object = "",
    limit: int = 20,
) -> dict[str, int]:
    wanted = str(member_id or "").strip()
    retryable = [
        row
        for row in db.get("email_delivery_logs", []) or []
        if str(row.get("status", "")) in RETRYABLE_STATUSES
        and (not wanted or str(row.get("member_id", "")) == wanted)
    ]
    retryable.sort(key=lambda row: str(row.get("ts", "")))
    attempted = sent = failed = 0
    for row in retryable[:limit]:
        attempted += 1
        result = retry_member_email_delivery(db, row.get("id", ""))
        if result.get("status") == "sent":
            sent += 1
        else:
            failed += 1
    return {"attempted": attempted, "sent": sent, "failed": failed}
