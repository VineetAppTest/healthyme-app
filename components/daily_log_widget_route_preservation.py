from __future__ import annotations

import functools
from typing import Any, Callable

import streamlit as st


_INSTALL_MARKER = "_hm_daily_log_widget_route_preservation_v1"
_PENDING_ROUTE_KEY = "_hm_h13r9e_pending_rerun_path"
_DAILY_LOG_ROUTE = "Daily_Log"

# These keys belong to Food/Exercise Journal controls only. Navigation controls such
# as Back and Dashboard deliberately stay outside this list so intentional route
# changes are never pulled back to Daily Log.
_DAILY_LOG_KEY_PREFIXES = (
    "hm_daily_log_",
    "hm_h9a4c_",
    "hm_food_journal_",
)

_WIDGET_CALLBACKS = {
    "button": "on_click",
    "checkbox": "on_change",
    "date_input": "on_change",
    "multiselect": "on_change",
    "number_input": "on_change",
    "radio": "on_change",
    "selectbox": "on_change",
    "slider": "on_change",
    "text_area": "on_change",
    "text_input": "on_change",
    "time_input": "on_change",
    "toggle": "on_change",
}


def _is_daily_log_widget_key(value: object) -> bool:
    key = str(value or "").strip()
    return bool(key) and key.startswith(_DAILY_LOG_KEY_PREFIXES)


def _stage_daily_log_route() -> None:
    st.session_state[_PENDING_ROUTE_KEY] = _DAILY_LOG_ROUTE


def _compose_route_callback(
    widget_kwargs: dict[str, Any],
    callback_name: str,
) -> None:
    original_callback = widget_kwargs.get(callback_name)
    original_args = tuple(widget_kwargs.pop("args", ()) or ())
    original_kwargs = dict(widget_kwargs.pop("kwargs", {}) or {})

    def preserve_route_then_run_callback() -> Any:
        _stage_daily_log_route()
        if callable(original_callback):
            return original_callback(*original_args, **original_kwargs)
        return None

    widget_kwargs[callback_name] = preserve_route_then_run_callback


def _wrap_widget(widget_name: str, callback_name: str) -> None:
    current_widget = getattr(st, widget_name, None)
    if not callable(current_widget) or getattr(current_widget, _INSTALL_MARKER, False):
        return

    @functools.wraps(current_widget)
    def widget_with_daily_log_route(*args: Any, **kwargs: Any) -> Any:
        if _is_daily_log_widget_key(kwargs.get("key")):
            _compose_route_callback(kwargs, callback_name)
        return current_widget(*args, **kwargs)

    setattr(widget_with_daily_log_route, _INSTALL_MARKER, True)
    widget_with_daily_log_route._hm_original_widget = current_widget
    setattr(st, widget_name, widget_with_daily_log_route)


def install_daily_log_widget_route_preservation() -> None:
    """Keep Daily Log active across native Streamlit widget reruns.

    Streamlit widget changes rerun the app internally and therefore do not pass
    through the explicit ``st.rerun`` wrapper installed by the native router. This
    installer composes a small callback onto journal widgets so the existing router
    receives the same pending-route marker before a Status, Activity, date or other
    journal control causes its automatic rerun.
    """

    for widget_name, callback_name in _WIDGET_CALLBACKS.items():
        _wrap_widget(widget_name, callback_name)
