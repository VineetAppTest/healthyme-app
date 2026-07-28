from __future__ import annotations

from typing import Any

from components.member_email import queue_member_event_email


_INSTALLED = False


def _delivery_fields(delivery: dict[str, Any]) -> dict[str, Any]:
    return {
        "email_event_id": delivery.get("id", ""),
        "email_delivery_version": delivery.get("email_delivery_version", "member-event-email-v1"),
        "email_delivery_status": delivery.get("status", ""),
        "email_provider": delivery.get("provider", ""),
        "email_provider_id": delivery.get("provider_id", ""),
        "email_delivery_error": delivery.get("error", ""),
        "email_attempted_at": delivery.get("attempted_at", ""),
        "email_to": delivery.get("email_to", ""),
        "email_subject": delivery.get("subject", ""),
        "email_dedupe_key": delivery.get("dedupe_key", ""),
    }


def _annotate_latest(rows: list[dict], delivery: dict[str, Any], predicate) -> None:
    for item in reversed(rows or []):
        if predicate(item):
            item.update(_delivery_fields(delivery))
            return


def install_legacy_schedule_reminder_delivery() -> None:
    global _INSTALLED
    if _INSTALLED:
        return
    _INSTALLED = True

    from components import db as db_api
    from components import schedule_timezone as schedule_module

    base_reminders = db_api.queue_schedule_acknowledgement_reminders_v104b11

    def queue_schedule_acknowledgement_reminders_v104b11(
        member_id,
        actor_id="system",
    ):
        queued = base_reminders(member_id, actor_id=actor_id)
        if not queued:
            return queued
        db = db_api.load_db()
        for row in queued:
            context = {}
            try:
                context = schedule_module.schedule_time_context(
                    row,
                    member_id=row.get("member_id") or member_id,
                )
            except Exception:
                context = {}
            member_view = context.get("member", {}) if isinstance(context, dict) else {}
            time_text = " - ".join(
                value
                for value in [row.get("start_time", ""), row.get("end_time", "")]
                if value
            )
            delivery = queue_member_event_email(
                db,
                member_id=row.get("member_id") or member_id,
                kind="schedule_48h_acknowledgement_reminder",
                subject="Please acknowledge your upcoming HealthyMe session",
                message=(
                    f"Your session, {row.get('title') or 'Scheduled session'}, is approaching. "
                    "Please sign in to acknowledge it or submit a reschedule request as soon as possible."
                ),
                actor_id=actor_id,
                source="schedule_48h_acknowledgement_reminder",
                source_id=row.get("id", ""),
                email_to=row.get("member_email", ""),
                details={
                    "Session": row.get("title") or row.get("schedule_type") or "Scheduled session",
                    "Date": member_view.get("date_label") or row.get("schedule_date", ""),
                    "Time": member_view.get("time_window") or time_text,
                    "Timezone": member_view.get("timezone_name") or row.get("member_timezone_name", ""),
                    "Mode": row.get("mode", ""),
                    "Link/location": row.get("location_or_link", ""),
                },
                dedupe_key=(
                    f"schedule_48h_acknowledgement_reminder|{row.get('id', '')}|"
                    f"{row.get('ack_reminder_48h_sent_at', '')}"
                ),
                append_message=False,
                append_notification=False,
            )
            _annotate_latest(
                db.get("messages", []),
                delivery,
                lambda item: item.get("schedule_id") == row.get("id")
                and item.get("source") == "schedule_48h_acknowledgement_reminder",
            )
            _annotate_latest(
                db.get("notifications", []),
                delivery,
                lambda item: item.get("schedule_id") == row.get("id")
                and item.get("kind") == "schedule_48h_acknowledgement_reminder",
            )
            row.update(_delivery_fields(delivery))
        db_api.save_db(db)
        return queued

    db_api.queue_schedule_acknowledgement_reminders_v104b11 = (
        queue_schedule_acknowledgement_reminders_v104b11
    )
