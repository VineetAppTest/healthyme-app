from __future__ import annotations

import datetime as dt
import functools
import inspect
from zoneinfo import ZoneInfo

import streamlit as st


_MARKER = "_hm_member_home_side_by_side_runtime_v6"
_MEMBER_TIMEZONE = ZoneInfo("Asia/Kolkata")


def _frame_file(frame) -> str:
    return str((frame.f_globals if frame is not None else {}).get("__file__") or "").replace("\\", "/")


def _is_member_home_frame(frame) -> bool:
    page_file = _frame_file(frame)
    return page_file.endswith("/pages/02_Member_Home.py") or page_file.endswith("pages/02_Member_Home.py")


def _frame_function(frame) -> str:
    return str((frame.f_code.co_name if frame is not None else "") or "")


def _member_home_frame(function_name: str):
    frame = inspect.currentframe().f_back
    for _ in range(24):
        if frame is None:
            break
        if _is_member_home_frame(frame) and _frame_function(frame) == function_name:
            return frame
        frame = frame.f_back
    return None


def _member_home_stack_has(function_name: str) -> bool:
    return _member_home_frame(function_name) is not None


def _parse_due_date(value) -> dt.date | None:
    if isinstance(value, dt.datetime):
        return value.date()
    if isinstance(value, dt.date):
        return value
    text = str(value or "").strip()
    if not text or text.lower() in {"not set", "none", "nan"}:
        return None
    candidate = text[:10] if "T" in text else text
    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%d-%m-%Y", "%d/%m/%Y", "%d %b %Y", "%d %B %Y"):
        try:
            return dt.datetime.strptime(candidate, fmt).date()
        except ValueError:
            continue
    try:
        return dt.date.fromisoformat(candidate)
    except ValueError:
        return None


def _task_due_state_class() -> str:
    frame = _member_home_frame("_render_task_progress")
    current_instance = dict((frame.f_locals.get("current_instance") if frame is not None else {}) or {})
    due_date = _parse_due_date(current_instance.get("due_date"))
    today = dt.datetime.now(_MEMBER_TIMEZONE).date()
    return "hm-task-overdue" if due_date is not None and due_date < today else "hm-task-before-due"


def _completed_task_button_label(label: object) -> str | None:
    text = str(label or "").strip()
    task_map = {
        "Start NSP Page 1": ("nsp1_completed", "NSP Page 1 Completed"),
        "Start NSP Page 2": ("nsp2_completed", "NSP Page 2 Completed"),
    }
    task = task_map.get(text)
    if task is None:
        return None
    frame = _member_home_frame("_render_task_progress")
    if frame is None:
        return None
    current_instance = dict(frame.f_locals.get("current_instance") or {})
    completed_key, completed_label = task
    return completed_label if bool(current_instance.get(completed_key)) else None


def install_member_home_side_by_side_runtime() -> None:
    """Keep task-state presentation helpers without relocating page sections.

    Upcoming Schedule and Messages are now owned directly by Member Home. The
    retired runtime used to move them into a dynamically created two-column row,
    which also introduced negative margins and made the global header regress
    whenever one of those sections appeared or disappeared.
    """

    current_markdown = st.markdown
    current_button = st.button
    if getattr(current_markdown, _MARKER, False):
        return

    @functools.wraps(current_markdown)
    def markdown_with_task_state(body, *args, **kwargs):
        if (
            _member_home_stack_has("_render_task_progress")
            and isinstance(body, str)
            and "hm-v990-task-progress" in body
        ):
            state_class = _task_due_state_class()
            body = body.replace(
                "hm-v990-task-progress",
                f"hm-v990-task-progress {state_class}",
                1,
            )
        return current_markdown(body, *args, **kwargs)

    @functools.wraps(current_button)
    def button_with_completed_task_labels(label, *args, **kwargs):
        completed_label = _completed_task_button_label(label)
        if completed_label is not None:
            label = completed_label
            kwargs = dict(kwargs)
            kwargs["disabled"] = True
        return current_button(label, *args, **kwargs)

    setattr(markdown_with_task_state, _MARKER, True)
    setattr(button_with_completed_task_labels, _MARKER, True)
    st.markdown = markdown_with_task_state
    st.button = button_with_completed_task_labels
