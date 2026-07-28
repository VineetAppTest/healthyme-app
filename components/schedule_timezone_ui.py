from __future__ import annotations

import datetime
import html

import streamlit as st

from components.guards import require_admin, require_member
from components.ui_common import (
    inject_global_styles,
    apply_luxe_theme,
    utility_logout_bar,
    render_back_to_top,
    topbar,
    render_page_nav,
)
from components.db import (
    list_members,
    update_member_schedule_status,
    acknowledge_member_schedule,
    schedule_display_status_label_v104b11,
    reschedule_policy_text_v1012,
    get_member_session_ledger_v1024b13,
    get_member_active_package_v1024b14,
)
from components.member_timezone import member_timezone_name
from components.schedule_timezone import (
    build_dual_time_context,
    context_start_is_future,
    create_timezone_aware_member_schedule,
    decide_timezone_aware_reschedule_request,
    list_timezone_aware_admin_open_schedules,
    list_timezone_aware_member_schedules,
    list_timezone_aware_reschedule_requests,
    persist_practitioner_timezone,
    practitioner_timezone_name,
    queue_timezone_aware_schedule_acknowledgement_reminders,
    request_timezone_aware_reschedule,
    schedule_within_hours,
    timezone_enriched_schedule_rows,
    timezone_options,
    today_in_timezone,
)


def _safe(value: object) -> str:
    return html.escape(str(value or ""))


def _inject_schedule_styles() -> None:
    st.markdown(
        """
<style id="hm-cross-timezone-schedule-v1">
section.main > div.block-container,.main .block-container,[data-testid="stAppViewBlockContainer"],.stMainBlockContainer,.block-container{max-width:1180px!important;padding-top:.72rem!important;}
.hm-tz-context-shell{border:1.5px solid #B89345;background:linear-gradient(135deg,#FFFDF8 0%,#FFF3D6 100%);border-radius:20px;padding:1rem 1.05rem;margin:.20rem 0 .82rem 0;box-shadow:0 12px 26px rgba(15,23,42,.07);}
.hm-tz-context-title{color:#064E3B;font-size:1rem;font-weight:900;margin-bottom:.16rem;letter-spacing:.01em;}
.hm-tz-context-sub{color:#72551A;font-size:.80rem;font-weight:620;margin-bottom:.52rem;}
.hm-schedule-section{border:1px solid #E3C98E;background:linear-gradient(180deg,#FFFDF8 0%,#FFF9EC 100%);border-radius:20px;padding:1rem 1.08rem;box-shadow:0 10px 24px rgba(15,23,42,.05);margin:.40rem 0 .90rem 0;}
.hm-schedule-heading{color:#003C36;font-size:1.12rem;font-weight:980;margin:0 0 .25rem 0;}
.hm-schedule-sub{color:#475569;font-size:.86rem;font-weight:700;margin:0 0 .90rem 0;}
.hm-schedule-card{border:1px solid #E3C98E;background:#FFFDF8;border-radius:18px;padding:.90rem 1.05rem;margin:.50rem 0;box-shadow:0 8px 20px rgba(15,23,42,.045);}
.hm-schedule-title{color:#064E3B;font-size:1rem;font-weight:950;margin-bottom:.20rem;}
.hm-schedule-line{color:#334155;font-size:.86rem;font-weight:720;margin:.10rem 0;line-height:1.35;}
.hm-schedule-muted{color:#64748B;font-size:.78rem;font-weight:620;margin:.12rem 0;}
.hm-schedule-pill{display:inline-flex;padding:.18rem .48rem;border-radius:999px;border:1px solid #D9C28F;background:#FFF7E6;color:#7A5A16;font-size:.72rem;font-weight:850;margin-left:.25rem;}
.hm-time-preview{border:1px solid #D7C28D;background:#FFFFFF;border-radius:16px;padding:.78rem .88rem;margin:.55rem 0 .72rem 0;}
.hm-time-preview-title{color:#064E3B;font-size:.86rem;font-weight:900;margin-bottom:.28rem;}
.hm-time-preview-line{color:#334155;font-size:.83rem;font-weight:690;margin:.12rem 0;line-height:1.36;}
.hm-time-preview-note{color:#8A641D;font-size:.76rem;font-weight:700;margin-top:.30rem;}
.hm-policy-box{border:1px solid #E3C98E;background:#FFF7E6;border-radius:14px;padding:.72rem .84rem;color:#7A5A16;font-size:.84rem;font-weight:650;margin:.45rem 0 .65rem 0;}
.hm-package-summary{border:1px solid #E3C98E;border-radius:16px;background:#FFFDF8;padding:.82rem .92rem;margin:.35rem 0 .85rem 0;}
.hm-package-title{color:#064E3B;font-size:.98rem;font-weight:760;margin-bottom:.18rem;}
.hm-package-line{color:#334155;font-size:.84rem;font-weight:520;margin:.08rem 0;}
.hm-ledger-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:.7rem;margin:.45rem 0 1rem 0;}
.hm-ledger-kpi{border:1px solid #E3C98E;background:#FFFDF8;border-radius:16px;padding:.75rem .85rem;}
.hm-ledger-kpi b{display:block;color:#064E3B;font-size:1.25rem;margin-top:.12rem;}
.hm-ledger-table{border:1px solid #E3C98E;border-radius:16px;overflow:hidden;background:#FFFDF8;margin:.35rem 0;}
.hm-ledger-row{display:grid;grid-template-columns:1.3fr .8fr .9fr .65fr .75fr;gap:.5rem;padding:.62rem .72rem;border-top:1px solid #F0E3C5;align-items:center;font-size:.82rem;}
.hm-ledger-head{background:#FFF7E6;border-top:0;font-weight:760;color:#064E3B;}
.hm-flash-ok{border:1px solid #B7DEC5;background:#EEF9F1;color:#14532D;border-radius:14px;padding:.72rem .86rem;margin:.45rem 0 .80rem 0;font-weight:650;}
.hm-flash-error{border:1px solid #F0B4A5;background:#FFF2EE;color:#9A3412;border-radius:14px;padding:.72rem .86rem;margin:.45rem 0 .80rem 0;font-weight:650;}
div[data-testid="stButton"] > button{min-height:2.72rem!important;border-radius:14px!important;border:1.25px solid #D9C28F!important;background:#FFFDF8!important;color:#064E3B!important;font-weight:600!important;box-shadow:none!important;}
div[data-testid="stButton"] > button:hover{border-color:#B89345!important;background:#FFF7E6!important;}
@media(max-width:760px){.hm-ledger-grid{grid-template-columns:1fr!important}.hm-ledger-row{grid-template-columns:1fr!important;gap:.18rem!important}.hm-ledger-head{display:none!important}}
</style>
""",
        unsafe_allow_html=True,
    )


def _time_preview_html(context: dict, *, member_first: bool = True) -> str:
    if not context:
        return ""
    member = context.get("member") or {}
    practitioner = context.get("practitioner") or {}
    if context.get("same_timezone"):
        lines = [("Member & practitioner", member)]
    elif member_first:
        lines = [("Member", member), ("Practitioner", practitioner)]
    else:
        lines = [("Practitioner", practitioner), ("Member", member)]
    rendered = []
    for label, row in lines:
        rendered.append(
            "<div class='hm-time-preview-line'><b>"
            f"{_safe(label)}:</b> {_safe(row.get('date_label'))} · "
            f"{_safe(row.get('time_window'))} · {_safe(row.get('timezone_name'))} "
            f"({_safe(row.get('offset'))})</div>"
        )
    notes = []
    if context.get("crosses_party_date_boundary"):
        notes.append("The calendar date differs between the member and practitioner.")
    if context.get("dst_warning"):
        notes.append(context.get("dst_warning"))
    if context.get("legacy_inferred"):
        notes.append("Legacy schedule: the stored date/time has been interpreted in the member timezone.")
    note_html = "".join(
        f"<div class='hm-time-preview-note'>{_safe(note)}</div>" for note in notes
    )
    return "".join(rendered) + note_html


def _render_time_preview(context: dict, title: str, *, member_first: bool = True) -> None:
    if not context:
        return
    st.markdown(
        "<div class='hm-time-preview'>"
        f"<div class='hm-time-preview-title'>{_safe(title)}</div>"
        f"{_time_preview_html(context, member_first=member_first)}"
        "</div>",
        unsafe_allow_html=True,
    )


def _render_package(member_id: object, *, member_view: bool) -> None:
    active_pkg = get_member_active_package_v1024b14(member_id)
    st.markdown("<div class='hm-schedule-section'>", unsafe_allow_html=True)
    st.markdown("<div class='hm-schedule-heading'>Package Subscribed</div>", unsafe_allow_html=True)
    st.markdown(
        "<div class='hm-schedule-sub'>Your subscribed package and session allowance.</div>"
        if member_view
        else "<div class='hm-schedule-sub'>The selected member's active package and session allowance.</div>",
        unsafe_allow_html=True,
    )
    if active_pkg:
        inclusions = ", ".join(
            key for key, value in (active_pkg.get("inclusions", {}) or {}).items() if value
        ) or "No inclusions selected"
        st.markdown(
            "<div class='hm-package-summary'>"
            f"<div class='hm-package-title'>{_safe(active_pkg.get('package_name') or 'Package')}</div>"
            f"<div class='hm-package-line'>{int(active_pkg.get('session_count', 0) or 0)} sessions · "
            f"{_safe(active_pkg.get('currency') or 'INR')} {float(active_pkg.get('cost_per_session', 0) or 0):,.2f} per session · "
            f"{int(active_pkg.get('number_of_people', 1) or 1)} people</div>"
            f"<div class='hm-package-line'>Inclusions: {_safe(inclusions)}</div></div>",
            unsafe_allow_html=True,
        )
    else:
        st.info("No package has been subscribed for you yet." if member_view else "No active package is assigned to this member.")
    st.markdown("</div>", unsafe_allow_html=True)


def _render_member_ledger(member_id: object, member_timezone: str) -> None:
    st.markdown("<div class='hm-schedule-section'>", unsafe_allow_html=True)
    st.markdown("<div class='hm-schedule-heading'>Session Usage</div>", unsafe_allow_html=True)
    st.markdown(
        f"<div class='hm-schedule-sub'>Session count is controlled by scheduled sessions and approved late reschedules. Ledger dates and times are shown in member local time: {_safe(member_timezone)}.</div>",
        unsafe_allow_html=True,
    )
    ledger = get_member_session_ledger_v1024b13(member_id)
    rows = ledger.get("rows", [])
    currency = (ledger.get("package") or {}).get("currency", "INR")
    st.markdown(
        "<div class='hm-ledger-grid'>"
        f"<div class='hm-ledger-kpi'>Package sessions<b>{ledger.get('package_sessions', 0) or len(rows)}</b></div>"
        f"<div class='hm-ledger-kpi'>Sessions consumed<b>{ledger.get('consumed_count', 0)}</b></div>"
        f"<div class='hm-ledger-kpi'>Remaining<b>{ledger.get('remaining_sessions', 0)}</b></div>"
        "</div>"
        f"<div class='hm-package-line'>Consumed cost: {_safe(currency)} {float(ledger.get('consumed_cost', 0) or 0):,.2f}</div>",
        unsafe_allow_html=True,
    )
    if rows:
        st.markdown("<div class='hm-ledger-table'>", unsafe_allow_html=True)
        st.markdown(
            "<div class='hm-ledger-row hm-ledger-head'><div>Session</div><div>Date</div><div>Time</div><div>Cost</div><div>Usage</div></div>",
            unsafe_allow_html=True,
        )
        for row in rows:
            usage = "Consumed" if row.get("consumed") else "Open"
            st.markdown(
                "<div class='hm-ledger-row'>"
                f"<div>{_safe(row.get('title') or 'Session')}<br><small>{_safe(row.get('status'))}</small></div>"
                f"<div>{_safe(row.get('date'))}</div><div>{_safe(row.get('time'))}</div>"
                f"<div>{_safe(currency)} {float(row.get('cost', 0) or 0):,.2f}</div><div>{_safe(usage)}</div></div>",
                unsafe_allow_html=True,
            )
        st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.info("No sessions have been scheduled yet.")
    st.markdown("</div>", unsafe_allow_html=True)


def render_admin_scheduling_page() -> None:
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
    _inject_schedule_styles()

    members = list_members()
    if not members:
        st.info("No members available.")
        st.stop()

    st.markdown("<div class='hm-tz-context-shell'>", unsafe_allow_html=True)
    st.markdown("<div class='hm-tz-context-title'>Page Context Selector · Controls this full page</div>", unsafe_allow_html=True)
    st.markdown("<div class='hm-tz-context-sub'>All schedule creation, status, reschedule review and session usage below are for the selected member only.</div>", unsafe_allow_html=True)
    member_options = {
        f"{member.get('name', '')} — {member.get('email', '')}": member.get("id")
        for member in members
    }
    selected_label = st.selectbox(
        "Select member controlling this page",
        list(member_options.keys()),
        key="hm_tz_schedule_member",
    )
    member_id = member_options[selected_label]
    practitioner_id = st.session_state.get("user_id") or "admin"
    current_practitioner_tz = practitioner_timezone_name(practitioner_id, persist=True)
    tz_values = timezone_options()
    selected_practitioner_tz = st.selectbox(
        "Your scheduling timezone",
        tz_values,
        index=tz_values.index(current_practitioner_tz) if current_practitioner_tz in tz_values else 0,
        key="hm_tz_practitioner_timezone",
        help="HealthyMe stores this IANA timezone for scheduling. It does not use your IP, VPN or server location.",
    )
    if selected_practitioner_tz != current_practitioner_tz:
        persist_practitioner_timezone(practitioner_id, selected_practitioner_tz)
        current_practitioner_tz = selected_practitioner_tz
    member_tz = member_timezone_name(member_id, persist=True)
    st.markdown(
        f"<div class='hm-schedule-muted'>Practitioner timezone: <b>{_safe(current_practitioner_tz)}</b> · Member timezone: <b>{_safe(member_tz)}</b></div>",
        unsafe_allow_html=True,
    )
    entry_basis = st.radio(
        "Enter the schedule in",
        ["Practitioner local time", "Member local time"],
        horizontal=True,
        key="hm_tz_entry_basis",
    )
    source_tz = current_practitioner_tz if entry_basis == "Practitioner local time" else member_tz
    st.markdown(
        f"<div class='hm-schedule-muted'>Date and time controls below are interpreted in <b>{_safe(source_tz)}</b>. Both local versions are shown before saving.</div>",
        unsafe_allow_html=True,
    )
    st.markdown("</div>", unsafe_allow_html=True)

    open_count = len(list_timezone_aware_admin_open_schedules(member_id, limit=0))
    pending_count = len(
        list_timezone_aware_reschedule_requests(
            member_id=member_id, status="pending", limit=0
        )
    )
    tab_create, tab_status, tab_reschedule, tab_ledger = st.tabs(
        [
            "Create Schedule",
            f"Schedule Status ({open_count})" if open_count else "Schedule Status",
            f"Reschedule Status ({pending_count})" if pending_count else "Reschedule Status",
            "Session Ledger",
        ]
    )

    with tab_create:
        st.markdown("<div class='hm-schedule-section'>", unsafe_allow_html=True)
        st.markdown("<div class='hm-schedule-heading'>Create Schedule / Notify Member</div>", unsafe_allow_html=True)
        st.markdown("<div class='hm-schedule-sub'>Choose whether the entered date/time is practitioner-local or member-local. HealthyMe stores the agreed instant in UTC and shows both local views.</div>", unsafe_allow_html=True)
        active_pkg = get_member_active_package_v1024b14(member_id)
        if active_pkg:
            st.markdown(
                f"<div class='hm-package-line'>Active package: <b>{_safe(active_pkg.get('package_name') or 'Package')}</b> · {int(active_pkg.get('session_count', 0) or 0)} sessions · {_safe(active_pkg.get('currency') or 'INR')} {float(active_pkg.get('cost_per_session', 0) or 0):,.2f} per session</div>",
                unsafe_allow_html=True,
            )
        schedule_type = st.selectbox(
            "Schedule type",
            [
                "Consultation",
                "Follow-up",
                "Daily Log Review",
                "Recipe Review",
                "Exercise Review",
                "Reassessment Discussion",
                "Other",
            ],
            key="hm_tz_schedule_type",
        )
        title = st.text_input(
            "Schedule title",
            value=schedule_type,
            placeholder="Example: Follow-up call",
            key="hm_tz_schedule_title",
        )
        date_col, start_col, end_col = st.columns([1, 1, 1], gap="medium")
        with date_col:
            schedule_date = st.date_input(
                "Date",
                value=today_in_timezone(source_tz),
                key="hm_tz_schedule_date",
            )
        with start_col:
            start_time = st.time_input(
                "Start time",
                value=datetime.time(10, 0),
                key="hm_tz_schedule_start",
            )
        with end_col:
            default_end = (
                datetime.datetime.combine(schedule_date, start_time)
                + datetime.timedelta(minutes=30)
            ).time()
            end_time = st.time_input(
                "End time",
                value=default_end,
                key="hm_tz_schedule_end",
            )
        mode_col, link_col = st.columns([0.9, 1.4], gap="medium")
        with mode_col:
            mode = st.selectbox(
                "Mode",
                ["Video", "Call", "In-person", "App message", "Other"],
                key="hm_tz_schedule_mode",
            )
        with link_col:
            location_or_link = st.text_input(
                "Meeting link / phone / location",
                placeholder="Optional",
                key="hm_tz_schedule_location",
            )
        notes = st.text_area(
            "Notes for member",
            placeholder="Optional instructions for the member",
            height=100,
            key="hm_tz_schedule_notes",
        )
        preview = {}
        preview_error = ""
        try:
            preview = build_dual_time_context(
                schedule_date,
                start_time,
                end_time,
                source_timezone_name=source_tz,
                member_timezone=member_tz,
                practitioner_timezone=current_practitioner_tz,
            )
        except ValueError as exc:
            preview_error = str(exc)
            st.error(preview_error)
        if preview:
            _render_time_preview(
                preview,
                "Timezone confirmation before creating the schedule",
                member_first=False,
            )
        flash = st.session_state.pop("hm_tz_schedule_flash", None)
        if st.button(
            "Create Schedule / Notify Member",
            use_container_width=True,
            disabled=bool(preview_error),
            key="hm_tz_create_schedule",
        ):
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
                if created.get("error"):
                    st.session_state["hm_tz_schedule_flash"] = {
                        "kind": "error",
                        "message": created.get("error"),
                    }
                else:
                    st.session_state["hm_tz_schedule_flash"] = {
                        "kind": "success",
                        "message": "Schedule created in UTC and shared with both local times.",
                    }
            except ValueError as exc:
                st.session_state["hm_tz_schedule_flash"] = {
                    "kind": "error",
                    "message": str(exc),
                }
            st.rerun()
        if flash:
            klass = "hm-flash-ok" if flash.get("kind") == "success" else "hm-flash-error"
            st.markdown(
                f"<div class='{klass}'>{_safe(flash.get('message'))}</div>",
                unsafe_allow_html=True,
            )
        st.markdown("</div>", unsafe_allow_html=True)

    with tab_status:
        st.markdown("<div class='hm-schedule-section'>", unsafe_allow_html=True)
        st.markdown("<div class='hm-schedule-heading'>Schedule Status</div>", unsafe_allow_html=True)
        st.markdown("<div class='hm-schedule-sub'>Track open and closed sessions. Every schedule shows the member and practitioner local date/time from the same UTC instant.</div>", unsafe_allow_html=True)
        rows = timezone_enriched_schedule_rows(
            member_id, include_cancelled=True, limit=30
        )
        if not rows:
            st.info("No schedules created for this member yet.")
        else:
            for row in rows:
                status = str(row.get("status") or "scheduled").lower().strip()
                counted_note = " · Prior session counted" if row.get("session_counted") else ""
                st.markdown(
                    "<div class='hm-schedule-card'>"
                    f"<div class='hm-schedule-title'>{_safe(row.get('title') or 'Scheduled session')}<span class='hm-schedule-pill'>{_safe(schedule_display_status_label_v104b11(row))}</span></div>"
                    f"{_time_preview_html(row.get('_time_context') or {}, member_first=False)}"
                    f"<div class='hm-schedule-line'>Mode: {_safe(row.get('mode') or '-')} · Link/location: {_safe(row.get('location_or_link') or '-')}</div>"
                    f"<div class='hm-schedule-line'>Notes: {_safe(row.get('notes') or '-')}{_safe(counted_note)}</div>"
                    "</div>",
                    unsafe_allow_html=True,
                )
                if status in {"scheduled", "acknowledged"}:
                    c1, c2 = st.columns(2, gap="medium")
                    with c1:
                        if st.button(
                            "Mark Completed",
                            key=f"hm_tz_schedule_done_{row.get('id')}",
                            use_container_width=True,
                        ):
                            update_member_schedule_status(
                                row.get("id"),
                                "completed",
                                actor_id=practitioner_id,
                            )
                            st.success("Schedule marked completed.")
                            st.rerun()
                    with c2:
                        if st.button(
                            "Cancel",
                            key=f"hm_tz_schedule_cancel_{row.get('id')}",
                            use_container_width=True,
                        ):
                            update_member_schedule_status(
                                row.get("id"),
                                "cancelled",
                                actor_id=practitioner_id,
                            )
                            st.warning("Schedule cancelled.")
                            st.rerun()
                else:
                    st.caption("Closed schedule — no action available.")
        st.markdown("</div>", unsafe_allow_html=True)

    with tab_reschedule:
        st.markdown("<div class='hm-schedule-section'>", unsafe_allow_html=True)
        st.markdown("<div class='hm-schedule-heading'>Reschedule Status</div>", unsafe_allow_html=True)
        st.markdown("<div class='hm-schedule-sub'>Approve or reject member-requested changes after reviewing both local representations.</div>", unsafe_allow_html=True)
        requests = list_timezone_aware_reschedule_requests(
            member_id=member_id, status=None, limit=30
        )
        if not requests:
            st.info("No reschedule requests for this member.")
        else:
            for req in requests:
                request_status = req.get("status", "pending")
                st.markdown(
                    "<div class='hm-schedule-card'>"
                    f"<div class='hm-schedule-title'>{_safe(req.get('current_title') or 'Scheduled session')}<span class='hm-schedule-pill'>{_safe(str(request_status).title())}</span></div>"
                    "<div class='hm-time-preview-title'>Current schedule</div>"
                    f"{_time_preview_html(req.get('_current_time_context') or {}, member_first=False)}"
                    "<div class='hm-time-preview-title' style='margin-top:.45rem'>Requested schedule</div>"
                    f"{_time_preview_html(req.get('_requested_time_context') or {}, member_first=False)}"
                    f"<div class='hm-schedule-line'>Reason: {_safe(req.get('reason') or '-')}</div>"
                    "</div>"
                    f"<div class='hm-policy-box'>{_safe(reschedule_policy_text_v1012(bool(req.get('within_24_hours'))))}</div>",
                    unsafe_allow_html=True,
                )
                if req.get("_requested_in_past") and request_status == "pending":
                    st.error("The requested UTC instant is already in the past. Ask the member for a fresh future time or reject this request.")
                admin_note = st.text_input(
                    "Admin note",
                    key=f"hm_tz_reschedule_note_{req.get('id')}",
                    placeholder="Optional note to member",
                    disabled=request_status != "pending",
                )
                approve_col, reject_col = st.columns(2, gap="medium")
                with approve_col:
                    if st.button(
                        "Approve Reschedule",
                        key=f"hm_tz_approve_reschedule_{req.get('id')}",
                        use_container_width=True,
                        disabled=request_status != "pending" or bool(req.get("_requested_in_past")),
                    ):
                        result = decide_timezone_aware_reschedule_request(
                            req.get("id"),
                            "approved",
                            admin_note=admin_note,
                            actor_id=practitioner_id,
                        )
                        if result.get("error"):
                            st.error(result.get("error"))
                        else:
                            st.success("Reschedule approved and member notified with both local times.")
                            st.rerun()
                with reject_col:
                    if st.button(
                        "Reject Request",
                        key=f"hm_tz_reject_reschedule_{req.get('id')}",
                        use_container_width=True,
                        disabled=request_status != "pending",
                    ):
                        decide_timezone_aware_reschedule_request(
                            req.get("id"),
                            "rejected",
                            admin_note=admin_note,
                            actor_id=practitioner_id,
                        )
                        st.warning("Reschedule request rejected and member notified.")
                        st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    with tab_ledger:
        _render_member_ledger(member_id, member_tz)

    render_page_nav(
        "Scheduling",
        back_page="pages/10_Admin_Dashboard.py",
        dashboard_page="pages/10_Admin_Dashboard.py",
        show_evaluation=False,
        show_dashboard=True,
        location="bottom",
    )
    render_back_to_top()


def render_member_schedule_page() -> None:
    st.set_page_config(
        page_title="My Schedule",
        page_icon="💚",
        layout="wide",
        initial_sidebar_state="collapsed",
    )
    inject_global_styles()
    apply_luxe_theme()
    require_member()
    user_id = st.session_state.get("user_id")
    utility_logout_bar()
    topbar(
        "My Schedule",
        "View, acknowledge or request a reschedule for upcoming sessions.",
        "Member content",
    )
    _inject_schedule_styles()
    member_tz = member_timezone_name(user_id, persist=True)

    _render_package(user_id, member_view=True)

    st.markdown("<div class='hm-schedule-section'>", unsafe_allow_html=True)
    st.markdown("<div class='hm-schedule-heading'>Upcoming Schedule</div>", unsafe_allow_html=True)
    st.markdown(
        f"<div class='hm-schedule-sub'>Your primary date/time is shown in member local time: {_safe(member_tz)}. Practitioner local time is shown alongside when different.</div>",
        unsafe_allow_html=True,
    )
    queue_timezone_aware_schedule_acknowledgement_reminders(user_id)
    rows = list_timezone_aware_member_schedules(user_id, limit=30)
    if not rows:
        st.info("No upcoming schedule has been created for you yet.")
    else:
        for row in rows:
            status = row.get("status", "scheduled")
            context = row.get("_time_context") or {}
            st.markdown(
                "<div class='hm-schedule-card'>"
                f"<div class='hm-schedule-title'>{_safe(row.get('title') or 'Scheduled session')}<span class='hm-schedule-pill'>{_safe(schedule_display_status_label_v104b11(row))}</span></div>"
                f"{_time_preview_html(context, member_first=True)}"
                f"<div class='hm-schedule-line'>Mode: {_safe(row.get('mode') or '-')} · Link/location: {_safe(row.get('location_or_link') or '-')}</div>"
                f"<div class='hm-schedule-line'>Notes: {_safe(row.get('notes') or '-')}</div>"
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
                        acknowledge_member_schedule(row.get("id"), user_id)
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
                    st.session_state[state_key] = not st.session_state.get(state_key, False)
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
                        value=today_in_timezone(member_tz),
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
                        requested_preview = build_dual_time_context(
                            preferred_date,
                            preferred_start,
                            preferred_end,
                            source_timezone_name=member_tz,
                            member_timezone=member_tz,
                            practitioner_timezone=context.get("practitioner_timezone_name") or member_tz,
                        )
                        if not context_start_is_future(requested_preview):
                            request_error = "Choose a future member-local date and time."
                    except ValueError as exc:
                        request_error = str(exc)
                    if request_error:
                        st.error(request_error)
                    if requested_preview:
                        _render_time_preview(
                            requested_preview,
                            "Timezone confirmation for your requested slot",
                            member_first=True,
                        )
                    within_24 = schedule_within_hours(row, 24)
                    st.markdown(
                        f"<div class='hm-policy-box'>{_safe(reschedule_policy_text_v1012(within_24))}</div>",
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
                            req = request_timezone_aware_reschedule(
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
                            st.success("Reschedule request submitted with both local times for admin review.")
                            st.session_state[state_key] = False
                            st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

    _render_member_ledger(user_id, member_tz)

    render_page_nav(
        "My Schedule",
        back_page="pages/02_Member_Home.py",
        dashboard_page="pages/02_Member_Home.py",
        show_evaluation=False,
        show_dashboard=True,
        location="bottom",
    )
    render_back_to_top()
