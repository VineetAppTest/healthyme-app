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


def _friendly_list(values: list[str]) -> str:
    clean = [str(value).strip() for value in values if str(value).strip()]
    if not clean:
        return ""
    if len(clean) == 1:
        return clean[0]
    return ", ".join(clean[:-1]) + f" and {clean[-1]}"


def _install_db_wrappers(db_api) -> None:
    if getattr(db_api, "_hm_member_email_wrappers_installed", False):
        return
    db_api._hm_member_email_wrappers_installed = True

    base_queue_member_message = db_api.queue_member_message

    def queue_member_message(member_id, sender_role, subject, message, actor_id=""):
        result = base_queue_member_message(
            member_id,
            sender_role,
            subject,
            message,
            actor_id=actor_id,
        )
        db = db_api.load_db()
        delivery = queue_member_event_email(
            db,
            member_id=member_id,
            kind="app_message",
            subject=subject,
            message=message,
            actor_id=actor_id or sender_role,
            source="admin_member_message",
            source_id=(result or {}).get("id", ""),
            dedupe_key=f"app_message|{(result or {}).get('id', '')}",
            append_message=False,
            append_notification=False,
        )
        _annotate_latest(
            db.get("messages", []),
            delivery,
            lambda row: row.get("id") == (result or {}).get("id"),
        )
        _annotate_latest(
            db.get("notifications", []),
            delivery,
            lambda row: row.get("kind") == "app_message"
            and row.get("user_id") == member_id,
        )
        db_api.save_db(db)
        if isinstance(result, dict):
            result.update(_delivery_fields(delivery))
        return result

    db_api.queue_member_message = queue_member_message

    base_daily_log_reminder = db_api.queue_daily_log_reminder

    def queue_daily_log_reminder(member_id, actor="admin"):
        result = base_daily_log_reminder(member_id, actor=actor)
        db = db_api.load_db()
        delivery = queue_member_event_email(
            db,
            member_id=member_id,
            kind="daily_log_reminder",
            subject="A gentle reminder from HealthyMe",
            message=(
                "This is a friendly reminder to complete your Daily Log. "
                "Keeping it updated helps your wellness team review your progress accurately."
            ),
            actor_id=actor,
            source="daily_log_reminder",
            source_id=db.get("notifications", [])[-1].get("ts", "") if db.get("notifications") else "",
            dedupe_key=(
                f"daily_log_reminder|{member_id}|"
                f"{db.get('notifications', [])[-1].get('ts', '') if db.get('notifications') else ''}"
            ),
            append_message=True,
            append_notification=False,
        )
        _annotate_latest(
            db.get("notifications", []),
            delivery,
            lambda row: row.get("kind") == "daily_log_reminder"
            and row.get("user_id") == member_id,
        )
        db_api.save_db(db)
        return result

    db_api.queue_daily_log_reminder = queue_daily_log_reminder

    base_save_note = db_api.save_daily_log_supervision_note

    def save_daily_log_supervision_note(member_id, note, actor_id="nutritionist", log_date=None):
        result = base_save_note(
            member_id,
            note,
            actor_id=actor_id,
            log_date=log_date,
        )
        if not result:
            return result
        date_text = str(log_date or result.get("log_date") or "").strip()
        subject = "A note from your HealthyMe nutritionist"
        if date_text:
            subject += f" — {date_text}"
        db = db_api.load_db()
        delivery = queue_member_event_email(
            db,
            member_id=member_id,
            kind="nutritionist_note",
            subject=subject,
            message=str(note or "").strip(),
            actor_id=actor_id,
            source="daily_log_supervision_note",
            source_id=result.get("id", ""),
            dedupe_key=f"nutritionist_note|{result.get('id', '')}",
            append_message=False,
            append_notification=False,
        )
        _annotate_latest(
            db.get("messages", []),
            delivery,
            lambda row: row.get("note_id") == result.get("id"),
        )
        _annotate_latest(
            db.get("notifications", []),
            delivery,
            lambda row: row.get("kind") == "nutritionist_note"
            and row.get("user_id") == member_id
            and row.get("log_date", "") == date_text,
        )
        db_api.save_db(db)
        if isinstance(result, dict):
            result.update(_delivery_fields(delivery))
        return result

    db_api.save_daily_log_supervision_note = save_daily_log_supervision_note

    base_resource_assignments = db_api.save_resource_assignments

    def save_resource_assignments(member_id, resource_type, item_ids, actor="admin"):
        result = base_resource_assignments(
            member_id,
            resource_type,
            item_ids,
            actor=actor,
        )
        clean_ids = [str(value).strip() for value in item_ids if str(value).strip()]
        resource_label = "meal resources" if resource_type == "recipes" else "exercise resources"
        subject = (
            "Your HealthyMe meal resources have been updated"
            if resource_type == "recipes"
            else "Your HealthyMe exercise resources have been updated"
        )
        db = db_api.load_db()
        delivery = queue_member_event_email(
            db,
            member_id=member_id,
            kind=f"{resource_type}_allocated",
            subject=subject,
            message=(
                f"Your wellness team has assigned {len(clean_ids)} {resource_label} to your HealthyMe plan. "
                "Please sign in to review the latest guidance."
            ),
            actor_id=actor,
            source="resource_assignment",
            source_id=resource_type,
            details={"Assigned items": len(clean_ids)},
            dedupe_key=f"resource_assignment|{member_id}|{resource_type}|{'|'.join(sorted(clean_ids))}",
            append_message=True,
            append_notification=False,
        )
        _annotate_latest(
            db.get("notifications", []),
            delivery,
            lambda row: row.get("kind") == f"{resource_type}_allocated"
            and row.get("user_id") == member_id,
        )
        db_api.save_db(db)
        return result

    db_api.save_resource_assignments = save_resource_assignments

    base_assign_package = db_api.assign_member_package_v1024b14

    def assign_member_package_v1024b14(member_id, package_id, actor_id="admin"):
        result = base_assign_package(member_id, package_id, actor_id=actor_id)
        if not result or result.get("error"):
            return result
        db = db_api.load_db()
        inclusions = [
            key
            for key, value in (result.get("inclusions", {}) or {}).items()
            if value
        ]
        delivery = queue_member_event_email(
            db,
            member_id=member_id,
            kind="package_assigned",
            subject="Your HealthyMe package has been assigned",
            message=(
                f"Your {result.get('package_name') or 'HealthyMe package'} is now active. "
                "You can review the package and session balance in My Schedule."
            ),
            actor_id=actor_id,
            source="member_package",
            source_id=result.get("id", ""),
            details={
                "Package": result.get("package_name", ""),
                "Sessions": result.get("session_count", ""),
                "Cost per session": (
                    f"{result.get('currency', 'INR')} {float(result.get('cost_per_session', 0) or 0):,.2f}"
                ),
                "Inclusions": _friendly_list(inclusions),
            },
            dedupe_key=f"package_assigned|{result.get('id', '')}",
            append_message=True,
            append_notification=True,
        )
        db_api.save_db(db)
        result.update(_delivery_fields(delivery))
        return result

    db_api.assign_member_package_v1024b14 = assign_member_package_v1024b14

    base_recommendation_share = db_api.save_recommendation_share

    def save_recommendation_share(member_id, share_data, actor_id="admin", publish=False):
        result = base_recommendation_share(
            member_id,
            share_data,
            actor_id=actor_id,
            publish=publish,
        )
        if not publish or not result:
            return result
        db = db_api.load_db()
        sections = []
        if any((row or {}).get("recipe_id") for row in result.get("meal_plan", []) or []):
            sections.append("Meal plan")
        if any((row or {}).get("exercise_id") for row in result.get("exercise_plan", []) or []):
            sections.append("Exercise plan")
        if any(
            (row or {}).get("supplement_ids")
            or (row or {}).get("supplement_details")
            for row in result.get("supplement_plan", []) or []
        ):
            sections.append("Supplement plan")
        delivery = queue_member_event_email(
            db,
            member_id=member_id,
            kind="recommendations_shared",
            subject="Your HealthyMe recommendations are ready",
            message=(
                "Your wellness team has published your latest recommendations. "
                "Please sign in to review Today's Plan and your Weekly Plan."
            ),
            actor_id=actor_id,
            source="recommendation_share",
            source_id=result.get("id", ""),
            details={
                "Plan period": (
                    f"{result.get('start_date', '')} to {result.get('end_date', '')}"
                    if result.get("start_date") or result.get("end_date")
                    else ""
                ),
                "Plan sections": _friendly_list(sections),
            },
            dedupe_key=f"recommendations_shared|{result.get('id', '')}|{result.get('published_at', '')}",
            append_message=True,
            append_notification=False,
        )
        _annotate_latest(
            db.get("notifications", []),
            delivery,
            lambda row: row.get("kind") == "recommendations_shared"
            and row.get("user_id") == member_id,
        )
        db_api.save_db(db)
        if isinstance(result, dict):
            result.update(_delivery_fields(delivery))
        return result

    db_api.save_recommendation_share = save_recommendation_share

    def _supplement_event(record: dict, action: str, actor_id: object) -> dict[str, Any]:
        member_id = record.get("member_id", "")
        name = record.get("supplement_name") or "Supplement"
        if action == "assigned":
            subject = "Your HealthyMe supplement plan has been updated"
            message = f"{name} has been added to your supplement plan. Please review the dosage and instructions in HealthyMe."
        elif action == "stopped":
            subject = "A supplement in your HealthyMe plan has been stopped"
            message = f"{name} has been marked as stopped in your supplement plan. Please review the update in HealthyMe."
        else:
            subject = "Your HealthyMe supplement guidance has been updated"
            message = f"The guidance for {name} has been updated. Please review the latest details in HealthyMe."
        db = db_api.load_db()
        delivery = queue_member_event_email(
            db,
            member_id=member_id,
            kind=f"supplement_{action}",
            subject=subject,
            message=message,
            actor_id=actor_id,
            source="member_supplement",
            source_id=record.get("id", ""),
            details={
                "Supplement": name,
                "Dosage": record.get("dosage", ""),
                "Frequency": record.get("frequency", ""),
                "Timing": record.get("timing", ""),
                "Start date": record.get("start_date", ""),
                "End/stop date": record.get("stop_date") or record.get("end_date", ""),
            },
            dedupe_key=(
                f"supplement|{action}|{record.get('id', '')}|"
                f"{record.get('updated_at', '') or record.get('created_at', '')}"
            ),
            append_message=True,
            append_notification=True,
        )
        db_api.save_db(db)
        if isinstance(record, dict):
            record.update(_delivery_fields(delivery))
        return record

    base_add_supplement = db_api.add_member_supplement

    def add_member_supplement(member_id, data, actor_id="admin"):
        record = base_add_supplement(member_id, data, actor_id=actor_id)
        return _supplement_event(record, "assigned", actor_id)

    db_api.add_member_supplement = add_member_supplement

    base_update_supplement = db_api.update_member_supplement

    def update_member_supplement(supplement_id, updates, actor_id="admin"):
        record = base_update_supplement(supplement_id, updates, actor_id=actor_id)
        return _supplement_event(record, "updated", actor_id)

    db_api.update_member_supplement = update_member_supplement

    base_stop_supplement = db_api.stop_member_supplement

    def stop_member_supplement(supplement_id, stop_date=None, stop_reason="", actor_id="admin"):
        record = base_stop_supplement(
            supplement_id,
            stop_date=stop_date,
            stop_reason=stop_reason,
            actor_id=actor_id,
        )
        return _supplement_event(record, "stopped", actor_id)

    db_api.stop_member_supplement = stop_member_supplement

    # Wrapped after schedule_timezone is loaded so cancellation emails can use the
    # same member-local time context as the accepted scheduling engine.


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
    return {
        "Session": row.get("title") or row.get("schedule_type") or "Scheduled session",
        "Date": member_view.get("date_label") or row.get("schedule_date", ""),
        "Time": member_view.get("time_window")
        or " - ".join(
            value
            for value in [row.get("start_time", ""), row.get("end_time", "")]
            if value
        ),
        "Timezone": member_view.get("timezone_name") or row.get("member_timezone_name", ""),
        "Mode": row.get("mode", ""),
        "Link/location": row.get("location_or_link", ""),
    }


def _install_schedule_wrappers(db_api, schedule_module) -> None:
    if getattr(schedule_module, "_hm_member_email_wrappers_installed", False):
        return
    schedule_module._hm_member_email_wrappers_installed = True

    base_status_update = db_api.update_member_schedule_status

    def update_member_schedule_status(schedule_id, status, actor_id="admin"):
        result = base_status_update(schedule_id, status, actor_id=actor_id)
        if not result or str(status).lower() != "cancelled":
            return result
        db = db_api.load_db()
        delivery = queue_member_event_email(
            db,
            member_id=result.get("member_id", ""),
            kind="schedule_cancelled",
            subject="Your HealthyMe session has been cancelled",
            message=(
                f"Your session, {result.get('title') or 'Scheduled session'}, has been cancelled. "
                "Please contact your HealthyMe team if a replacement session is required."
            ),
            actor_id=actor_id,
            source="schedule",
            source_id=result.get("id", ""),
            email_to=result.get("member_email", ""),
            details=_schedule_details(schedule_module, result),
            dedupe_key=f"schedule_cancelled|{result.get('id', '')}|{result.get('cancelled_at', '')}",
            append_message=True,
            append_notification=True,
        )
        db_api.save_db(db)
        result.update(_delivery_fields(delivery))
        return result

    db_api.update_member_schedule_status = update_member_schedule_status

    base_create_schedule = schedule_module.create_timezone_aware_member_schedule

    def create_timezone_aware_member_schedule(**kwargs):
        result = base_create_schedule(**kwargs)
        if not result or result.get("error"):
            return result
        db = db_api.load_db()
        details = _schedule_details(schedule_module, result)
        delivery = queue_member_event_email(
            db,
            member_id=result.get("member_id") or kwargs.get("member_id", ""),
            kind="schedule_created",
            subject="Your HealthyMe session is scheduled",
            message=(
                f"Your session, {result.get('title') or 'Scheduled session'}, has been scheduled. "
                "Please review the date, time and joining details below."
            ),
            actor_id=kwargs.get("practitioner_id", "admin"),
            source="schedule",
            source_id=result.get("id", ""),
            email_to=result.get("member_email", ""),
            details=details,
            dedupe_key=f"schedule_created|{result.get('id', '')}",
            append_message=False,
            append_notification=False,
        )
        _annotate_latest(
            db.get("messages", []),
            delivery,
            lambda row: row.get("schedule_id") == result.get("id")
            and row.get("source") == "schedule",
        )
        _annotate_latest(
            db.get("notifications", []),
            delivery,
            lambda row: row.get("schedule_id") == result.get("id")
            and row.get("kind") == "schedule_created",
        )
        db_api.save_db(db)
        result.update(_delivery_fields(delivery))
        return result

    schedule_module.create_timezone_aware_member_schedule = (
        create_timezone_aware_member_schedule
    )

    base_request_reschedule = schedule_module.request_timezone_aware_reschedule

    def request_timezone_aware_reschedule(**kwargs):
        result = base_request_reschedule(**kwargs)
        if not result or result.get("error"):
            return result
        member_id = result.get("member_id") or kwargs.get("member_id", "")
        db = db_api.load_db()
        requested = result.get("_requested_time_context", {}) or {}
        member_view = requested.get("member", {}) or {}
        delivery = queue_member_event_email(
            db,
            member_id=member_id,
            kind="reschedule_request_received",
            subject="We received your HealthyMe reschedule request",
            message=(
                f"We have received your request to reschedule {result.get('current_title') or 'your session'}. "
                "Your wellness team will review it and send you an update."
            ),
            actor_id=member_id,
            source="reschedule_request",
            source_id=result.get("id", ""),
            email_to=result.get("member_email", ""),
            details={
                "Requested date": member_view.get("date_label") or result.get("requested_date", ""),
                "Requested time": member_view.get("time_window")
                or " - ".join(
                    value
                    for value in [
                        result.get("requested_start_time", ""),
                        result.get("requested_end_time", ""),
                    ]
                    if value
                ),
                "Timezone": member_view.get("timezone_name") or result.get("member_timezone_name", ""),
            },
            dedupe_key=f"reschedule_request_received|{result.get('id', '')}",
            append_message=True,
            append_notification=True,
        )
        db_api.save_db(db)
        result.update(_delivery_fields(delivery))
        return result

    schedule_module.request_timezone_aware_reschedule = (
        request_timezone_aware_reschedule
    )

    base_decide_reschedule = schedule_module.decide_timezone_aware_reschedule_request

    def decide_timezone_aware_reschedule_request(
        request_id,
        decision,
        *,
        admin_note="",
        actor_id="admin",
    ):
        result = base_decide_reschedule(
            request_id,
            decision,
            admin_note=admin_note,
            actor_id=actor_id,
        )
        if not result or result.get("error"):
            return result
        request = result.get("request", {}) or {}
        normalized = str(request.get("status") or decision).lower()
        approved = normalized == "approved"
        new_schedule = result.get("new_schedule") or {}
        db = db_api.load_db()
        details = _schedule_details(schedule_module, new_schedule) if approved else {
            "Session": request.get("current_title", ""),
            "Admin note": request.get("admin_note", ""),
        }
        subject = (
            "Your HealthyMe reschedule request is approved"
            if approved
            else "Update on your HealthyMe reschedule request"
        )
        message = (
            f"Your request to reschedule {request.get('current_title') or 'your session'} has been approved. "
            "Please review the revised session details below."
            if approved
            else f"Your request to reschedule {request.get('current_title') or 'your session'} could not be approved. "
            "The original session remains unchanged unless your HealthyMe team contacts you separately."
        )
        delivery = queue_member_event_email(
            db,
            member_id=request.get("member_id", ""),
            kind=f"reschedule_{normalized}",
            subject=subject,
            message=message,
            actor_id=actor_id,
            source="reschedule",
            source_id=request_id,
            email_to=request.get("member_email", ""),
            details=details,
            dedupe_key=f"reschedule_{normalized}|{request_id}|{request.get('decided_at', '')}",
            append_message=False,
            append_notification=False,
        )
        _annotate_latest(
            db.get("messages", []),
            delivery,
            lambda row: row.get("reschedule_request_id") == str(request_id),
        )
        _annotate_latest(
            db.get("notifications", []),
            delivery,
            lambda row: row.get("reschedule_request_id") == str(request_id)
            and str(row.get("kind", "")).startswith("reschedule_"),
        )
        db_api.save_db(db)
        result["email_delivery"] = delivery
        return result

    schedule_module.decide_timezone_aware_reschedule_request = (
        decide_timezone_aware_reschedule_request
    )


def _install_assessment_wrappers(db_api, assessment_module) -> None:
    if getattr(assessment_module, "_hm_member_email_wrappers_installed", False):
        return
    assessment_module._hm_member_email_wrappers_installed = True
    base_create_request = assessment_module.create_reassessment_request

    def create_reassessment_request(
        member_id,
        requested_pages,
        due_date="",
        admin_note="",
        admin_id="admin",
    ):
        instance, created = base_create_request(
            member_id,
            requested_pages,
            due_date=due_date,
            admin_note=admin_note,
            admin_id=admin_id,
        )
        if not created:
            return instance, created
        labels = [assessment_module._page_title(page) for page in instance.get("requested_pages", [])]
        db = db_api.load_db()
        delivery = queue_member_event_email(
            db,
            member_id=member_id,
            kind="member_reassessment_request",
            subject="A new HealthyMe task is ready",
            message=(
                f"Your wellness team has assigned a new task: {_friendly_list(labels)}. "
                "Please complete it within HealthyMe and submit it for review."
            ),
            actor_id=admin_id,
            source="assessment_instance",
            source_id=instance.get("instance_id", ""),
            details={
                "Requested tasks": _friendly_list(labels),
                "Due date": instance.get("due_date", "") or "Not specified",
                "Note from your wellness team": instance.get("admin_note", ""),
            },
            dedupe_key=f"member_reassessment_request|{instance.get('instance_id', '')}",
            append_message=True,
            append_notification=False,
        )
        _annotate_latest(
            db.get("notifications", []),
            delivery,
            lambda row: row.get("kind") == "member_reassessment_request"
            and row.get("user_id") == member_id,
        )
        db_api.save_db(db)
        if isinstance(instance, dict):
            instance.update(_delivery_fields(delivery))
        return instance, created

    assessment_module.create_reassessment_request = create_reassessment_request


def _install_profile_wrappers(db_api, profile_module) -> None:
    if getattr(profile_module, "_hm_member_email_wrappers_installed", False):
        return
    profile_module._hm_member_email_wrappers_installed = True
    base_activate_profile = profile_module.activate_profile

    def activate_profile(profile, confirm_text):
        success, message = base_activate_profile(profile, confirm_text)
        if not success:
            return success, message
        member_id = str(profile.get("assigned_member_id") or "").strip()
        profile_id = str(profile.get("id") or "").strip()
        sections = []
        try:
            ok, _detail, items, _load_message = profile_module.load_profile_detail(profile_id)
            if ok:
                item_types = {str(item.get("item_type") or "").strip() for item in items}
                if "meal" in item_types:
                    sections.append("Meal plan")
                if "exercise" in item_types:
                    sections.append("Exercise plan")
                if "supplement" in item_types:
                    sections.append("Supplement plan")
        except Exception:
            pass
        db = db_api.load_db()
        delivery = queue_member_event_email(
            db,
            member_id=member_id,
            kind="recommendation_profile_activated",
            subject="Your HealthyMe recommendation profile is ready",
            message=(
                f"Your {profile.get('profile_name') or 'recommendation profile'} has been activated. "
                "Please sign in to review your latest personalized guidance."
            ),
            actor_id=profile_module._clean(profile_module.st.session_state.get("user_id")) or "admin",
            source="recommendation_profile",
            source_id=profile_id,
            details={
                "Profile": profile.get("profile_name", ""),
                "Start date": profile.get("start_date", ""),
                "Includes": _friendly_list(sections),
            },
            dedupe_key=f"recommendation_profile_activated|{profile_id}|{profile.get('updated_at', '')}",
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

    profile_module.activate_profile = activate_profile


def install_member_email_notifications() -> None:
    global _INSTALLED
    if _INSTALLED:
        return
    _INSTALLED = True

    from components import db as db_api
    from components import assessment_instances as assessment_module
    from components import profile_publish_control as profile_module
    from components import schedule_timezone as schedule_module

    _install_db_wrappers(db_api)
    _install_schedule_wrappers(db_api, schedule_module)
    _install_assessment_wrappers(db_api, assessment_module)
    _install_profile_wrappers(db_api, profile_module)
