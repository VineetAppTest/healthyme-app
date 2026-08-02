from __future__ import annotations

import contextlib
import functools
import inspect
from typing import Any

import streamlit as st


_MARKER = "_hm_member_daily_log_sections_v1"
_PAGE_SUFFIX = "pages/18_Daily_Log.py"
_LABELS = ("Food Journal", "Exercise Journal")
_STATE_KEY = "hm_daily_log_active_journal"
_INACTIVE_DEPTH = 0


def _page_in_stack() -> bool:
    for frame_info in inspect.stack():
        page_file = str(frame_info.frame.f_globals.get("__file__") or "").replace("\\", "/")
        if page_file.endswith(_PAGE_SUFFIX):
            return True
    return False


def _inactive() -> bool:
    return _INACTIVE_DEPTH > 0


def _activate(label: str) -> None:
    if label in _LABELS:
        st.session_state[_STATE_KEY] = label


def _value(args, kwargs, default: Any = "") -> Any:
    if "value" in kwargs:
        return kwargs.get("value")
    if len(args) > 1:
        return args[1]
    return default


def _option_value(args, kwargs) -> Any:
    options = kwargs.get("options")
    if options is None and len(args) > 1:
        options = args[1]
    try:
        values = list(options or [])
    except Exception:
        values = []
    if not values:
        return None
    index = int(kwargs.get("index", 0) or 0)
    return values[max(0, min(index, len(values) - 1))]


class _NullElement:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        return False

    def __getattr__(self, _name):
        def no_op(*_args, **_kwargs):
            return self

        return no_op


class _JournalContext:
    def __init__(self, active: bool):
        self.active = bool(active)

    def __enter__(self):
        global _INACTIVE_DEPTH
        if not self.active:
            _INACTIVE_DEPTH += 1
        return st

    def __exit__(self, exc_type, exc, traceback):
        global _INACTIVE_DEPTH
        if not self.active:
            _INACTIVE_DEPTH = max(0, _INACTIVE_DEPTH - 1)
        return False


def install_member_daily_log_section_runtime() -> None:
    current_tabs = st.tabs
    if getattr(current_tabs, _MARKER, False):
        return

    originals = {
        name: getattr(st, name)
        for name in (
            "markdown",
            "subheader",
            "header",
            "caption",
            "info",
            "warning",
            "error",
            "success",
            "toast",
            "write",
            "text",
            "code",
            "divider",
            "dataframe",
            "table",
            "image",
            "metric",
            "json",
            "text_input",
            "text_area",
            "selectbox",
            "radio",
            "multiselect",
            "date_input",
            "time_input",
            "number_input",
            "slider",
            "select_slider",
            "checkbox",
            "toggle",
            "file_uploader",
            "data_editor",
            "button",
            "form_submit_button",
            "download_button",
            "columns",
            "container",
            "expander",
            "form",
            "spinner",
            "popover",
            "empty",
            "progress",
            "stop",
            "rerun",
        )
        if hasattr(st, name)
    }

    original_markdown = originals.get("markdown", st.markdown)
    original_columns = originals.get("columns", st.columns)
    original_button = originals.get("button", st.button)

    @functools.wraps(current_tabs)
    def persistent_daily_log_sections(labels, *args, **kwargs):
        label_tuple = tuple(str(label) for label in labels)
        if _inactive():
            return [contextlib.nullcontext() for _ in label_tuple]
        if not _page_in_stack() or label_tuple != _LABELS:
            return current_tabs(labels, *args, **kwargs)

        selected = str(st.session_state.get(_STATE_KEY) or _LABELS[0])
        if selected not in _LABELS:
            selected = _LABELS[0]
            st.session_state[_STATE_KEY] = selected

        original_markdown(
            """
<style id="hm-daily-log-persistent-journal-selector">
.hm-daily-log-journal-anchor{display:block;height:0;margin:0;padding:0;overflow:hidden;}
.hm-daily-log-journal-anchor + div[data-testid="stHorizontalBlock"]{gap:.55rem!important;margin:.15rem 0 1rem!important;border-bottom:1px solid #E3D4BA;padding-bottom:.45rem!important;}
.hm-daily-log-journal-anchor + div[data-testid="stHorizontalBlock"] button{min-height:2.65rem!important;border:1.4px solid #D8A84E!important;border-radius:999px!important;font-weight:950!important;padding:.52rem 1rem!important;}
.hm-daily-log-journal-anchor + div[data-testid="stHorizontalBlock"] button[kind="primary"]{background:#064E3B!important;border-color:#064E3B!important;color:#FFFFFF!important;}
.hm-daily-log-journal-anchor + div[data-testid="stHorizontalBlock"] button[kind="secondary"]{background:#FFFFFF!important;color:#064E3B!important;}
</style>
<span class="hm-daily-log-journal-anchor"></span>
            """,
            unsafe_allow_html=True,
        )
        columns = original_columns(2, gap="small")
        for column, label in zip(columns, _LABELS):
            with column:
                original_button(
                    label,
                    key=f"hm_daily_log_journal_{label.lower().replace(' ', '_')}",
                    type="primary" if selected == label else "secondary",
                    use_container_width=True,
                    on_click=_activate,
                    args=(label,),
                )

        return [_JournalContext(selected == label) for label in _LABELS]

    setattr(persistent_daily_log_sections, _MARKER, True)
    st.tabs = persistent_daily_log_sections

    def wrap_output(name: str) -> None:
        original = originals[name]

        @functools.wraps(original)
        def wrapped(*args, **kwargs):
            if _inactive():
                return None
            return original(*args, **kwargs)

        setattr(wrapped, _MARKER, True)
        setattr(st, name, wrapped)

    for name in (
        "markdown",
        "subheader",
        "header",
        "caption",
        "info",
        "warning",
        "error",
        "success",
        "toast",
        "write",
        "text",
        "code",
        "divider",
        "dataframe",
        "table",
        "image",
        "metric",
        "json",
    ):
        if name in originals:
            wrap_output(name)

    for name in ("text_input", "text_area", "date_input", "time_input", "number_input", "slider"):
        if name not in originals:
            continue
        original = originals[name]

        @functools.wraps(original)
        def wrapped_value(*args, __original=original, **kwargs):
            if _inactive():
                return _value(args, kwargs, "")
            return __original(*args, **kwargs)

        setattr(wrapped_value, _MARKER, True)
        setattr(st, name, wrapped_value)

    for name in ("selectbox", "radio"):
        if name not in originals:
            continue
        original = originals[name]

        @functools.wraps(original)
        def wrapped_option(*args, __original=original, **kwargs):
            if _inactive():
                return _option_value(args, kwargs)
            return __original(*args, **kwargs)

        setattr(wrapped_option, _MARKER, True)
        setattr(st, name, wrapped_option)

    if "select_slider" in originals:
        original_select_slider = originals["select_slider"]

        @functools.wraps(original_select_slider)
        def wrapped_select_slider(*args, **kwargs):
            if _inactive():
                if "value" in kwargs:
                    return kwargs.get("value")
                return _option_value(args, kwargs)
            return original_select_slider(*args, **kwargs)

        setattr(wrapped_select_slider, _MARKER, True)
        st.select_slider = wrapped_select_slider

    if "multiselect" in originals:
        original_multiselect = originals["multiselect"]

        @functools.wraps(original_multiselect)
        def wrapped_multiselect(*args, **kwargs):
            if _inactive():
                default = kwargs.get("default")
                return list(default or [])
            return original_multiselect(*args, **kwargs)

        setattr(wrapped_multiselect, _MARKER, True)
        st.multiselect = wrapped_multiselect

    for name in ("checkbox", "toggle"):
        if name not in originals:
            continue
        original = originals[name]

        @functools.wraps(original)
        def wrapped_bool(*args, __original=original, **kwargs):
            if _inactive():
                return bool(_value(args, kwargs, False))
            return __original(*args, **kwargs)

        setattr(wrapped_bool, _MARKER, True)
        setattr(st, name, wrapped_bool)

    if "file_uploader" in originals:
        original_file_uploader = originals["file_uploader"]

        @functools.wraps(original_file_uploader)
        def wrapped_file_uploader(*args, **kwargs):
            if _inactive():
                return [] if kwargs.get("accept_multiple_files") else None
            return original_file_uploader(*args, **kwargs)

        setattr(wrapped_file_uploader, _MARKER, True)
        st.file_uploader = wrapped_file_uploader

    if "data_editor" in originals:
        original_data_editor = originals["data_editor"]

        @functools.wraps(original_data_editor)
        def wrapped_data_editor(data, *args, **kwargs):
            if _inactive():
                return data
            return original_data_editor(data, *args, **kwargs)

        setattr(wrapped_data_editor, _MARKER, True)
        st.data_editor = wrapped_data_editor

    for name in ("button", "form_submit_button", "download_button"):
        if name not in originals:
            continue
        original = originals[name]

        @functools.wraps(original)
        def wrapped_action(*args, __original=original, **kwargs):
            if _inactive():
                return False
            return __original(*args, **kwargs)

        setattr(wrapped_action, _MARKER, True)
        setattr(st, name, wrapped_action)

    if "columns" in originals:
        original_columns_runtime = originals["columns"]

        @functools.wraps(original_columns_runtime)
        def wrapped_columns(spec, *args, **kwargs):
            if _inactive():
                count = spec if isinstance(spec, int) else len(spec)
                return [contextlib.nullcontext() for _ in range(count)]
            return original_columns_runtime(spec, *args, **kwargs)

        setattr(wrapped_columns, _MARKER, True)
        st.columns = wrapped_columns

    for name in ("container", "expander", "form", "spinner", "popover"):
        if name not in originals:
            continue
        original = originals[name]

        @functools.wraps(original)
        def wrapped_context(*args, __original=original, **kwargs):
            if _inactive():
                return contextlib.nullcontext()
            return __original(*args, **kwargs)

        setattr(wrapped_context, _MARKER, True)
        setattr(st, name, wrapped_context)

    for name in ("empty", "progress"):
        if name not in originals:
            continue
        original = originals[name]

        @functools.wraps(original)
        def wrapped_element(*args, __original=original, **kwargs):
            if _inactive():
                return _NullElement()
            return __original(*args, **kwargs)

        setattr(wrapped_element, _MARKER, True)
        setattr(st, name, wrapped_element)

    for name in ("stop", "rerun"):
        if name not in originals:
            continue
        original = originals[name]

        @functools.wraps(original)
        def wrapped_control(*args, __original=original, **kwargs):
            if _inactive():
                return None
            return __original(*args, **kwargs)

        setattr(wrapped_control, _MARKER, True)
        setattr(st, name, wrapped_control)
