from __future__ import annotations

import datetime as dt
import functools
import inspect
from zoneinfo import ZoneInfo

import streamlit as st


_MARKER = "_hm_member_task_pending_age_v2"
_MEMBER_TIMEZONE = ZoneInfo("Asia/Kolkata")

# This stylesheet is inserted with the task card itself. Member Home's accepted
# side-by-side runtime injects its own ACTION REQUIRED pseudo-element during the
# topbar render, so a later task-local stylesheet is required to suppress that
# older label and keep the two real badges on the same line.
_RUNTIME_STYLE = """
<style id="hm-member-task-pending-age-runtime-v2">
.hm-v990-task-progress::before{
  display:none!important;
  visibility:hidden!important;
  content:none!important;
  width:0!important;
  height:0!important;
  margin:0!important;
  padding:0!important;
}
.hm-task-alert-row{
  display:flex!important;
  align-items:center!important;
  gap:.45rem!important;
  flex-wrap:wrap!important;
  margin:0 0 .48rem 0!important;
}
.hm-task-alert-pill{
  display:inline-flex!important;
  align-items:center!important;
  padding:.30rem .62rem!important;
  border-radius:999px!important;
  background:#FEE2E2!important;
  border:1px solid #DC2626!important;
  color:#B91C1C!important;
  font-size:.88rem!important;
  font-weight:950!important;
  letter-spacing:.02em!important;
  text-transform:uppercase!important;
  line-height:1.1!important;
  white-space:nowrap!important;
}
.hm-task-pending-age{
  display:inline-flex!important;
  align-items:center!important;
  padding:.27rem .56rem!important;
  border-radius:999px!important;
  font-size:.78rem!important;
  font-weight:900!important;
  line-height:1.1!important;
  white-space:nowrap!important;
}
.hm-task-pending-age.overdue,
.hm-task-pending-age.today{
  background:#FFF1F2!important;
  border:1px solid #FB7185!important;
  color:#BE123C!important;
}
.hm-task-pending-age.future{
  background:#DCFCE7!important;
  border:1px solid #22C55E!important;
  color:#166534!important;
}
.hm-task-pending-age.neutral{
  background:#F1F5F9!important;
  border:1px solid #CBD5E1!important;
  color:#475569!important;
}
</style>
"""


def _frame_file(frame) -> str:
    return str(
        (frame.f_globals if frame is not None else {}).get("__file__") or ""
    ).replace("\\", "/")


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
                _RUNTIME_STYLE
                + "<div class='hm-task-alert-row'>"
                + "<span class='hm-task-alert-pill'>ACTION REQUIRED</span>"
                + f"<span class='hm-task-pending-age {state}'>{label}</span>"
                + "</div>"
            )
            body = body.replace(
                "<div class='hm-v990-task-progress'>",
                "<div class='hm-v990-task-progress'>" + alert,
                1,
            )
        return current_markdown(body, *args, **kwargs)

    setattr(markdown_with_pending_age, _MARKER, True)
    st.markdown = markdown_with_pending_age
