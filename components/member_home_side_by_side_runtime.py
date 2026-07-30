from __future__ import annotations

import functools
import inspect

import streamlit as st


_MARKER = "_hm_member_home_side_by_side_runtime_v2"


def _frame_file(frame) -> str:
    return str((frame.f_globals if frame is not None else {}).get("__file__") or "").replace("\\", "/")


def _is_member_home_frame(frame) -> bool:
    page_file = _frame_file(frame)
    return page_file.endswith("/pages/02_Member_Home.py") or page_file.endswith("pages/02_Member_Home.py")


def _frame_function(frame) -> str:
    return str((frame.f_code.co_name if frame is not None else "") or "")


def _member_home_stack_has(function_name: str) -> bool:
    frame = inspect.currentframe().f_back
    for _ in range(14):
        if frame is None:
            break
        if _is_member_home_frame(frame) and _frame_function(frame) == function_name:
            return True
        frame = frame.f_back
    return False


def install_member_home_side_by_side_runtime() -> None:
    from components import ui_common

    current_columns = st.columns
    current_markdown = st.markdown
    current_button = st.button
    current_expander = st.expander
    current_topbar = ui_common.topbar
    pair_state = {"pair": None}

    if getattr(current_topbar, _MARKER, False):
        return

    def ensure_pair():
        if pair_state["pair"] is None:
            left, right = current_columns([1, 1], gap="large")
            left.markdown("<span class='hm-home-side-col-anchor-v2'></span>", unsafe_allow_html=True)
            right.markdown("<span class='hm-home-side-col-anchor-v2'></span>", unsafe_allow_html=True)
            pair_state["pair"] = (left, right)
        return pair_state["pair"]

    @functools.wraps(current_topbar)
    def topbar_with_real_home_columns(title, *args, **kwargs):
        if str(title or "").strip() == "Member Home":
            pair_state["pair"] = None
        result = current_topbar(title, *args, **kwargs)
        if str(title or "").strip() == "Member Home":
            current_markdown(
                """
<style id="hm-member-home-real-columns-v2">
.hm-home-side-col-anchor-v2{display:none!important;height:0!important;margin:0!important;padding:0!important;}
div[data-testid="stHorizontalBlock"]:has(.hm-home-side-col-anchor-v2){align-items:flex-start!important;gap:1.25rem!important;margin:.42rem 0 .82rem 0!important;}
div[data-testid="stHorizontalBlock"]:has(.hm-home-side-col-anchor-v2)>div[data-testid="column"]{min-width:0!important;}
.hm-b13-message-shell{float:none!important;width:100%!important;max-width:none!important;margin:0!important;padding:0!important;border:0!important;background:transparent!important;box-shadow:none!important;}
.hm-b13-message-title{width:285px!important;margin:0 0 .52rem 0!important;}
.hm-b13-message-card{width:100%!important;max-width:none!important;margin:.42rem 0!important;}
div[data-testid="stExpander"]:has(.hm-upcoming-schedule-anchor){float:none!important;width:100%!important;max-width:none!important;margin:0!important;}
div[data-testid="stExpander"]:has(.hm-upcoming-schedule-anchor) .hm-v101-schedule-card{width:100%!important;max-width:none!important;margin:.42rem 0!important;}
@media(max-width:900px){div[data-testid="stHorizontalBlock"]:has(.hm-home-side-col-anchor-v2){display:flex!important;flex-direction:column!important;gap:.8rem!important;}div[data-testid="stHorizontalBlock"]:has(.hm-home-side-col-anchor-v2)>div{width:100%!important;min-width:100%!important}.hm-b13-message-title{width:100%!important}}
</style>
                """,
                unsafe_allow_html=True,
            )
        return result

    @functools.wraps(current_markdown)
    def markdown_in_message_column(body, *args, **kwargs):
        if _member_home_stack_has("_render_messages"):
            _, right = ensure_pair()
            return right.markdown(body, *args, **kwargs)
        return current_markdown(body, *args, **kwargs)

    @functools.wraps(current_button)
    def button_in_message_column(label, *args, **kwargs):
        if _member_home_stack_has("_render_messages"):
            _, right = ensure_pair()
            return right.button(label, *args, **kwargs)
        return current_button(label, *args, **kwargs)

    @functools.wraps(current_expander)
    def expander_in_schedule_column(label, *args, **kwargs):
        if _member_home_stack_has("_render_upcoming_schedules") and pair_state["pair"] is not None:
            left, _ = ensure_pair()
            return left.expander(label, *args, **kwargs)
        return current_expander(label, *args, **kwargs)

    setattr(topbar_with_real_home_columns, _MARKER, True)
    setattr(markdown_in_message_column, _MARKER, True)
    setattr(button_in_message_column, _MARKER, True)
    setattr(expander_in_schedule_column, _MARKER, True)
    ui_common.topbar = topbar_with_real_home_columns
    st.markdown = markdown_in_message_column
    st.button = button_in_message_column
    st.expander = expander_in_schedule_column
