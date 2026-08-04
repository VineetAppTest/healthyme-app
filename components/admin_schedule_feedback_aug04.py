from __future__ import annotations

import datetime as dt
import functools
import html
from typing import Any

import streamlit as st

from components import db as db_api
from components.schedule_timezone import schedule_time_context


_MARKER = "_hm_admin_schedule_feedback_aug04_v1"


def _text(value: object) -> str:
    return str(value or "").strip()


def _safe(value: object) -> str:
    return html.escape(_text(value))


def _clear_transaction_prefix(prefix: str) -> None:
    for key in list(st.session_state.keys()):
        if str(key).startswith(prefix):
            st.session_state.pop(key, None)


def _consume_pending_reset(scheduling_module: Any) -> None:
    old_version = st.session_state.pop(scheduling_module._CREATE_CLEANUP_KEY, None)
    if old_version is None:
        return
    _clear_transaction_prefix(f"hm_admin_sched_create_v{old_version}_")


def _member_name(schedule: dict[str, Any]) -> str:
    direct = _text(schedule.get("member_name"))
    if direct:
        return direct
    member_id = _text(schedule.get("member_id"))
    member_email = _text(schedule.get("member_email")).lower()
    member = db_api.get_user_by_id(member_id) or {}
    return (
        _text(member.get("name"))
        or _text(member.get("email"))
        or member_email
        or member_id
        or "Member"
    )


def _admin_schedule_for_date(
    selected_date: dt.date,
    practitioner_id: str,
) -> list[dict[str, str]]:
    db = db_api.load_db()
    practitioner_key = _text(practitioner_id) or "admin"
    output: list[dict[str, str]] = []
    for raw in db.get("schedules", []) or []:
        if not isinstance(raw, dict):
            continue
        status = _text(raw.get("status") or "scheduled").lower()
        if status in {"cancelled", "rescheduled"}:
            continue
        created_by = _text(raw.get("created_by") or raw.get("actor_id"))
        if created_by and created_by != practitioner_key:
            continue
        try:
            context = schedule_time_context(
                raw,
                member_id=raw.get("member_id", ""),
                practitioner_id=practitioner_key,
            )
        except Exception:
            context = {}
        practitioner = dict(context.get("practitioner") or {})
        schedule_date = _text(practitioner.get("date_iso")) or _text(
            raw.get("practitioner_local_date") or raw.get("schedule_date")
        )
        if schedule_date != selected_date.isoformat():
            continue
        schedule_time = _text(practitioner.get("time_window"))
        if not schedule_time:
            start = _text(raw.get("practitioner_local_start_time") or raw.get("start_time"))
            end = _text(raw.get("practitioner_local_end_time") or raw.get("end_time"))
            schedule_time = " – ".join(value for value in (start, end) if value)
        output.append(
            {
                "Schedule date": schedule_date,
                "Name of Member": _member_name(raw),
                "Schedule Time": schedule_time or "—",
                "Subject": _text(raw.get("title") or raw.get("schedule_type"))
                or "Scheduled session",
            }
        )
    output.sort(key=lambda row: (row["Schedule Time"], row["Name of Member"].casefold()))
    return output


def _render_day_schedule(rows: list[dict[str, str]], selected_date: dt.date) -> None:
    st.markdown(
        "<div class='hm-sched-day-title'>Admin schedule</div>"
        f"<div class='hm-sched-day-sub'>{_safe(selected_date.strftime('%d %b %Y'))}</div>",
        unsafe_allow_html=True,
    )
    if not rows:
        st.info("No meetings are scheduled for this Admin on the selected date.")
        return
    body = "".join(
        "<tr>"
        f"<td>{_safe(row['Schedule date'])}</td>"
        f"<td>{_safe(row['Name of Member'])}</td>"
        f"<td>{_safe(row['Schedule Time'])}</td>"
        f"<td>{_safe(row['Subject'])}</td>"
        "</tr>"
        for row in rows
    )
    st.markdown(
        "<div class='hm-sched-day-table-wrap'><table class='hm-sched-day-table'>"
        "<thead><tr><th>Schedule date</th><th>Name of Member</th>"
        "<th>Schedule Time</th><th>Subject</th></tr></thead>"
        f"<tbody>{body}</tbody></table></div>",
        unsafe_allow_html=True,
    )


def _render_feedback_styles() -> None:
    st.markdown(
        """
<style id="hm-admin-schedule-feedback-aug04-v1">
.hm-sched-create-anchor{display:none!important;height:0!important;margin:0!important;padding:0!important;}
div[data-testid="stHorizontalBlock"]:has(.hm-sched-create-anchor){align-items:flex-start!important;gap:.85rem!important;}
div[data-testid="stHorizontalBlock"]:has(.hm-sched-create-anchor)>div:first-child{flex:3 1 0!important;min-width:0!important;}
div[data-testid="stHorizontalBlock"]:has(.hm-sched-create-anchor)>div:last-child{flex:1 1 0!important;min-width:250px!important;}
.hm-sched-day-title{color:#064E3B;font-size:.96rem;font-weight:950;margin:.08rem 0 .05rem;}
.hm-sched-day-sub{color:#64748B;font-size:.76rem;font-weight:750;margin-bottom:.42rem;}
.hm-sched-day-table-wrap{overflow:auto;border:1px solid #E3C98E;border-radius:13px;background:#FFFDF8;max-height:500px;}
.hm-sched-day-table{width:100%;border-collapse:collapse;font-size:.68rem;line-height:1.25;}
.hm-sched-day-table th{background:#FFF4DE;color:#064E3B;font-weight:900;text-align:left;padding:.42rem .38rem;border-bottom:1px solid #E3C98E;vertical-align:top;}
.hm-sched-day-table td{color:#334155;font-weight:650;padding:.42rem .38rem;border-bottom:1px solid #F1E2BD;vertical-align:top;overflow-wrap:anywhere;}
.hm-sched-day-table tr:last-child td{border-bottom:0;}
@media(max-width:900px){
  div[data-testid="stHorizontalBlock"]:has(.hm-sched-create-anchor){display:flex!important;flex-direction:column!important;}
  div[data-testid="stHorizontalBlock"]:has(.hm-sched-create-anchor)>div{width:100%!important;min-width:100%!important;}
}
</style>
""",
        unsafe_allow_html=True,
    )


def install_admin_schedule_feedback(scheduling_module: Any) -> None:
    if getattr(scheduling_module, _MARKER, False):
        return

    @functools.wraps(scheduling_module._render_create_schedule)
    def render_create_schedule_feedback(
        member_id: str,
        member_tz: str,
        practitioner_id: str,
        source_tz: str,
    ) -> None:
        _consume_pending_reset(scheduling_module)
        _render_feedback_styles()
        version = int(st.session_state.get(scheduling_module._CREATE_VERSION_KEY, 1) or 1)
        prefix = f"hm_admin_sched_create_v{version}_"
        practitioner_tz = _text(
            st.session_state.get(scheduling_module._SELECTED_TIMEZONE_KEY)
        )

        st.markdown("<span class='hm-sched-create-anchor'></span>", unsafe_allow_html=True)
        form_col, day_col = st.columns([3, 1], gap="small")

        with form_col:
            with st.container(border=True):
                st.markdown(
                    "<div class='hm-sched-section-title'>Create Schedule / Notify Member</div>",
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
                        value=scheduling_module.today_in_timezone(source_tz),
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
                    height=88,
                    key=prefix + "notes",
                )

                preview: dict[str, Any] = {}
                preview_error = ""
                try:
                    preview = scheduling_module.build_dual_time_context(
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
                    scheduling_module._render_time_context(
                        preview,
                        "Timezone confirmation before creating the schedule",
                        member_first=False,
                    )

                capacity = scheduling_module.schedule_capacity(member_id, schedule_date)
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
                    st.warning(
                        capacity.get("message")
                        or "A package-limit override is required."
                    )
                    if scheduling_module.current_user_is_admin():
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
                        st.error(
                            "Only Admin or Super Admin can override package scheduling limits."
                        )

                if st.button(
                    "Create Schedule / Notify Member",
                    type="primary",
                    use_container_width=True,
                    key=prefix + "submit",
                    disabled=bool(preview_error),
                ):
                    if blocked and (not override or not override_reason):
                        st.error(
                            "Enter the mandatory Admin/Super Admin override reason before creating this schedule."
                        )
                        return
                    st.session_state["hm_package_schedule_limit_override"] = bool(
                        blocked and override
                    )
                    st.session_state[
                        "hm_package_schedule_limit_override_reason"
                    ] = override_reason
                    try:
                        created = scheduling_module.create_timezone_aware_member_schedule(
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
                        st.session_state.pop(
                            "hm_package_schedule_limit_override", None
                        )
                        st.session_state.pop(
                            "hm_package_schedule_limit_override_reason", None
                        )
                    if created.get("error"):
                        st.error(created.get("error"))
                        return
                    st.session_state[scheduling_module._FLASH_KEY] = {
                        "kind": "success",
                        "message": "Schedule created. A fresh form is ready for the next schedule.",
                    }
                    st.session_state[scheduling_module._CREATE_CLEANUP_KEY] = version
                    st.session_state[scheduling_module._CREATE_VERSION_KEY] = version + 1
                    st.session_state[scheduling_module._SECTION_KEY] = "create"
                    st.rerun()

        with day_col:
            _render_day_schedule(
                _admin_schedule_for_date(schedule_date, practitioner_id),
                schedule_date,
            )

    scheduling_module._render_create_schedule = render_create_schedule_feedback
    setattr(scheduling_module, _MARKER, True)
