from __future__ import annotations

import contextlib
import functools
import inspect


_DAILY_LOG_LABELS = ("Food Journal", "Exercise Journal")
_DAILY_LOG_SELECTOR_KEY = "hm_daily_log_active_journal"
_DAILY_LOG_TAB_MARKER = "_hm_daily_log_tab_isolation_v2"
_DAILY_LOG_LAYOUT_MARKER = "_hm_exercise_layout_v4_installed"


def _is_daily_log_call(frame_globals: dict) -> bool:
    page_file = str(frame_globals.get("__file__") or "").replace("\\", "/")
    return page_file.endswith("/pages/18_Daily_Log.py") or page_file.endswith(
        "pages/18_Daily_Log.py"
    )


def _activate_daily_log_journal(label: str) -> None:
    import streamlit as st

    if label in _DAILY_LOG_LABELS:
        st.session_state[_DAILY_LOG_SELECTOR_KEY] = label


def _install_daily_log_tab_isolation() -> None:
    """Render only the selected Daily Log journal using stable button controls."""

    import streamlit as st

    current_tabs = st.tabs
    if getattr(current_tabs, _DAILY_LOG_TAB_MARKER, False):
        return

    @functools.wraps(current_tabs)
    def isolated_daily_log_tabs(labels, *args, **kwargs):
        normalized_labels = tuple(str(label) for label in labels)
        caller = inspect.currentframe().f_back
        frame_globals = caller.f_globals if caller is not None else {}

        if normalized_labels != _DAILY_LOG_LABELS or not _is_daily_log_call(
            frame_globals
        ):
            return current_tabs(labels, *args, **kwargs)

        current_value = st.session_state.get(
            _DAILY_LOG_SELECTOR_KEY,
            _DAILY_LOG_LABELS[0],
        )
        if current_value not in _DAILY_LOG_LABELS:
            current_value = _DAILY_LOG_LABELS[0]
            st.session_state[_DAILY_LOG_SELECTOR_KEY] = current_value

        st.markdown(
            """
<style id="hm-daily-log-journal-selector-v3">
.hm-daily-log-selector-anchor{
  display:block;height:0;min-height:0;margin:0;padding:0;overflow:hidden;
}
.hm-daily-log-selector-anchor + div[data-testid="stHorizontalBlock"]{
  gap:.55rem!important;margin:.05rem 0 .20rem 0!important;
}
.hm-daily-log-selector-anchor + div[data-testid="stHorizontalBlock"] button{
  min-height:2.75rem!important;border-radius:14px!important;font-weight:900!important;
}
</style>
            """,
            unsafe_allow_html=True,
        )
        st.markdown(
            "<span class='hm-daily-log-selector-anchor'></span>",
            unsafe_allow_html=True,
        )
        food_col, exercise_col = st.columns(2, gap="small")
        with food_col:
            st.button(
                "Food Journal",
                key="hm_daily_log_food_journal_selector",
                type=(
                    "primary"
                    if current_value == _DAILY_LOG_LABELS[0]
                    else "secondary"
                ),
                use_container_width=True,
                on_click=_activate_daily_log_journal,
                args=(_DAILY_LOG_LABELS[0],),
            )
        with exercise_col:
            st.button(
                "Exercise Journal",
                key="hm_daily_log_exercise_journal_selector",
                type=(
                    "primary"
                    if current_value == _DAILY_LOG_LABELS[1]
                    else "secondary"
                ),
                use_container_width=True,
                on_click=_activate_daily_log_journal,
                args=(_DAILY_LOG_LABELS[1],),
            )

        food_renderer = frame_globals.get("_render_food_journal")
        exercise_renderer = frame_globals.get("_render_exercise_journal")

        if callable(food_renderer) and not getattr(
            food_renderer,
            _DAILY_LOG_TAB_MARKER,
            False,
        ):

            @functools.wraps(food_renderer)
            def render_food_only_when_selected(*render_args, **render_kwargs):
                if (
                    st.session_state.get(
                        _DAILY_LOG_SELECTOR_KEY,
                        _DAILY_LOG_LABELS[0],
                    )
                    != _DAILY_LOG_LABELS[0]
                ):
                    return None
                return food_renderer(*render_args, **render_kwargs)

            setattr(render_food_only_when_selected, _DAILY_LOG_TAB_MARKER, True)
            frame_globals["_render_food_journal"] = render_food_only_when_selected

        if callable(exercise_renderer) and not getattr(
            exercise_renderer,
            _DAILY_LOG_TAB_MARKER,
            False,
        ):

            @functools.wraps(exercise_renderer)
            def render_exercise_only_when_selected(*render_args, **render_kwargs):
                if (
                    st.session_state.get(
                        _DAILY_LOG_SELECTOR_KEY,
                        _DAILY_LOG_LABELS[0],
                    )
                    != _DAILY_LOG_LABELS[1]
                ):
                    return None
                return exercise_renderer(*render_args, **render_kwargs)

            setattr(render_exercise_only_when_selected, _DAILY_LOG_TAB_MARKER, True)
            frame_globals[
                "_render_exercise_journal"
            ] = render_exercise_only_when_selected

        return [contextlib.nullcontext(), contextlib.nullcontext()]

    setattr(isolated_daily_log_tabs, _DAILY_LOG_TAB_MARKER, True)
    isolated_daily_log_tabs._hm_original_tabs = current_tabs
    st.tabs = isolated_daily_log_tabs


def install_member_exercise_journal_table() -> None:
    """Install the aligned Exercise Journal and the stable Daily Log selector."""

    from components import member_exercise_journal as journal
    from components.member_exercise_journal_layout_v4 import (
        render_member_exercise_journal_layout_v4,
    )

    if not getattr(journal, _DAILY_LOG_LAYOUT_MARKER, False):

        @functools.wraps(render_member_exercise_journal_layout_v4)
        def contextual_exercise_renderer(*args, **kwargs):
            if kwargs.get("key_prefix") == "hm_daily_log_exercise":
                kwargs["heading"] = ""
                kwargs["show_build_note"] = False
            return render_member_exercise_journal_layout_v4(*args, **kwargs)

        journal.render_member_exercise_journal = contextual_exercise_renderer
        journal._hm_editable_table_installed = True
        setattr(journal, _DAILY_LOG_LAYOUT_MARKER, True)

    _install_daily_log_tab_isolation()
