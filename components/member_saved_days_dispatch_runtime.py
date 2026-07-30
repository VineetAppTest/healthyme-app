from __future__ import annotations

import datetime as dt
import functools
import inspect
from zoneinfo import ZoneInfo

import streamlit as st


_MARKER = "_hm_member_saved_days_dispatch_runtime_v2"
_SAVED_BUTTON_PREFIX = "hm_h9a4c_load_"
_SAVED_FROM_KEY = "hm_h9a4c_saved_from"
_SAVED_TO_KEY = "hm_h9a4c_saved_to"
_FILTER_INIT_KEY = "_hm_saved_days_filter_initialized_v2"


def _frame_file(frame) -> str:
    return str((frame.f_globals if frame is not None else {}).get("__file__") or "").replace("\\", "/")


def _find_saved_days_frame():
    frame = inspect.currentframe().f_back
    for _ in range(14):
        if frame is None:
            break
        page_file = _frame_file(frame)
        function_name = str(frame.f_code.co_name or "")
        if (
            (page_file.endswith("/pages/18_Daily_Log.py") or page_file.endswith("pages/18_Daily_Log.py"))
            and function_name == "_render_saved_days"
        ):
            return frame
        frame = frame.f_back
    return None


def _india_today() -> dt.date:
    return dt.datetime.now(ZoneInfo("Asia/Kolkata")).date()


def install_member_saved_days_dispatch_runtime() -> None:
    current_date_input = st.date_input
    current_markdown = st.markdown
    current_button = st.button
    if getattr(current_button, _MARKER, False):
        return

    state = {"rendered": False}

    @functools.wraps(current_date_input)
    def date_input_with_outer_seven_day_default(label, *args, **kwargs):
        saved_frame = _find_saved_days_frame()
        key = str(kwargs.get("key") or "")
        if saved_frame is not None and key in {_SAVED_FROM_KEY, _SAVED_TO_KEY}:
            if not st.session_state.get(_FILTER_INIT_KEY):
                today = _india_today()
                st.session_state[_SAVED_FROM_KEY] = today - dt.timedelta(days=6)
                st.session_state[_SAVED_TO_KEY] = today
                st.session_state[_FILTER_INIT_KEY] = True
        return current_date_input(label, *args, **kwargs)

    @functools.wraps(current_markdown)
    def markdown_with_outer_saved_reset(body, *args, **kwargs):
        saved_frame = _find_saved_days_frame()
        if saved_frame is not None and str(body or "").strip() == "### View Saved Days":
            state["rendered"] = False
        return current_markdown(body, *args, **kwargs)

    @functools.wraps(current_button)
    def button_with_outer_saved_summary(label, *args, **kwargs):
        saved_frame = _find_saved_days_frame()
        key = str(kwargs.get("key") or "")
        if saved_frame is None or not key.startswith(_SAVED_BUTTON_PREFIX):
            return current_button(label, *args, **kwargs)
        if not state["rendered"]:
            from components.member_saved_days_home_cleanup import _render_filtered_meal_summary

            filtered_days = list(saved_frame.f_locals.get("filtered_days") or [])
            _render_filtered_meal_summary(filtered_days)
            state["rendered"] = True
        return False

    setattr(date_input_with_outer_seven_day_default, _MARKER, True)
    setattr(markdown_with_outer_saved_reset, _MARKER, True)
    setattr(button_with_outer_saved_summary, _MARKER, True)
    st.date_input = date_input_with_outer_seven_day_default
    st.markdown = markdown_with_outer_saved_reset
    st.button = button_with_outer_saved_summary
