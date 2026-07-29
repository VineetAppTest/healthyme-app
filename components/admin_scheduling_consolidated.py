from __future__ import annotations

import datetime as dt
import html
from typing import Any

import streamlit as st

from components.admin_role_model import current_user_is_admin
from components.admin_scheduling_timezone_selector import (
    _TIMEZONE_SEARCH_KEY,
    _friendly_timezone_label,
    _inject_timezone_selector_css,
    _match_location_timezones,
    _query_widget_key,
    _render_timezone_search_status,
    _safe_timezone_options,
)
from components.db import (
    list_members,
    reschedule_policy_text_v1012,
    schedule_display_status_label_v104b11,
    update_member_schedule_status,
)
from components.guards import require_admin
from components.member_timezone import member_timezone_name
from components.package_hardening import member_session_ledger, schedule_capacity
from components.schedule_timezone import (
    build_dual_time_context,
    create_timezone_aware_member_schedule,
    decide_timezone_aware_reschedule_request,
    list_timezone_aware_admin_open_schedules,
    list_timezone_aware_reschedule_requests,
    persist_practitioner_timezone,
    practitioner_timezone_name,
    timezone_enriched_schedule_rows,
    timezone_options,
    today_in_timezone,
)
from components.ui_common import (
    apply_luxe_theme,
    inject_global_styles,
    render_back_to_top,
    topbar,
    utility_logout_bar,
)


_SECTION_KEY = "hm_admin_schedule_workspace"
_CREATE_VERSION_KEY = "hm_admin_schedule_create_version"
_CREATE_CLEANUP_KEY = "hm_admin_schedule_create_cleanup_version"
_FLASH_KEY = "hm_admin_schedule_flash"
_SELECTED_TIMEZONE_KEY = "hm_admin_schedule_selected_practitioner_timezone"

_SECTIONS = (
    ("create", "Create Schedule"),
    ("status", "Schedule Status"),
    ("reschedule", "Reschedule Status"),
    ("ledger", "Session Ledger"),
)


def _text(value: object) -> str:
    return str(value or "").strip()


def _safe(value: object) -> str:
    return html.escape(_text(value))


def _money(value: object, currency: object = "INR") -> str:
    try:
        amount = float(value or 0)
    except Exception:
        amount = 0.0
    return f"{_text(currency) or 'INR'} {amount:,.2f}"


def _inject_styles() -> None:
    _inject_timezone_selector_css()
    st.markdown(
        """
<style id="hm-admin-scheduling-consolidated-v1">
section.main > div.block-container,.main .block-container,[data-testid="stAppViewBlockContainer"],.stMainBlockContainer,.block-container{max-width:1180px!important;padding-top:.72rem!important;}
.hm-sched-nav-row{margin:.1rem 0 .8rem}.hm-sched-context-note{color:#64748B;font-size:.80rem;font-weight:650;margin:.3rem 0 .75rem}
.hm-sched-workspace{margin:.3rem 0 .9rem}.hm-sched-section-title{color:#064E3B;font-size:1.12rem;font-weight:950;margin:0 0 .2rem}.hm-sched-section-sub{color:#64748B;font-size:.84rem;font-weight:650;margin:0 0 .75rem}
.hm-sched-time{border:1px solid #D7C28D;background:#FFFDF8;border-radius:14px;padding:.70rem .82rem;margin:.5rem 0}.hm-sched-time-title{color:#064E3B;font-size:.84rem;font-weight:900;margin-bottom:.25rem}.hm-sched-time-line{color:#334155;font-size:.82rem;font-weight:680;margin:.1rem 0;line-height:1.35}.hm-sched-time-note{color:#8A641D;font-size:.75rem;font-weight:700;margin-top:.28rem}
.hm-sched-capacity{border:1px solid #E3C98E;background:#FFF7E6;border-radius:14px;padding:.72rem .84rem;color:#72551A;font-size:.83rem;font-weight:700;margin:.55rem 0 .7rem}.hm-sched-success{border:2px solid #0F766E;background:linear-gradient(135deg,#E8F8EF 0%,#F4FFF8 100%);color:#064E3B;border-radius:16px;padding:1rem 1.1rem;margin:.2rem 0 .9rem;font-size:1.02rem;font-weight:900;box-shadow:0 10px 24px rgba(15,118,110,.14)}.hm-sched-success b{display:inline-flex;align-items:center;justify-content:center;width:1.55rem;height:1.55rem;margin-right:.5rem;border-radius:999px;background:#0F766E;color:#FFF}
.hm-sched-card-title{color:#064E3B;font-size:.98rem;font-weight:920;margin:0 0 .25rem}.hm-sched-pill{display:inline-flex;padding:.16rem .45rem;border-radius:999px;border:1px solid #D9C28F;background:#FFF7E6;color:#72551A;font-size:.70rem;font-weight:850;margin-left:.3rem}.hm-sched-line{color:#334155;font-size:.82rem;font-weight:650;margin:.12rem 0;line-height:1.4}.hm-sched-muted{color:#64748B;font-size:.76rem;font-weight:620;margin:.1rem 0}.hm-sched-kpis{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:.55rem;margin:.55rem 0 .8rem}.hm-sched-kpi{border:1px solid #E3C98E;background:#FFFDF8;border-radius:14px;padding:.68rem .72rem;color:#64748B;font-size:.72rem;font-weight:760}.hm-sched-kpi b{display:block;color:#064E3B;font-size:1.12rem;margin-top:.14rem}
.st-key-hm_admin_schedule_workspace button{min-height:2.75rem!important;font-weight:850!important}
@media(max-width:900px){.hm-sched-kpis{grid-template-columns:repeat(2,minmax(0,1fr))}}
</style>
""",
        unsafe_allow_html=True,
    )


def _render_return_navigation(location: str) -> None:
    key_suffix = "top" if location == "top" else "bottom"
    c1, c2, spacer = st.columns([1, 1.15, 2.85], gap="small")
    with c1:
        if st.button(
            "← Back",
            key=f"hm_admin_schedule_back_{key_suffix}",
            use_container_width=True,
        ):
            st.switch_page("pages/10_Admin_Dashboard.py")
    with c2:
        if st.button(
            "Admin Dashboard",
            key=f"hm_admin_schedule_dashboard_{key_suffix}",
            use_container_width=True,
        ):
            st.switch_page("pages/10_Admin_Dashboard.py")


def _render_time_context(
    context: dict[str, Any],
    title: str,
    *,
    member_first: bool = False,
) -> None:
    if not context:
        return
    member = dict(context.get("member") or {})
    practitioner = dict(context.get("practitioner") or {})
    if context.get("same_timezone"):
        rows = (("Member & practitioner", member),)
    elif member_first:
        rows = (("Member", member), ("Practitioner", practitioner))
    else:
        rows = (("Practitioner", practitioner), ("Member", member))
    lines = "".join(
        "<div class='hm-sched-time-line'><b>"
        f"{_safe(label)}:</b> {_safe(row.get('date_label'))} · "
        f"{_safe(row.get('time_window'))} · {_safe(row.get('timezone_name'))} "
        f"({_safe(row.get('offset'))})</div>"
        for label, row in rows
    )
    notes: list[str] = []
    if context.get("crosses_party_date_boundary"):
        notes.append("The calendar date differs between the member and practitioner.")
    if context.get("dst_warning"):
        notes.append(_text(context.get("dst_warning")))
    if context.get("legacy_inferred"):
        notes.append(
            "Legacy schedule: the stored date/time has been interpreted in the member timezone."
        )
    note_html = "".join(
        f"<div class='hm-sched-time-note'>{_safe(note)}</div>" for note in notes
    )
    st.markdown(
        "<div class='hm-sched-time'>"
        f"<div class='hm-sched-time-title'>{_safe(title)}</div>"
        f"{lines}{note_html}</div>",
        unsafe_allow_html=True,
    )


def _render_context_selector() -> tuple[str, str, str, str] | None:
    members = list_members()
    if not members:
        st.info("No members are available for scheduling.")
        return None

    with st.container(border=True):
        st.markdown("### Page Context Selector")

        all_timezones = _safe_timezone_options(timezone_options)
        st.text_input(
            "Search practitioner timezone",
            key=_TIMEZONE_SEARCH_KEY,
            placeholder="Type a city, country or timezone",
            help=(
                "HealthyMe compares the entry with supported cities, countries and "
                "IANA timezones, then stores only the selected valid timezone."
            ),
        )
        query = _text(st.session_state.get(_TIMEZONE_SEARCH_KEY))
        matching_timezones, matched_cities = _match_location_timezones(all_timezones)
        selected_timezone = None
        timezone_kwargs: dict[str, Any] = {
            "key": _query_widget_key(query),
            "format_func": lambda timezone_name: _friendly_timezone_label(
                timezone_name,
                matched_cities.get(timezone_name, ""),
            ),
        }
        if not query:
            selected_timezone = st.selectbox(
                "Practitioner scheduling timezone",
                [],
                index=None,
                placeholder="Search by city, country or timezone first",
                **timezone_kwargs,
            )
            _render_timezone_search_status(
                "Enter a city, country or timezone to view city-based choices."
            )
        elif not matching_timezones:
            selected_timezone = st.selectbox(
                "Practitioner scheduling timezone",
                [],
                index=None,
                placeholder="No matching location found",
                **timezone_kwargs,
            )
            _render_timezone_search_status(
                "No matching city, country or timezone found. Practitioner scheduling timezone remains empty."
            )
        else:
            selected_timezone = st.selectbox(
                "Practitioner scheduling timezone",
                matching_timezones,
                index=0 if len(matching_timezones) == 1 else None,
                placeholder=(
                    "Select a city-based timezone"
                    if len(matching_timezones) > 1
                    else None
                ),
                **timezone_kwargs,
            )
            if len(matching_timezones) > 1 and not selected_timezone:
                _render_timezone_search_status(
                    "Multiple matching locations were found. Select the correct city-based timezone."
                )

        member_options = {
            f"{member.get('name', '')} — {member.get('email', '')}": member.get("id")
            for member in members
        }
        selected_member_label = st.selectbox(
            "Select member controlling this page",
            list(member_options.keys()),
            key="hm_admin_schedule_member",
        )
        member_id = _text(member_options.get(selected_member_label))
        member_tz = member_timezone_name(member_id, persist=True)

        practitioner_id = _text(st.session_state.get("user_id")) or "admin"
        if selected_timezone:
            previous = practitioner_timezone_name(practitioner_id, persist=False)
            if selected_timezone != previous:
                persist_practitioner_timezone(practitioner_id, selected_timezone)
            st.session_state[_SELECTED_TIMEZONE_KEY] = selected_timezone
        else:
            st.session_state.pop(_SELECTED_TIMEZONE_KEY, None)

        st.markdown(
            "<div class='hm-sched-context-note'>"
            f"Practitioner timezone: <b>{_safe(selected_timezone or 'Not selected')}</b> · "
            f"Member timezone: <b>{_safe(member_tz)}</b></div>",
            unsafe_allow_html=True,
        )

    if not selected_timezone:
        st.info(
            "Search for and select a practitioner timezone to continue. Back and Dashboard controls remain available above."
        )
        return None

    entry_basis = st.radio(
        "Enter the schedule in",
        ("Practitioner local time", "Member local time"),
        horizontal=True,
        key="hm_admin_schedule_entry_basis",
    )
    source_tz = selected_timezone if entry_basis == "Practitioner local time" else member_tz
    st.caption(
        f"Date and time controls are interpreted in {source_tz}. HealthyMe stores one UTC instant and displays both local views."
    )
    return member_id, member_tz, practitioner_id, source_tz


def _workspace_navigation(member_id: str) -> str:
    open_count = len(list_timezone_aware_admin_open_schedules(member_id, limit=0))
    pending_count = len(
        list_timezone_aware_reschedule_requests(
            member_id=member_id,
            status="pending",
            limit=0,
        )
    )
    current = _text(st.session_state.get(_SECTION_KEY)) or "create"
    valid = {key for key, _label in _SECTIONS}
    if current not in valid:
        current = "create"
        st.session_state[_SECTION_KEY] = current

    counts = {"status": open_count, "reschedule": pending_count}
    columns = st.columns(4, gap="small")
    for column, (key, label) in zip(columns, _SECTIONS):
        suffix = f" ({counts[key]})" if counts.get(key) else ""
        with column:
            if st.button(
                label + suffix,
                key=f"hm_admin_schedule_section_{key}",
                type="primary" if current == key else "secondary",
                use_container_width=True,
            ):
                st.session_state[_SECTION_KEY] = key
                st.rerun()
    return current


def _consume_old_create_state() -> None:
    old_version = st.session_state.pop(_CREATE_CLEANUP_KEY, None)
    if old_version is None:
        return
    prefix = f"hm_admin_sched_create_v{old_version}_"
    for key in list(st.session_state.keys()):
        if str(key).startswith(prefix):
            st.session_state.pop(key, None)


def _render_flash() -> None:
    flash = st.session_state.pop(_FLASH_KEY, None)
    if not flash:
        return
    kind = _text(flash.get("kind"))
    message = _text(flash.get("message"))
    if kind == "success":
        st.markdown(
            "<div class='hm-sched-success'><b>✓</b>"
            f"{_safe(message)}</div>",
            unsafe_allow_html=True,
        )
    elif kind == "warning":
        st.warning(message)
    else:
        st.error(message)


def _render_create_schedule(
    member_id: str,
    member_tz: str,
    practitioner_id: str,
    source_tz: str,
) -> None:
    _consume_old_create_state()
    _render_flash()
    version = int(st.session_state.get(_CREATE_VERSION_KEY, 1) or 1)
    prefix = f"hm_admin_sched_create_v{version}_"
    practitioner_tz = _text(st.session_state.get(_SELECTED_TIMEZONE_KEY))

    with st.container(border=True):
        st.markdown("<div class='hm-sched-section-title'>Create Schedule / Notify Member</div>", unsafe_allow_html=True)
        st.markdown(
            "<div class='hm-sched-section-sub'>Only this workspace section is rendered. A successful creation opens a fresh transaction form with new widget identities.</div>",
            unsafe_allow_html=True,
        )

        schedule_type = st.selectbox(
            "Schedule type",
            (
                "Consultation",
                "Follow-up",
                "Daily Log Review",
                "Recipe Review",
                "Exercise Review",
                "Reassessment Discussion",
                "Other",
            ),
            key=prefix + "type",
        )
        title = st.text_input(
            "Schedule title",
            value=schedule_type,
            placeholder="Example: Follow-up call",
            key=prefix + "title",
        )
        date_col, start_col, end_col = st.columns(3, gap="medium")
        with date_col:
            schedule_date = st.date_input(
                "Date",
                value=today_in_timezone(source_tz),
                key=prefix + "date",
            )
        with start_col:
            start_time = st.time_input(
                "Start time",
                value=dt.time(10, 0),
                key=prefix + "start",
            )
        with end_col:
            default_end = (
                dt.datetime.combine(schedule_date, start_time)
                + dt.timedelta(minutes=30)
            ).time()
            end_time = st.time_input(
                "End time",
                value=default_end,
                key=prefix + "end",
            )
        mode_col, location_col = st.columns([0.9, 1.4], gap="medium")
        with mode_col:
            mode = st.selectbox(
                "Mode",
                ("Video", "Call", "In-person", "App message", "Other"),
                key=prefix + "mode",
            )
        with location_col:
            location_or_link = st.text_input(
                "Meeting link / phone / location",
                placeholder="Optional",
                key=prefix + "location",
            )
        notes = st.text_area(
            "Notes for member",
            placeholder="Optional instructions for the member",
            height=100,
            key=prefix + "notes",
        )

        preview: dict[str, Any] = {}
        preview_error = ""
        try:
            preview = build_dual_time_context(
                schedule_date,
                start_time,
                end_time,
                source_timezone_name=source_tz,
                member_timezone=member_tz,
                practitioner_timezone=practitioner_tz,
            )
        except ValueError as exc:
            preview_error = str(exc)
            st.error(preview_error)
        if preview:
            _render_time_context(
                preview,
                "Timezone confirmation before creating the schedule",
                member_first=False,
            )

        capacity = schedule_capacity(member_id, schedule_date)
        metrics = dict(capacity.get("metrics") or {})
        package = dict(capacity.get("package") or {})
        st.markdown(
            "<div class='hm-sched-capacity'><b>Package capacity:</b> "
            f"{_safe(package.get('package_name') or 'No current package')} · "
            f"Allowance {int(metrics.get('package_sessions', 0) or 0)} · "
            f"Consumed {int(metrics.get('sessions_consumed', 0) or 0)} · "
            f"Reserved {int(metrics.get('sessions_reserved', 0) or 0)} · "
            f"Available to schedule {int(metrics.get('sessions_available_to_schedule', 0) or 0)}</div>",
            unsafe_allow_html=True,
        )

        blocked = bool(capacity.get("requires_override"))
        override = False
        override_reason = ""
        if blocked:
            st.warning(capacity.get("message") or "A package-limit override is required.")
            if current_user_is_admin():
                override = st.checkbox(
                    "Admin/Super Admin override — allow this schedule despite the package limit",
                    key=prefix + "override",
                )
                if override:
                    override_reason = st.text_area(
                        "Mandatory package-limit override reason",
                        placeholder="Explain why this schedule must be created beyond the current package limit or lifecycle status.",
                        key=prefix + "override_reason",
                    ).strip()
            else:
                st.error("Only Admin or Super Admin can override package scheduling limits.")

        if st.button(
            "Create Schedule / Notify Member",
            type="primary",
            use_container_width=True,
            key=prefix + "submit",
            disabled=bool(preview_error),
        ):
            if blocked and (not override or not override_reason):
                st.error("Enter the mandatory Admin/Super Admin override reason before creating this schedule.")
                return
            st.session_state["hm_package_schedule_limit_override"] = bool(blocked and override)
            st.session_state["hm_package_schedule_limit_override_reason"] = override_reason
            try:
                created = create_timezone_aware_member_schedule(
                    member_id=member_id,
                    title=title,
                    schedule_type=schedule_type,
                    local_date=schedule_date,
                    start_time=start_time,
                    end_time=end_time,
                    source_timezone_name=source_tz,
                    practitioner_id=practitioner_id,
                    mode=mode,
                    location_or_link=location_or_link,
                    notes=notes,
                )
            except ValueError as exc:
                created = {"error": str(exc)}
            finally:
                st.session_state.pop("hm_package_schedule_limit_override", None)
                st.session_state.pop("hm_package_schedule_limit_override_reason", None)

            if created.get("error"):
                st.error(created.get("error"))
                return

            st.session_state[_FLASH_KEY] = {
                "kind": "success",
                "message": "Schedule created in UTC and shared with both local times.",
            }
            st.session_state[_CREATE_CLEANUP_KEY] = version
            st.session_state[_CREATE_VERSION_KEY] = version + 1
            st.session_state[_SECTION_KEY] = "create"
            st.rerun()


def _sorted_schedule_rows(member_id: str) -> list[dict[str, Any]]:
    rows = timezone_enriched_schedule_rows(
        member_id,
        include_cancelled=True,
        limit=0,
    )
    rows.sort(
        key=lambda row: (
            _text((row.get("_time_context") or {}).get("start_at_utc")),
            _text(row.get("created_at")),
        ),
        reverse=True,
    )
    return rows


def _render_schedule_status(member_id: str, practitioner_id: str) -> None:
    _render_flash()
    st.markdown("<div class='hm-sched-section-title'>Schedule Status</div>", unsafe_allow_html=True)
    st.markdown(
        "<div class='hm-sched-section-sub'>Latest consultation or meeting is shown first. Only this workspace section is rendered.</div>",
        unsafe_allow_html=True,
    )
    rows = _sorted_schedule_rows(member_id)
    if not rows:
        st.info("No schedules have been created for this member.")
        return
    for row in rows:
        status = _text(row.get("status") or "scheduled").lower()
        with st.container(border=True):
            st.markdown(
                "<div class='hm-sched-card-title'>"
                f"{_safe(row.get('title') or 'Scheduled session')}"
                f"<span class='hm-sched-pill'>{_safe(schedule_display_status_label_v104b11(row))}</span></div>",
                unsafe_allow_html=True,
            )
            _render_time_context(
                dict(row.get("_time_context") or {}),
                "Local schedule",
                member_first=False,
            )
            st.markdown(
                f"<div class='hm-sched-line'><b>Mode:</b> {_safe(row.get('mode') or '-')} · <b>Link/location:</b> {_safe(row.get('location_or_link') or '-')}</div>"
                f"<div class='hm-sched-line'><b>Notes:</b> {_safe(row.get('notes') or '-')}</div>",
                unsafe_allow_html=True,
            )
            if status in {"scheduled", "acknowledged"}:
                complete_col, cancel_col = st.columns(2, gap="medium")
                with complete_col:
                    if st.button(
                        "Mark Completed",
                        key=f"hm_admin_sched_complete_{row.get('id')}",
                        use_container_width=True,
                    ):
                        update_member_schedule_status(
                            row.get("id"),
                            "completed",
                            actor_id=practitioner_id,
                        )
                        st.session_state[_FLASH_KEY] = {
                            "kind": "success",
                            "message": "Schedule marked completed.",
                        }
                        st.rerun()
                with cancel_col:
                    if st.button(
                        "Cancel",
                        key=f"hm_admin_sched_cancel_{row.get('id')}",
                        use_container_width=True,
                    ):
                        update_member_schedule_status(
                            row.get("id"),
                            "cancelled",
                            actor_id=practitioner_id,
                        )
                        st.session_state[_FLASH_KEY] = {
                            "kind": "warning",
                            "message": "Schedule cancelled.",
                        }
                        st.rerun()
            else:
                st.caption("Closed schedule — no action is available.")


def _sorted_reschedule_requests(member_id: str) -> list[dict[str, Any]]:
    rows = list_timezone_aware_reschedule_requests(
        member_id=member_id,
        status=None,
        limit=0,
    )
    rows.sort(
        key=lambda row: (
            _text(row.get("updated_at")),
            _text(row.get("requested_at")),
            _text(row.get("created_at")),
        ),
        reverse=True,
    )
    return rows


def _render_reschedule_status(member_id: str, practitioner_id: str) -> None:
    _render_flash()
    st.markdown("<div class='hm-sched-section-title'>Reschedule Status</div>", unsafe_allow_html=True)
    st.markdown(
        "<div class='hm-sched-section-sub'>Latest request is shown first. Closed requests remain read-only.</div>",
        unsafe_allow_html=True,
    )
    requests = _sorted_reschedule_requests(member_id)
    if not requests:
        st.info("No reschedule requests exist for this member.")
        return
    for request in requests:
        request_id = _text(request.get("id"))
        request_status = _text(request.get("status") or "pending").lower()
        with st.container(border=True):
            st.markdown(
                "<div class='hm-sched-card-title'>"
                f"{_safe(request.get('current_title') or 'Scheduled session')}"
                f"<span class='hm-sched-pill'>{_safe(request_status.title())}</span></div>",
                unsafe_allow_html=True,
            )
            _render_time_context(
                dict(request.get("_current_time_context") or {}),
                "Current schedule",
                member_first=False,
            )
            _render_time_context(
                dict(request.get("_requested_time_context") or {}),
                "Requested schedule",
                member_first=False,
            )
            st.markdown(
                f"<div class='hm-sched-line'><b>Reason:</b> {_safe(request.get('reason') or '-')}</div>"
                f"<div class='hm-sched-capacity'>{_safe(reschedule_policy_text_v1012(bool(request.get('within_24_hours'))))}</div>",
                unsafe_allow_html=True,
            )
            requested_in_past = bool(request.get("_requested_in_past"))
            if requested_in_past and request_status == "pending":
                st.error(
                    "The requested UTC instant is already in the past. Ask the member for a fresh future time or reject the request."
                )
            admin_note = st.text_input(
                "Admin note",
                key=f"hm_admin_sched_reschedule_note_{request_id}",
                placeholder="Optional note to member",
                disabled=request_status != "pending",
            )
            if request_status != "pending":
                st.caption("Closed request — no action is available.")
                continue
            approve_col, reject_col = st.columns(2, gap="medium")
            with approve_col:
                if st.button(
                    "Approve Reschedule",
                    key=f"hm_admin_sched_approve_{request_id}",
                    use_container_width=True,
                    disabled=requested_in_past,
                ):
                    result = decide_timezone_aware_reschedule_request(
                        request_id,
                        "approved",
                        admin_note=admin_note,
                        actor_id=practitioner_id,
                    )
                    if result.get("error"):
                        st.error(result.get("error"))
                    else:
                        st.session_state[_FLASH_KEY] = {
                            "kind": "success",
                            "message": "Reschedule approved and the member was notified with both local times.",
                        }
                        st.rerun()
            with reject_col:
                if st.button(
                    "Reject Request",
                    key=f"hm_admin_sched_reject_{request_id}",
                    use_container_width=True,
                ):
                    result = decide_timezone_aware_reschedule_request(
                        request_id,
                        "rejected",
                        admin_note=admin_note,
                        actor_id=practitioner_id,
                    )
                    if result.get("error"):
                        st.error(result.get("error"))
                    else:
                        st.session_state[_FLASH_KEY] = {
                            "kind": "warning",
                            "message": "Reschedule request rejected and the member was notified.",
                        }
                        st.rerun()


def _render_session_ledger(member_id: str, member_tz: str) -> None:
    st.markdown("<div class='hm-sched-section-title'>Session Ledger</div>", unsafe_allow_html=True)
    st.markdown(
        f"<div class='hm-sched-section-sub'>Package usage and historical pricing for the selected member. Dates are shown in member local time: {_safe(member_tz)}.</div>",
        unsafe_allow_html=True,
    )
    ledger = member_session_ledger(member_id)
    metrics = dict(ledger.get("metrics") or {})
    st.markdown(
        "<div class='hm-sched-kpis'>"
        f"<div class='hm-sched-kpi'>Allowance<b>{int(metrics.get('package_sessions', 0) or 0)}</b></div>"
        f"<div class='hm-sched-kpi'>Consumed<b>{int(metrics.get('sessions_consumed', 0) or 0)}</b></div>"
        f"<div class='hm-sched-kpi'>Reserved<b>{int(metrics.get('sessions_reserved', 0) or 0)}</b></div>"
        f"<div class='hm-sched-kpi'>Remaining<b>{int(metrics.get('sessions_remaining', 0) or 0)}</b></div>"
        f"<div class='hm-sched-kpi'>Available<b>{int(metrics.get('sessions_available_to_schedule', 0) or 0)}</b></div>"
        "</div>",
        unsafe_allow_html=True,
    )
    package = dict(ledger.get("package") or {})
    st.caption(
        "Historical consumed value: "
        + _money(ledger.get("consumed_cost"), package.get("currency", "INR"))
        + ". Each row uses its saved historical subscription price."
    )
    if int(metrics.get("overbooked_sessions", 0) or 0) > 0:
        st.warning(
            f"{int(metrics.get('overbooked_sessions', 0))} session(s) are beyond the package allowance. Review the audited override history."
        )
    rows = list(ledger.get("rows") or [])
    if not rows:
        st.info("No sessions are available in the ledger.")
        return
    for row in rows:
        with st.container(border=True):
            st.markdown(
                "<div class='hm-sched-card-title'>"
                f"{_safe(row.get('title') or 'Session')}"
                f"<span class='hm-sched-pill'>{_safe(row.get('count_note') or row.get('status') or 'Open')}</span></div>"
                f"<div class='hm-sched-line'><b>Date:</b> {_safe(row.get('date'))} · <b>Time:</b> {_safe(row.get('time'))}</div>"
                f"<div class='hm-sched-line'><b>Historical cost:</b> {_safe(_money(row.get('cost'), row.get('currency', package.get('currency', 'INR'))))}</div>",
                unsafe_allow_html=True,
            )


def render_admin_scheduling_consolidated_page() -> None:
    st.set_page_config(
        page_title="Admin Scheduling",
        page_icon="💚",
        layout="wide",
        initial_sidebar_state="collapsed",
    )
    inject_global_styles()
    apply_luxe_theme()
    require_admin()
    utility_logout_bar()
    topbar(
        "Scheduling",
        "Create, manage and approve member appointments, follow-ups and reschedule requests.",
        "Admin workflow",
    )
    _inject_styles()

    # This navigation is rendered directly on every rerun, before timezone validation.
    _render_return_navigation("top")

    context = _render_context_selector()
    if context is None:
        render_back_to_top()
        st.stop()
    member_id, member_tz, practitioner_id, source_tz = context

    section = _workspace_navigation(member_id)
    st.markdown("<div class='hm-sched-workspace'>", unsafe_allow_html=True)
    if section == "create":
        _render_create_schedule(member_id, member_tz, practitioner_id, source_tz)
    elif section == "status":
        _render_schedule_status(member_id, practitioner_id)
    elif section == "reschedule":
        _render_reschedule_status(member_id, practitioner_id)
    else:
        _render_session_ledger(member_id, member_tz)
    st.markdown("</div>", unsafe_allow_html=True)

    _render_return_navigation("bottom")
    render_back_to_top()
