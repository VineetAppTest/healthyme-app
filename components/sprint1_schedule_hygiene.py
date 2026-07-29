from __future__ import annotations

from components.form_hygiene import clear_widget_state


_CREATE_KEYS = (
    "hm_tz_schedule_type",
    "hm_tz_schedule_title",
    "hm_tz_schedule_date",
    "hm_tz_schedule_start",
    "hm_tz_schedule_end",
    "hm_tz_schedule_mode",
    "hm_tz_schedule_location",
    "hm_tz_schedule_notes",
    "hm_package_schedule_limit_override",
    "hm_package_schedule_limit_override_reason",
)


def install_sprint1_schedule_hygiene(schedule_timezone_ui) -> None:
    """Apply successful-submit clearing and Admin latest-first ordering."""

    if getattr(schedule_timezone_ui, "_hm_sprint1_schedule_hygiene_installed", False):
        return
    schedule_timezone_ui._hm_sprint1_schedule_hygiene_installed = True

    base_create = schedule_timezone_ui.create_timezone_aware_member_schedule
    base_request = schedule_timezone_ui.request_timezone_aware_reschedule
    base_decide = schedule_timezone_ui.decide_timezone_aware_reschedule_request
    base_rows = schedule_timezone_ui.timezone_enriched_schedule_rows

    def create_and_clear(**kwargs):
        result = base_create(**kwargs)
        if result and not result.get("error"):
            clear_widget_state(_CREATE_KEYS)
        return result

    def request_and_clear(**kwargs):
        result = base_request(**kwargs)
        if result and not result.get("error"):
            schedule_id = str(kwargs.get("schedule_id") or "")
            clear_widget_state(
                (
                    f"hm_tz_reschedule_date_{schedule_id}",
                    f"hm_tz_reschedule_start_{schedule_id}",
                    f"hm_tz_reschedule_end_{schedule_id}",
                    f"hm_tz_reschedule_reason_{schedule_id}",
                    f"hm_tz_reschedule_confirm_{schedule_id}",
                    f"hm_tz_show_reschedule_{schedule_id}",
                )
            )
        return result

    def decide_and_clear(request_id, decision, **kwargs):
        result = base_decide(request_id, decision, **kwargs)
        if result and not result.get("error"):
            clear_widget_state((f"hm_tz_reschedule_note_{request_id}",))
        return result

    def latest_first_rows(member_id, *, include_cancelled=True, limit=50):
        rows = base_rows(
            member_id,
            include_cancelled=include_cancelled,
            limit=0,
        )
        rows.sort(
            key=lambda row: (
                str((row.get("_time_context") or {}).get("start_at_utc") or ""),
                str(row.get("created_at") or ""),
            ),
            reverse=True,
        )
        return rows[:limit] if limit else rows

    schedule_timezone_ui.create_timezone_aware_member_schedule = create_and_clear
    schedule_timezone_ui.request_timezone_aware_reschedule = request_and_clear
    schedule_timezone_ui.decide_timezone_aware_reschedule_request = decide_and_clear
    schedule_timezone_ui.timezone_enriched_schedule_rows = latest_first_rows
