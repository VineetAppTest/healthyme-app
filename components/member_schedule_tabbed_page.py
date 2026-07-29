from __future__ import annotations

import datetime

import streamlit as st


def render_tabbed_member_schedule_page(schedule_ui) -> None:
    """Render the accepted Member My Schedule workflow in three tabs.

    The schedule/package functions remain owned by ``schedule_timezone_ui`` so the
    existing acknowledgement, reschedule, timezone and package contracts are reused
    without duplication or mutation.
    """

    st.set_page_config(
        page_title="My Schedule",
        page_icon="💚",
        layout="wide",
        initial_sidebar_state="collapsed",
    )
    schedule_ui.inject_global_styles()
    schedule_ui.apply_luxe_theme()
    schedule_ui.require_member()
    user_id = st.session_state.get("user_id")
    schedule_ui.utility_logout_bar()
    schedule_ui.topbar(
        "My Schedule",
        "View your package, upcoming sessions and session usage.",
        "Member content",
    )
    schedule_ui._inject_schedule_styles()
    member_tz = schedule_ui.member_timezone_name(user_id, persist=True)

    package_tab, upcoming_tab, usage_tab = st.tabs(
        ["Package Subscribed", "Upcoming Schedule", "Session Usage"]
    )

    with package_tab:
        schedule_ui._render_package(user_id, member_view=True)

    with upcoming_tab:
        st.markdown("<div class='hm-schedule-section'>", unsafe_allow_html=True)
        st.markdown(
            "<div class='hm-schedule-heading'>Upcoming Schedule</div>",
            unsafe_allow_html=True,
        )
        st.markdown(
            f"<div class='hm-schedule-sub'>Your primary date/time is shown in member local time: {schedule_ui._safe(member_tz)}. Practitioner local time is shown alongside when different.</div>",
            unsafe_allow_html=True,
        )
        schedule_ui.queue_timezone_aware_schedule_acknowledgement_reminders(user_id)
        rows = schedule_ui.list_timezone_aware_member_schedules(user_id, limit=30)
        if not rows:
            st.info("No upcoming schedule has been created for you yet.")
        else:
            for row in rows:
                status = row.get("status", "scheduled")
                context = row.get("_time_context") or {}
                st.markdown(
                    "<div class='hm-schedule-card'>"
                    f"<div class='hm-schedule-title'>{schedule_ui._safe(row.get('title') or 'Scheduled session')}<span class='hm-schedule-pill'>{schedule_ui._safe(schedule_ui.schedule_display_status_label_v104b11(row))}</span></div>"
                    f"{schedule_ui._time_preview_html(context, member_first=True)}"
                    f"<div class='hm-schedule-line'>Mode: {schedule_ui._safe(row.get('mode') or '-')} · Link/location: {schedule_ui._safe(row.get('location_or_link') or '-')}</div>"
                    f"<div class='hm-schedule-line'>Notes: {schedule_ui._safe(row.get('notes') or '-')}</div>"
                    "</div>",
                    unsafe_allow_html=True,
                )
                action_col_1, action_col_2 = st.columns(2, gap="medium")
                with action_col_1:
                    if status == "scheduled":
                        if st.button(
                            "Acknowledge schedule",
                            key=f"hm_tz_ack_schedule_{row.get('id')}",
                            use_container_width=True,
                        ):
                            schedule_ui.acknowledge_member_schedule(row.get("id"), user_id)
                            st.success("Schedule acknowledged.")
                            st.rerun()
                with action_col_2:
                    can_request = (
                        status in ["scheduled", "acknowledged"]
                        and row.get("reschedule_request_status") != "pending"
                    )
                    if st.button(
                        "Request Reschedule",
                        key=f"hm_tz_open_reschedule_{row.get('id')}",
                        use_container_width=True,
                        disabled=not can_request,
                    ):
                        state_key = f"hm_tz_show_reschedule_{row.get('id')}"
                        st.session_state[state_key] = not st.session_state.get(
                            state_key, False
                        )
                        st.rerun()
                if row.get("reschedule_request_status") == "pending":
                    st.caption("A reschedule request is already pending admin review.")

                state_key = f"hm_tz_show_reschedule_{row.get('id')}"
                if st.session_state.get(state_key, False):
                    with st.container(border=True):
                        st.markdown("#### Request reschedule")
                        st.caption(
                            f"Enter your preferred slot in your local timezone: {member_tz}."
                        )
                        preferred_date = st.date_input(
                            "Preferred new date",
                            value=schedule_ui.today_in_timezone(member_tz),
                            key=f"hm_tz_reschedule_date_{row.get('id')}",
                        )
                        t_col1, t_col2 = st.columns(2, gap="medium")
                        with t_col1:
                            preferred_start = st.time_input(
                                "Preferred start time",
                                value=datetime.time(10, 0),
                                key=f"hm_tz_reschedule_start_{row.get('id')}",
                            )
                        with t_col2:
                            preferred_end = st.time_input(
                                "Preferred end time",
                                value=datetime.time(10, 30),
                                key=f"hm_tz_reschedule_end_{row.get('id')}",
                            )
                        reason = st.text_area(
                            "Reason / note",
                            placeholder="Optional: mention why you are requesting a new slot",
                            key=f"hm_tz_reschedule_reason_{row.get('id')}",
                            height=80,
                        )
                        requested_preview = {}
                        request_error = ""
                        try:
                            requested_preview = schedule_ui.build_dual_time_context(
                                preferred_date,
                                preferred_start,
                                preferred_end,
                                source_timezone_name=member_tz,
                                member_timezone=member_tz,
                                practitioner_timezone=context.get(
                                    "practitioner_timezone_name"
                                )
                                or member_tz,
                            )
                            if not schedule_ui.context_start_is_future(
                                requested_preview
                            ):
                                request_error = (
                                    "Choose a future member-local date and time."
                                )
                        except ValueError as exc:
                            request_error = str(exc)
                        if request_error:
                            st.error(request_error)
                        if requested_preview:
                            schedule_ui._render_time_preview(
                                requested_preview,
                                "Timezone confirmation for your requested slot",
                                member_first=True,
                            )
                        within_24 = schedule_ui.schedule_within_hours(row, 24)
                        st.markdown(
                            f"<div class='hm-policy-box'>{schedule_ui._safe(schedule_ui.reschedule_policy_text_v1012(within_24))}</div>",
                            unsafe_allow_html=True,
                        )
                        confirm_key = f"hm_tz_reschedule_confirm_{row.get('id')}"
                        if within_24:
                            st.checkbox(
                                "I understand that because this is within 24 hours, the current session may still be counted as consumed.",
                                key=confirm_key,
                            )
                        else:
                            st.session_state[confirm_key] = True
                        if st.button(
                            "Submit Reschedule Request",
                            key=f"hm_tz_submit_reschedule_{row.get('id')}",
                            use_container_width=True,
                            disabled=(
                                not st.session_state.get(confirm_key, False)
                                or bool(request_error)
                            ),
                        ):
                            try:
                                req = schedule_ui.request_timezone_aware_reschedule(
                                    schedule_id=row.get("id"),
                                    member_id=user_id,
                                    requested_date=preferred_date,
                                    requested_start_time=preferred_start,
                                    requested_end_time=preferred_end,
                                    reason=reason,
                                )
                            except ValueError as exc:
                                req = {"error": str(exc)}
                            if req.get("error"):
                                st.error(req.get("error"))
                            else:
                                st.success(
                                    "Reschedule request submitted with both local times for admin review."
                                )
                                st.session_state[state_key] = False
                                st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    with usage_tab:
        schedule_ui._render_member_ledger(user_id, member_tz)

    schedule_ui.render_page_nav(
        "My Schedule",
        back_page="pages/02_Member_Home.py",
        dashboard_page="pages/02_Member_Home.py",
        show_evaluation=False,
        show_dashboard=True,
        location="bottom",
    )
    schedule_ui.render_back_to_top()
