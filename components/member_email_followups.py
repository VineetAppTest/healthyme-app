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
    for row in reversed(rows or []):
        if predicate(row):
            row.update(_delivery_fields(delivery))
            return


def _schedule_details(schedule_module, row: dict[str, Any]) -> dict[str, object]:
    context = {}
    try:
        context = schedule_module.schedule_time_context(
            row,
            member_id=row.get("member_id", ""),
        )
    except Exception:
        context = {}
    member_view = context.get("member", {}) if isinstance(context, dict) else {}
    time_text = " - ".join(
        value
        for value in [row.get("start_time", ""), row.get("end_time", "")]
        if value
    )
    return {
        "Session": row.get("title") or row.get("schedule_type") or "Scheduled session",
        "Date": member_view.get("date_label") or row.get("schedule_date", ""),
        "Time": member_view.get("time_window") or time_text,
        "Timezone": member_view.get("timezone_name") or row.get("member_timezone_name", ""),
        "Mode": row.get("mode", ""),
        "Link/location": row.get("location_or_link", ""),
    }


def _install_schedule_reminder_delivery(db_api, schedule_module) -> None:
    base_reminders = schedule_module.queue_timezone_aware_schedule_acknowledgement_reminders

    def queue_timezone_aware_schedule_acknowledgement_reminders(
        member_id,
        actor_id="system",
    ):
        queued = base_reminders(member_id, actor_id=actor_id)
        if not queued:
            return queued
        db = db_api.load_db()
        for row in queued:
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
                details=_schedule_details(schedule_module, row),
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

    schedule_module.queue_timezone_aware_schedule_acknowledgement_reminders = (
        queue_timezone_aware_schedule_acknowledgement_reminders
    )


def _install_auto_stop_delivery(db_api) -> None:
    base_auto_stop = db_api._auto_stop_expired_supplements_v102_3a

    def auto_stop_expired_supplements(db, actor_id="system"):
        before = {
            str(row.get("id", "")): str(row.get("status", ""))
            for row in db.get("member_supplements", []) or []
            if isinstance(row, dict)
        }
        changed = base_auto_stop(db, actor_id=actor_id)
        for row in db.get("member_supplements", []) or []:
            if not isinstance(row, dict):
                continue
            row_id = str(row.get("id", ""))
            newly_stopped = (
                before.get(row_id, "").lower() == "active"
                and str(row.get("status", "")).lower() == "stopped"
                and str(row.get("stop_reason", "")) == "Predefined Timelines"
            )
            if not newly_stopped:
                continue
            delivery = queue_member_event_email(
                db,
                member_id=row.get("member_id", ""),
                kind="supplement_auto_stopped",
                subject="A supplement timeline in your HealthyMe plan has ended",
                message=(
                    f"The planned timeline for {row.get('supplement_name') or 'a supplement'} has ended, "
                    "and it is now marked as stopped in HealthyMe."
                ),
                actor_id=actor_id,
                source="member_supplement",
                source_id=row_id,
                email_to=row.get("member_email", ""),
                details={
                    "Supplement": row.get("supplement_name", ""),
                    "Stop date": row.get("stop_date", ""),
                    "Reason": row.get("stop_reason", ""),
                },
                dedupe_key=f"supplement_auto_stopped|{row_id}|{row.get('stopped_at', '')}",
                append_message=True,
                append_notification=True,
            )
            row.update(_delivery_fields(delivery))
        return changed

    db_api._auto_stop_expired_supplements_v102_3a = auto_stop_expired_supplements


def _install_final_report_delivery(db_api) -> None:
    base_finalize = db_api.finalize_admin_assessment

    def finalize_admin_assessment(
        user_id,
        assessment_data,
        activation_selected=False,
        instance_id=None,
    ):
        result = base_finalize(
            user_id,
            assessment_data,
            activation_selected=activation_selected,
            instance_id=instance_id,
        )
        if not result or result.get("already_finalized"):
            return result
        db = db_api.load_db()
        body_mind_ready = bool(result.get("body_mind_unlocked"))
        delivery = queue_member_event_email(
            db,
            member_id=user_id,
            kind="assessment_finalized",
            subject="Your HealthyMe expert review is complete",
            message=(
                "Your wellness assessment has been reviewed and your latest HealthyMe guidance is now available. "
                "Please sign in to review your personalized content."
            ),
            actor_id="admin",
            source="assessment_finalization",
            source_id=instance_id or "member_workflow",
            details={
                "Review status": "Completed",
                "Body-Mind Connection": "Available" if body_mind_ready else "Not activated",
            },
            dedupe_key=f"assessment_finalized|{user_id}|{instance_id or 'member_workflow'}",
            append_message=True,
            append_notification=True,
        )
        db_api.save_db(db)
        result["email_delivery"] = delivery
        return result

    db_api.finalize_admin_assessment = finalize_admin_assessment

    base_manual_unlock = db_api.manually_unlock_body_mind_after_finalization

    def manually_unlock_body_mind_after_finalization(user_id):
        success, message = base_manual_unlock(user_id)
        if not success:
            return success, message
        db = db_api.load_db()
        delivery = queue_member_event_email(
            db,
            member_id=user_id,
            kind="body_mind_activated",
            subject="Body-Mind Connection is now available in HealthyMe",
            message=(
                "Your wellness team has activated the Body-Mind Connection section. "
                "Please sign in to review and complete it when convenient."
            ),
            actor_id="admin",
            source="body_mind_activation",
            source_id=user_id,
            dedupe_key=f"body_mind_activated|{user_id}",
            append_message=True,
            append_notification=True,
        )
        db_api.save_db(db)
        suffix = (
            " Email sent to the member."
            if delivery.get("status") == "sent"
            else " Member email was recorded but delivery needs configuration or retry."
        )
        return success, message + suffix

    db_api.manually_unlock_body_mind_after_finalization = (
        manually_unlock_body_mind_after_finalization
    )


def install_member_email_followups() -> None:
    global _INSTALLED
    if _INSTALLED:
        return
    _INSTALLED = True

    from components import db as db_api
    from components import schedule_timezone as schedule_module

    _install_schedule_reminder_delivery(db_api, schedule_module)
    _install_auto_stop_delivery(db_api)
    _install_final_report_delivery(db_api)
