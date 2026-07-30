from __future__ import annotations

import contextlib
import datetime as dt
import functools
import inspect


_DAILY_LOG_LABELS = ("Food Journal", "Exercise Journal")
_DAILY_LOG_SELECTOR_KEY = "hm_daily_log_active_journal"
_DAILY_LOG_TAB_MARKER = "_hm_daily_log_tab_isolation_v3"
_DAILY_LOG_LAYOUT_MARKER = "_hm_exercise_layout_v4_installed"
_DAILY_LOG_WIDGET_MARKER = "_hm_daily_log_widget_corrections_v1"
_FOOD_DATE_KEY = "hm_food_journal_date"
_FOOD_PENDING_DATE_KEY = "hm_food_journal_pending_date"
_SAVED_DAY_BUTTON_PREFIX = "hm_h9a4c_load_"
_FLUID_TIME_PREFIX = "hm_h9a4c_fluid_time_"


def _is_daily_log_call(frame_globals: dict) -> bool:
    page_file = str(frame_globals.get("__file__") or "").replace("\\", "/")
    return page_file.endswith("/pages/18_Daily_Log.py") or page_file.endswith(
        "pages/18_Daily_Log.py"
    )


def _activate_daily_log_journal(label: str) -> None:
    import streamlit as st

    if label in _DAILY_LOG_LABELS:
        st.session_state[_DAILY_LOG_SELECTOR_KEY] = label


def _parse_saved_date(value: object) -> dt.date | None:
    text = str(value or "").strip()
    try:
        return dt.date.fromisoformat(text[:10])
    except (TypeError, ValueError):
        return None


def _parse_compact_time(value: object) -> dt.time | None:
    if isinstance(value, dt.time):
        return value.replace(second=0, microsecond=0)
    text = str(value or "").strip().upper()
    if not text:
        return None
    for fmt in ("%I:%M %p", "%H:%M", "%I %p"):
        try:
            return dt.datetime.strptime(text, fmt).time()
        except ValueError:
            pass
    return None


def _display_compact_time(value: object) -> str:
    parsed = _parse_compact_time(value)
    if parsed is None:
        return str(value or "").strip()
    return parsed.strftime("%I:%M %p").lstrip("0")


def _install_daily_log_widget_corrections() -> None:
    """Correct Food Journal widget state and fluid-time presentation only."""

    import streamlit as st

    current_date_input = st.date_input
    if getattr(current_date_input, _DAILY_LOG_WIDGET_MARKER, False):
        return

    current_button = st.button
    current_time_input = st.time_input
    current_text_input = st.text_input

    @functools.wraps(current_date_input)
    def date_input_with_pending_saved_day(label, *args, **kwargs):
        key = str(kwargs.get("key") or "")
        if key == _FOOD_DATE_KEY:
            pending = st.session_state.pop(_FOOD_PENDING_DATE_KEY, None)
            parsed = _parse_saved_date(pending)
            if parsed is not None:
                # This runs before the date widget is instantiated on the new rerun.
                st.session_state[_FOOD_DATE_KEY] = parsed
        return current_date_input(label, *args, **kwargs)

    @functools.wraps(current_button)
    def button_with_safe_saved_day_callback(label, *args, **kwargs):
        key = str(kwargs.get("key") or "")
        if not key.startswith(_SAVED_DAY_BUTTON_PREFIX):
            return current_button(label, *args, **kwargs)

        saved_date = _parse_saved_date(key[len(_SAVED_DAY_BUTTON_PREFIX) :])
        original_callback = kwargs.get("on_click")
        original_args = tuple(kwargs.pop("args", ()) or ())
        original_kwargs = dict(kwargs.pop("kwargs", {}) or {})

        def stage_saved_day() -> None:
            if callable(original_callback):
                original_callback(*original_args, **original_kwargs)
            if saved_date is not None:
                st.session_state[_FOOD_PENDING_DATE_KEY] = saved_date

        kwargs["on_click"] = stage_saved_day
        current_button(label, *args, **kwargs)
        # The callback stages the value before Streamlit reruns. Returning False prevents
        # the legacy page body from mutating the already-created date widget key.
        return False

    @functools.wraps(current_time_input)
    def time_input_with_compact_fluid_field(label, *args, **kwargs):
        key = str(kwargs.get("key") or "")
        if not key.startswith(_FLUID_TIME_PREFIX):
            return current_time_input(label, *args, **kwargs)

        compact_key = f"{key}_compact"
        initial = _display_compact_time(kwargs.get("value"))
        text_kwargs = {
            "key": compact_key,
            "value": initial,
            "placeholder": "Example: 10:30 PM",
        }
        for optional_name in ("disabled", "label_visibility", "help"):
            if optional_name in kwargs:
                text_kwargs[optional_name] = kwargs[optional_name]
        raw_value = current_text_input(label, **text_kwargs)
        parsed = _parse_compact_time(raw_value)
        if str(raw_value or "").strip() and parsed is None:
            st.caption("Use HH:MM or HH:MM AM/PM format.")
        return parsed

    setattr(date_input_with_pending_saved_day, _DAILY_LOG_WIDGET_MARKER, True)
    date_input_with_pending_saved_day._hm_original = current_date_input
    button_with_safe_saved_day_callback._hm_original = current_button
    time_input_with_compact_fluid_field._hm_original = current_time_input
    st.date_input = date_input_with_pending_saved_day
    st.button = button_with_safe_saved_day_callback
    st.time_input = time_input_with_compact_fluid_field


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
<style id="hm-daily-log-journal-selector-v5">
html,body,#root{margin-top:0!important;padding-top:0!important;}
header[data-testid="stHeader"],[data-testid="stToolbar"],[data-testid="stDecoration"],[data-testid="stStatusWidget"]{
  display:none!important;visibility:hidden!important;height:0!important;min-height:0!important;
  margin:0!important;padding:0!important;
}
[data-testid="stAppViewContainer"],[data-testid="stMain"],section.main,
[data-testid="stMainBlockContainer"],[data-testid="stAppViewBlockContainer"],
section.main > div.block-container,.main .block-container,.stMainBlockContainer,.block-container{
  padding-top:0!important;padding-block-start:0!important;margin-top:0!important;
}
div[data-testid="stElementContainer"]:has(style#hm-daily-log-journal-selector-v5),
div[data-testid="stElementContainer"]:has(style#hm-exercise-journal-table-v3),
div[data-testid="stElementContainer"]:has(style#hm-exercise-journal-layout-v4){
  display:none!important;height:0!important;min-height:0!important;
  margin:0!important;padding:0!important;overflow:hidden!important;
}
div[data-testid="stElementContainer"]:has(.utility-bar),
div[data-testid="stHorizontalBlock"]:has(.utility-bar){
  position:relative!important;top:-.55rem!important;margin-bottom:-.45rem!important;
}
.hero-shell{margin-bottom:.32rem!important;}
.hm-daily-log-selector-anchor{
  display:block;height:0;min-height:0;margin:0;padding:0;overflow:hidden;
}
.hm-daily-log-selector-anchor + div[data-testid="stHorizontalBlock"]{
  gap:.55rem!important;margin:.02rem 0 .06rem 0!important;
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
    """Install the aligned Exercise Journal and stable Daily Log corrections."""

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

    _install_daily_log_widget_corrections()
    _install_daily_log_tab_isolation()
