from __future__ import annotations

import streamlit as st

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
_CREATE_RESET_PENDING = "_hm_schedule_create_reset_pending"
_MEMBER_RESET_PENDING = "_hm_schedule_member_reset_pending"
_ADMIN_RESET_PENDING = "_hm_schedule_admin_reset_pending"


def _pending_keys(value) -> tuple[str, ...]:
    if isinstance(value, (list, tuple, set)):
        return tuple(str(key) for key in value if str(key))
    return ()


def _consume_pending_resets() -> None:
    """Clear completed transaction widgets before this rerun creates them again."""

    if st.session_state.pop(_CREATE_RESET_PENDING, False):
        clear_widget_state(_CREATE_KEYS)
    clear_widget_state(
        _pending_keys(st.session_state.pop(_MEMBER_RESET_PENDING, ()))
    )
    clear_widget_state(
        _pending_keys(st.session_state.pop(_ADMIN_RESET_PENDING, ()))
    )


def _install_prominent_success_and_pending_reset(schedule_timezone_ui) -> None:
    base_styles = schedule_timezone_ui._inject_schedule_styles

    def styles_with_sprint1_retest_fixes() -> None:
        # _inject_schedule_styles runs after set_page_config/topbar and before any
        # Scheduling form widgets. This is the safe point to clear completed values.
        _consume_pending_resets()
        base_styles()
        st.markdown(
            """
            <style id="hm-schedule-success-prominence-v1">
            .hm-flash-ok{
              border:2px solid #0F766E!important;
              background:linear-gradient(135deg,#E8F8EF 0%,#F4FFF8 100%)!important;
              color:#064E3B!important;
              border-radius:16px!important;
              padding:1rem 1.10rem!important;
              margin:.70rem 0 1rem 0!important;
              font-size:1.04rem!important;
              font-weight:900!important;
              line-height:1.35!important;
              box-shadow:0 10px 24px rgba(15,118,110,.14)!important;
            }
            .hm-flash-ok::before{
              content:"✓";
              display:inline-flex;
              align-items:center;
              justify-content:center;
              width:1.55rem;
              height:1.55rem;
              margin-right:.55rem;
              border-radius:999px;
              background:#0F766E;
              color:#FFFFFF;
              font-size:.92rem;
              font-weight:950;
              vertical-align:middle;
            }
            </style>
            """,
            unsafe_allow_html=True,
        )

    schedule_timezone_ui._inject_schedule_styles = styles_with_sprint1_retest_fixes


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
            # The current widgets already exist in this run. Mark the reset for the
            # next rerun so Streamlit cannot restore the submitted frontend values.
            st.session_state[_CREATE_RESET_PENDING] = True
        return result

    def request_and_clear(**kwargs):
        result = base_request(**kwargs)
        if result and not result.get("error"):
            schedule_id = str(kwargs.get("schedule_id") or "")
            st.session_state[_MEMBER_RESET_PENDING] = (
                f"hm_tz_reschedule_date_{schedule_id}",
                f"hm_tz_reschedule_start_{schedule_id}",
                f"hm_tz_reschedule_end_{schedule_id}",
                f"hm_tz_reschedule_reason_{schedule_id}",
                f"hm_tz_reschedule_confirm_{schedule_id}",
                f"hm_tz_show_reschedule_{schedule_id}",
            )
        return result

    def decide_and_clear(request_id, decision, **kwargs):
        result = base_decide(request_id, decision, **kwargs)
        if result and not result.get("error"):
            st.session_state[_ADMIN_RESET_PENDING] = (
                f"hm_tz_reschedule_note_{request_id}",
            )
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
    _install_prominent_success_and_pending_reset(schedule_timezone_ui)
