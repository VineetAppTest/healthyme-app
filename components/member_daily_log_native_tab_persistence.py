from __future__ import annotations

import contextlib
import functools
import inspect
from types import FrameType

import streamlit as st


_MARKER = "_hm_member_daily_log_exclusive_rendering_v3"
_RENDER_MARKER = "_hm_member_daily_log_renderer_gate_v3"
_PAGE_SUFFIX = "pages/18_Daily_Log.py"
_LABELS = ("Food Journal", "Exercise Journal")
_SELECTOR_KEY = "hm_daily_log_active_journal"
_PERSISTED_SELECTOR_KEY = "_hm_member_daily_log_selected_journal_v3"


def _daily_log_frame() -> FrameType | None:
    """Return the live Daily Log page frame, even through other wrappers."""

    for frame_info in inspect.stack():
        frame = frame_info.frame
        page_file = str(frame.f_globals.get("__file__") or "").replace("\\", "/")
        if page_file.endswith(_PAGE_SUFFIX):
            return frame
    return None


def _activate_journal(label: str) -> None:
    if label in _LABELS:
        # Keep one protected authority outside the public Daily Log widget prefix.
        # Some explicit save/load rerun paths clear page-scoped keys; the protected
        # value restores the selected journal before either renderer is dispatched.
        st.session_state[_PERSISTED_SELECTOR_KEY] = label
        st.session_state[_SELECTOR_KEY] = label


def _selected_journal() -> str:
    persisted = str(st.session_state.get(_PERSISTED_SELECTOR_KEY) or "")
    visible = str(st.session_state.get(_SELECTOR_KEY) or "")

    if persisted in _LABELS:
        selected = persisted
    elif visible in _LABELS:
        selected = visible
    else:
        selected = _LABELS[0]

    # Repair both keys on every rerun. The protected key remains authoritative,
    # while the public key stays compatible with the historical Daily Log layer.
    st.session_state[_PERSISTED_SELECTOR_KEY] = selected
    st.session_state[_SELECTOR_KEY] = selected
    return selected


def _render_selector() -> None:
    selected = _selected_journal()
    st.markdown(
        """
<style id="hm-daily-log-exclusive-selector-v3">
div[data-testid="stElementContainer"]:has(style#hm-daily-log-exclusive-selector-v3){
  display:none!important;height:0!important;min-height:0!important;
  margin:0!important;padding:0!important;overflow:hidden!important;
}
.hm-daily-log-exclusive-anchor{display:block;height:0;margin:0;padding:0;overflow:hidden;}
.hm-daily-log-exclusive-anchor + div[data-testid="stHorizontalBlock"]{
  gap:.55rem!important;margin:.05rem 0 .75rem 0!important;
}
.hm-daily-log-exclusive-anchor + div[data-testid="stHorizontalBlock"] button{
  min-height:2.75rem!important;border-radius:14px!important;font-weight:900!important;
}
</style>
        """,
        unsafe_allow_html=True,
    )
    st.markdown(
        "<span class='hm-daily-log-exclusive-anchor'></span>",
        unsafe_allow_html=True,
    )
    food_col, exercise_col = st.columns(2, gap="small")
    with food_col:
        st.button(
            _LABELS[0],
            key="hm_daily_log_food_journal_selector_v3",
            type="primary" if selected == _LABELS[0] else "secondary",
            use_container_width=True,
            on_click=_activate_journal,
            args=(_LABELS[0],),
        )
    with exercise_col:
        st.button(
            _LABELS[1],
            key="hm_daily_log_exercise_journal_selector_v3",
            type="primary" if selected == _LABELS[1] else "secondary",
            use_container_width=True,
            on_click=_activate_journal,
            args=(_LABELS[1],),
        )


def _gate_renderer(frame_globals: dict, name: str, label: str) -> None:
    renderer = frame_globals.get(name)
    if not callable(renderer) or getattr(renderer, _RENDER_MARKER, False):
        return

    @functools.wraps(renderer)
    def render_only_when_selected(*args, **kwargs):
        if _selected_journal() != label:
            return None
        return renderer(*args, **kwargs)

    setattr(render_only_when_selected, _RENDER_MARKER, True)
    setattr(render_only_when_selected, "_hm_original_renderer", renderer)
    frame_globals[name] = render_only_when_selected


def _install_renderer_gates(frame: FrameType) -> None:
    _gate_renderer(frame.f_globals, "_render_food_journal", _LABELS[0])
    _gate_renderer(frame.f_globals, "_render_exercise_journal", _LABELS[1])


def install_member_daily_log_native_tab_persistence() -> None:
    """Replace Daily Log tabs with deterministic server-side exclusive rendering.

    The historical function name is retained for bootstrap compatibility. The runtime
    intentionally does not call Streamlit tabs: both page blocks receive null contexts,
    while the renderer gates ensure that only the selected journal executes.
    """

    current_tabs = st.tabs
    if getattr(current_tabs, _MARKER, False):
        return

    @functools.wraps(current_tabs)
    def exclusive_daily_log_tabs(labels, *args, **kwargs):
        normalized = tuple(str(label) for label in labels)
        if normalized != _LABELS:
            return current_tabs(labels, *args, **kwargs)

        page_frame = _daily_log_frame()
        if page_frame is None:
            return current_tabs(labels, *args, **kwargs)

        _selected_journal()
        _render_selector()
        _install_renderer_gates(page_frame)
        return [contextlib.nullcontext(), contextlib.nullcontext()]

    setattr(exclusive_daily_log_tabs, _MARKER, True)
    setattr(exclusive_daily_log_tabs, "_hm_original_tabs", current_tabs)
    st.tabs = exclusive_daily_log_tabs
