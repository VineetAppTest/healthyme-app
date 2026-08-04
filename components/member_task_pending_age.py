from __future__ import annotations

import datetime as dt
import functools
import inspect
from zoneinfo import ZoneInfo

import streamlit as st


_MARKER = "_hm_member_task_pending_age_v1"
_MEMBER_TIMEZONE = ZoneInfo("Asia/Kolkata")


def _frame_file(frame) -> str:
    return str((frame.f_globals if frame is not None else {}).get("__file__") or "").replace("\\", "/")


def _member_task_frame():
    frame = inspect.currentframe().f_back
    for _ in range(28):
        if frame is None:
            break
        path = _frame_file(frame)
        if (
            path.endswith("/pages/02_Member_Home.py")
            or path.endswith("pages/02_Member_Home.py")
        ) and str(frame.f_code.co_name or "") == "_render_task_progress":
            return frame
        frame = frame.f_back
    return None


def _parse_due_date(value: object) -> dt.date | None:
    if isinstance(value, dt.datetime):
        return value.date()
    if isinstance(value, dt.date):
        return value
    text = str(value or "").strip()
    if not text or text.lower() in {"not set", "none", "nan"}:
        return None
    candidate = text[:10] if "T" in text else text
    for fmt in (
        "%Y-%m-%d",
        "%Y/%m/%d",
        "%d-%m-%Y",
        "%d/%m/%Y",
        "%d %b %Y",
        "%d %B %Y",
    ):
        try:
            return dt.datetime.strptime(candidate, fmt).date()
        except ValueError:
            continue
    return None


def _pending_age_label() -> tuple[str, str]:
    frame = _member_task_frame()
    current_instance = dict(
        (frame.f_locals.get("current_instance") if frame is not None else {}) or {}
    )
    due_date = _parse_due_date(current_instance.get("due_date"))
    if due_date is None:
        return "Task due date is not set", "neutral"
    today = dt.datetime.now(_MEMBER_TIMEZONE).date()
    delta = (today - due_date).days
    if delta > 0:
        unit = "day" if delta == 1 else "days"
        return f"Task is pending for {delta} {unit}", "overdue"
    if delta == 0:
        return "Task is pending for 0 days", "today"
    remaining = abs(delta)
    unit = "day" if remaining == 1 else "days"
    return f"Task is due in {remaining} {unit}", "future"


def install_member_task_pending_age() -> None:
    current_markdown = st.markdown
    if getattr(current_markdown, _MARKER, False):
        return

    @functools.wraps(current_markdown)
    def markdown_with_pending_age(body, *args, **kwargs):
        if (
            isinstance(body, str)
            and "<div class='hm-v990-task-progress'>" in body
            and _member_task_frame() is not None
        ):
            label, state = _pending_age_label()
            alert = (
                "<div class='hm-task-alert-row'>"
                "<span class='hm-task-alert-pill'>ACTION REQUIRED</span>"
                f"<span class='hm-task-pending-age {state}'>{label}</span>"
                "</div>"
            )
            body = body.replace(
                "<div class='hm-v990-task-progress'>",
                "<div class='hm-v990-task-progress'>" + alert,
                1,
            )
        return current_markdown(body, *args, **kwargs)

    setattr(markdown_with_pending_age, _MARKER, True)
    st.markdown = markdown_with_pending_age

    current_markdown(
        """
<style id="hm-member-task-pending-age-v1">
.hm-v990-task-progress::before{display:none!important;content:none!important;}
.hm-task-alert-row{display:flex;align-items:center;gap:.55rem;flex-wrap:wrap;margin:0 0 .48rem 0;}
.hm-task-alert-pill{display:inline-flex;align-items:center;padding:.30rem .62rem;border-radius:999px;background:#FEE2E2;border:1px solid #DC2626;color:#B91C1C;font-size:.88rem;font-weight:950;letter-spacing:.02em;text-transform:uppercase;line-height:1.1;}
.hm-task-pending-age{display:inline-flex;align-items:center;padding:.27rem .56rem;border-radius:999px;font-size:.78rem;font-weight:900;line-height:1.1;}
.hm-task-pending-age.overdue,.hm-task-pending-age.today{background:#FFF1F2;border:1px solid #FB7185;color:#BE123C;}
.hm-task-pending-age.future{background:#DCFCE7;border:1px solid #22C55E;color:#166534;}
.hm-task-pending-age.neutral{background:#F1F5F9;border:1px solid #CBD5E1;color:#475569;}
</style>
""",
        unsafe_allow_html=True,
    )
