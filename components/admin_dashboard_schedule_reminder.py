from __future__ import annotations

import datetime as dt
import html
from typing import Any

import streamlit as st

from components.db import schedule_display_status_label_v104b11
from components.storage_backend import load_state


UTC = dt.timezone.utc
OPEN_STATUSES = {"scheduled", "acknowledged"}


def _text(value: object) -> str:
    return str(value or "").strip()


def _safe(value: object) -> str:
    return html.escape(_text(value))


def _parse_time(value: object) -> dt.time:
    raw = _text(value).upper()
    for fmt in ("%I:%M %p", "%H:%M", "%I %p", "%H"):
        try:
            return dt.datetime.strptime(raw, fmt).time()
        except ValueError:
            pass
    return dt.time(0, 0)


def _parse_start_utc(row: dict[str, Any]) -> dt.datetime | None:
    start_utc = _text(row.get("start_at_utc"))
    if start_utc:
        try:
            parsed = dt.datetime.fromisoformat(start_utc.replace("Z", "+00:00"))
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=UTC)
            return parsed.astimezone(UTC)
        except ValueError:
            pass
    schedule_date = _text(
        row.get("practitioner_local_date") or row.get("schedule_date")
    )
    if not schedule_date:
        return None
    try:
        parsed_date = dt.date.fromisoformat(schedule_date[:10])
    except ValueError:
        return None
    local_start = _parse_time(
        row.get("practitioner_local_start_time") or row.get("start_time")
    )
    return dt.datetime.combine(parsed_date, local_start, tzinfo=UTC)


def _member_name(row: dict[str, Any]) -> str:
    return (
        _text(row.get("member_name"))
        or _text(row.get("member_email"))
        or _text(row.get("member_id"))
        or "Member"
    )


def _practitioner_time(row: dict[str, Any]) -> str:
    date_label = _text(row.get("practitioner_local_date") or row.get("schedule_date"))
    start = _text(row.get("practitioner_local_start_time") or row.get("start_time"))
    end = _text(row.get("practitioner_local_end_time") or row.get("end_time"))
    time_label = " - ".join(value for value in (start, end) if value) or "Time not set"
    return " · ".join(value for value in (date_label, time_label) if value)


def upcoming_admin_schedule_rows(
    practitioner_id: object,
    *,
    now_utc: dt.datetime | None = None,
    hours: int = 48,
) -> list[dict[str, str]]:
    state = load_state()
    now_value = (now_utc or dt.datetime.now(UTC)).astimezone(UTC)
    window_end = now_value + dt.timedelta(hours=hours)
    practitioner_key = _text(practitioner_id) or "admin"
    output: list[tuple[dt.datetime, dict[str, str]]] = []
    for raw in state.get("schedules", []) or []:
        if not isinstance(raw, dict):
            continue
        status = _text(raw.get("status") or "scheduled").lower()
        if status not in OPEN_STATUSES:
            continue
        created_by = _text(raw.get("created_by") or raw.get("actor_id"))
        if created_by and created_by != practitioner_key:
            continue
        start = _parse_start_utc(raw)
        if not start or start < now_value or start > window_end:
            continue
        row = {
            "Member": _member_name(raw),
            "Session": _text(raw.get("title") or raw.get("schedule_type"))
            or "Scheduled session",
            "Practitioner Time": _practitioner_time(raw),
            "Status": schedule_display_status_label_v104b11(raw),
        }
        output.append((start, row))
    output.sort(key=lambda item: (item[0], item[1]["Member"].casefold()))
    return [row for _start, row in output]


def render_admin_upcoming_schedule_reminder(practitioner_id: object) -> None:
    rows = upcoming_admin_schedule_rows(practitioner_id)
    st.markdown(
        """
<style id="hm-admin-upcoming-schedule-reminder-v1">
.hm-admin-upcoming-wrap{border:1px solid #E3C98E;background:#FFFDF8;border-radius:16px;padding:.68rem .74rem;margin:.42rem 0 .34rem}
.hm-admin-upcoming-title{display:flex;align-items:center;justify-content:space-between;gap:.5rem;color:#064E3B;font-size:.90rem;font-weight:950;margin:0 0 .42rem}
.hm-admin-upcoming-pill{border:1px solid #D9C28F;background:#FFF7E6;color:#72551A;border-radius:999px;padding:.14rem .42rem;font-size:.68rem;font-weight:900;white-space:nowrap}
.hm-admin-upcoming-table-wrap{overflow-x:auto;border:1px solid #E3C98E;border-radius:12px;background:#fff}
.hm-admin-upcoming-table{width:100%;min-width:680px;border-collapse:collapse;font-size:.76rem;line-height:1.32}
.hm-admin-upcoming-table th{background:#FFF4DE;color:#064E3B;font-weight:950;text-align:left;padding:.42rem .48rem;border:1px solid #E3C98E;white-space:nowrap}
.hm-admin-upcoming-table td{color:#334155;font-weight:720;padding:.44rem .48rem;border:1px solid #F0E3C5;vertical-align:top}
</style>
        """,
        unsafe_allow_html=True,
    )
    st.markdown(
        "<div class='hm-admin-upcoming-wrap'>"
        "<div class='hm-admin-upcoming-title'>"
        f"<span>Upcoming Schedule for Admin</span><span class='hm-admin-upcoming-pill'>Next 48 hrs · {len(rows)}</span>"
        "</div>",
        unsafe_allow_html=True,
    )
    if rows:
        body = "".join(
            "<tr>"
            f"<td>{_safe(row['Member'])}</td>"
            f"<td>{_safe(row['Session'])}</td>"
            f"<td>{_safe(row['Practitioner Time'])}</td>"
            f"<td>{_safe(row['Status'])}</td>"
            "</tr>"
            for row in rows
        )
        st.markdown(
            "<div class='hm-admin-upcoming-table-wrap'><table class='hm-admin-upcoming-table'>"
            "<thead><tr><th>Member</th><th>Session</th><th>Practitioner Time</th><th>Status</th></tr></thead>"
            f"<tbody>{body}</tbody></table></div>",
            unsafe_allow_html=True,
        )
    else:
        st.caption("No Admin schedule is due in the next 48 hours.")
    if st.button(
        "Open Scheduling",
        key="hm_admin_dashboard_open_scheduling_from_upcoming",
        use_container_width=True,
    ):
        st.switch_page("pages/32_Admin_Scheduling.py")
    st.markdown("</div>", unsafe_allow_html=True)
