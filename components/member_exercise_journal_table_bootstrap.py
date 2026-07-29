from __future__ import annotations

import contextlib
import functools
import inspect


_DAILY_LOG_LABELS = ("Food Journal", "Exercise Journal")
_DAILY_LOG_SELECTOR_KEY = "hm_daily_log_active_journal"
_DAILY_LOG_TAB_MARKER = "_hm_daily_log_tab_isolation"


def _is_daily_log_call(frame_globals: dict) -> bool:
    page_file = str(frame_globals.get("__file__") or "").replace("\\", "/")
    return page_file.endswith("/pages/18_Daily_Log.py") or page_file.endswith(
        "pages/18_Daily_Log.py"
    )


def _install_daily_log_tab_isolation() -> None:
    """Render only the selected Daily Log journal body.

    Streamlit's native tabs execute both bodies and rely on browser-side hiding. The
    production screenshot showed that hiding fail, exposing Food Journal above Exercise
    Journal. This wrapper is limited to the exact Daily Log two-tab call and leaves all
    other application tabs untouched.
    """

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

        st.markdown(
            """
<style id="hm-daily-log-journal-selector-v1">
div[data-testid="stButtonGroup"]{width:100%;margin:.15rem 0 1rem 0;}
div[data-testid="stButtonGroup"] [role="radiogroup"]{width:100%;gap:.55rem;}
div[data-testid="stButtonGroup"] button{
  flex:1 1 0!important;min-height:2.75rem!important;border:1.4px solid #D8A84E!important;
  border-radius:14px!important;background:#FFFFFF!important;color:#064E3B!important;
  font-weight:900!important;box-shadow:0 7px 16px rgba(6,78,59,.07)!important;
}
div[data-testid="stButtonGroup"] button[aria-pressed="true"]{
  background:linear-gradient(135deg,#064E3B 0%,#0F766E 100%)!important;
  color:#FFFFFF!important;border-color:#064E3B!important;
}
div[data-testid="stButtonGroup"] button[aria-pressed="true"] *{color:#FFFFFF!important;}
</style>
            """,
            unsafe_allow_html=True,
        )

        selector_kwargs = {
            "key": _DAILY_LOG_SELECTOR_KEY,
            "selection_mode": "single",
            "label_visibility": "collapsed",
            "width": "stretch",
        }
        if _DAILY_LOG_SELECTOR_KEY not in st.session_state:
            selector_kwargs["default"] = _DAILY_LOG_LABELS[0]

        selected = st.segmented_control(
            "Daily Log Journal",
            list(_DAILY_LOG_LABELS),
            **selector_kwargs,
        )
        if selected not in _DAILY_LOG_LABELS:
            selected = _DAILY_LOG_LABELS[0]
            st.session_state[_DAILY_LOG_SELECTOR_KEY] = selected

        food_renderer = frame_globals.get("_render_food_journal")
        exercise_renderer = frame_globals.get("_render_exercise_journal")

        if callable(food_renderer) and not getattr(
            food_renderer, _DAILY_LOG_TAB_MARKER, False
        ):

            @functools.wraps(food_renderer)
            def render_food_only_when_selected(*render_args, **render_kwargs):
                if (
                    st.session_state.get(
                        _DAILY_LOG_SELECTOR_KEY, _DAILY_LOG_LABELS[0]
                    )
                    != _DAILY_LOG_LABELS[0]
                ):
                    return None
                return food_renderer(*render_args, **render_kwargs)

            setattr(render_food_only_when_selected, _DAILY_LOG_TAB_MARKER, True)
            frame_globals["_render_food_journal"] = render_food_only_when_selected

        if callable(exercise_renderer) and not getattr(
            exercise_renderer, _DAILY_LOG_TAB_MARKER, False
        ):

            @functools.wraps(exercise_renderer)
            def render_exercise_only_when_selected(*render_args, **render_kwargs):
                if (
                    st.session_state.get(
                        _DAILY_LOG_SELECTOR_KEY, _DAILY_LOG_LABELS[0]
                    )
                    != _DAILY_LOG_LABELS[1]
                ):
                    return None
                return exercise_renderer(*render_args, **render_kwargs)

            setattr(render_exercise_only_when_selected, _DAILY_LOG_TAB_MARKER, True)
            frame_globals[
                "_render_exercise_journal"
            ] = render_exercise_only_when_selected

        # The page's existing ``with food_tab`` / ``with exercise_tab`` structure is
        # preserved. These neutral contexts execute the conditional wrappers above.
        return [contextlib.nullcontext(), contextlib.nullcontext()]

    setattr(isolated_daily_log_tabs, _DAILY_LOG_TAB_MARKER, True)
    isolated_daily_log_tabs._hm_original_tabs = current_tabs
    st.tabs = isolated_daily_log_tabs


def install_member_exercise_journal_table() -> None:
    """Install the editable journal renderer and isolate the Daily Log selector."""

    from components import member_exercise_journal as journal
    from components.member_exercise_journal_table import (
        render_member_exercise_journal_table,
    )

    if not getattr(journal, "_hm_editable_table_installed", False):
        journal._hm_editable_table_installed = True
        journal.render_member_exercise_journal = render_member_exercise_journal_table

    _install_daily_log_tab_isolation()
