from __future__ import annotations

import contextvars
import functools
import inspect
from typing import Any, Callable

import streamlit as st

from components.repository_layout_correction_runtime import _REPOSITORY_CSS


_MARKER = "_hm_repository_exclusive_tabs_v1"
_SUPPRESSED = contextvars.ContextVar("hm_repository_section_suppressed", default=False)
_REPOSITORY_PAGES = {
    "pages/15_Admin_Recipe_Manager.py": "recipe",
    "pages/16_Admin_Exercise_Manager.py": "exercise",
    "pages/39_Admin_Supplement_Manager.py": "supplement",
}
_CLEAR_KEYS = {
    "recipe": (
        "hm_recipe_repository_edit_index",
        "hm_recipe_repository_delete_index",
    ),
    "exercise": (
        "hm_exercise_repository_edit_id",
        "hm_exercise_repository_delete_id",
    ),
    "supplement": (
        "hm_supplement_repository_edit_id",
        "hm_supplement_repository_delete_id",
    ),
}

_EXTRA_CSS = """
<style>
.hm-repository-exclusive-switch{display:none!important;}
div[data-testid="stSegmentedControl"]{
  margin:.10rem 0 .62rem!important;
  width:100%!important;
}

/* Safari/Streamlit may expose a second native disclosure glyph. Keep only the
   page-owned circular + / minus marker and the label container. */
div[data-testid="stExpander"] summary::-webkit-details-marker{
  display:none!important;
  width:0!important;
  font-size:0!important;
}
div[data-testid="stExpander"] summary::marker{
  content:""!important;
  display:none!important;
  color:transparent!important;
  font-size:0!important;
}
div[data-testid="stExpander"] summary > :not(p):not(:has(p)){
  display:none!important;
  width:0!important;
  min-width:0!important;
  height:0!important;
  margin:0!important;
  padding:0!important;
  overflow:hidden!important;
}
div[data-testid="stExpander"] summary > p,
div[data-testid="stExpander"] summary > :has(p){
  display:block!important;
  flex:1 1 auto!important;
}

/* The active repository page is the form scope after native tabs are retired.
   Keep Add and Edit moderately compact while separating section bands from the
   first field label/cell below them. */
div[data-testid="stVerticalBlock"]:has(.hm-repository-exclusive-switch) h4,
div[data-testid="stExpander"] h4{
  display:block!important;
  position:relative!important;
  z-index:1!important;
  color:#064E3B!important;
  background:#F8F3E7!important;
  border-left:3px solid #E3C98E!important;
  border-radius:6px!important;
  font-size:.80rem!important;
  line-height:1.2!important;
  margin:.38rem 0 .38rem!important;
  padding:.20rem .38rem!important;
}
div[data-testid="stVerticalBlock"]:has(.hm-repository-exclusive-switch) label p,
div[data-testid="stExpander"] label p{
  margin-top:.05rem!important;
  margin-bottom:.08rem!important;
}
div[data-testid="stVerticalBlock"]:has(.hm-repository-exclusive-switch) input,
div[data-testid="stExpander"] input,
div[data-testid="stVerticalBlock"]:has(.hm-repository-exclusive-switch) div[data-baseweb="select"]>div,
div[data-testid="stExpander"] div[data-baseweb="select"]>div{
  min-height:2.10rem!important;
}
div[data-testid="stVerticalBlock"]:has(.hm-repository-exclusive-switch) textarea,
div[data-testid="stExpander"] textarea{
  min-height:58px!important;
}
</style>
"""


def _page_context() -> tuple[str, Any | None]:
    frame = inspect.currentframe()
    frame = frame.f_back if frame is not None else None
    while frame is not None:
        path = str((frame.f_globals or {}).get("__file__") or "").replace("\\", "/")
        for suffix, kind in _REPOSITORY_PAGES.items():
            if path.endswith(suffix):
                return kind, frame
        frame = frame.f_back
    return "", None


def _option_list(args: tuple[Any, ...], kwargs: dict[str, Any]) -> list[str]:
    options = args[0] if args else kwargs.get("tabs", kwargs.get("options", []))
    try:
        return [str(value) for value in options]
    except Exception:
        return []


class _NullBlock:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        return False


class _RepositorySection:
    def __init__(self, *, active: bool, kind: str, page_frame: Any | None):
        self.active = active
        self.kind = kind
        self.page_frame = page_frame
        self._token = None
        self._patched_globals: dict[str, Any] = {}

    def _patch_page_reads(self) -> None:
        if self.page_frame is None:
            return
        namespace = self.page_frame.f_globals

        def patch(name: str, replacement: Any) -> None:
            if name in namespace:
                self._patched_globals[name] = namespace[name]
                namespace[name] = replacement

        if self.kind == "recipe":
            def empty_recipe_frame():
                pd = namespace.get("pd")
                columns = namespace.get("RECIPE_COLUMNS", [])
                return pd.DataFrame(columns=columns) if pd is not None else []

            patch("load", empty_recipe_frame)
        elif self.kind == "exercise":
            patch("list_exercise_repository", lambda *args, **kwargs: [])
        elif self.kind == "supplement":
            patch(
                "supplement_repository_counts",
                lambda *args, **kwargs: {"active": 0, "inactive": 0, "total": 0},
            )
            patch("list_supplement_repository", lambda *args, **kwargs: [])

    def __enter__(self):
        if self.active:
            return self
        self._token = _SUPPRESSED.set(True)
        self._patch_page_reads()
        return self

    def __exit__(self, exc_type, exc, traceback):
        if self.active:
            return False
        if self.page_frame is not None:
            namespace = self.page_frame.f_globals
            for name, original in self._patched_globals.items():
                namespace[name] = original
        if self._token is not None:
            _SUPPRESSED.reset(self._token)
        return False


def _suppressed() -> bool:
    return bool(_SUPPRESSED.get())


def _widget_default(args: tuple[Any, ...], kwargs: dict[str, Any], *, kind: str):
    if kind in {"text_input", "text_area"}:
        return kwargs.get("value", "")
    if kind == "selectbox":
        options = args[1] if len(args) > 1 else kwargs.get("options", [])
        try:
            values = list(options)
        except Exception:
            values = []
        if not values:
            return None
        try:
            index = int(kwargs.get("index", 0) or 0)
        except Exception:
            index = 0
        return values[max(0, min(index, len(values) - 1))]
    if kind == "multiselect":
        default = kwargs.get("default", [])
        return list(default or [])
    return None


def install_repository_exclusive_tabs_runtime() -> None:
    current_tabs = st.tabs
    if getattr(current_tabs, _MARKER, False):
        return

    current_markdown = st.markdown
    current_segmented_control = st.segmented_control
    current_columns = st.columns
    current_expander = st.expander
    current_form = st.form
    current_container = st.container
    current_button = st.button
    current_form_submit_button = st.form_submit_button
    current_text_input = st.text_input
    current_text_area = st.text_area
    current_selectbox = st.selectbox
    current_multiselect = st.multiselect
    current_file_uploader = st.file_uploader
    current_rerun = st.rerun
    current_stop = st.stop

    output_names = (
        "caption",
        "divider",
        "error",
        "header",
        "image",
        "info",
        "subheader",
        "success",
        "warning",
        "write",
    )
    current_outputs = {name: getattr(st, name) for name in output_names if hasattr(st, name)}

    @functools.wraps(current_tabs)
    def tabs_with_exclusive_repository_section(*args, **kwargs):
        kind, page_frame = _page_context()
        options = _option_list(args, kwargs)
        if not kind or len(options) != 2 or options[0] != "Current Repository":
            return current_tabs(*args, **kwargs)

        current_markdown(
            "<span class='hm-repository-exclusive-switch'></span>"
            + _REPOSITORY_CSS
            + _EXTRA_CSS,
            unsafe_allow_html=True,
        )
        selected = current_segmented_control(
            "Repository section",
            options,
            default=options[0],
            key=f"hm_{kind}_repository_exclusive_section",
            label_visibility="collapsed",
            width="stretch",
        ) or options[0]

        if selected == options[1]:
            for key in _CLEAR_KEYS.get(kind, ()):
                st.session_state.pop(key, None)

        return [
            _RepositorySection(
                active=selected == option,
                kind=kind,
                page_frame=page_frame,
            )
            for option in options
        ]

    @functools.wraps(current_markdown)
    def markdown_with_suppression(*args, **kwargs):
        if _suppressed():
            return None
        return current_markdown(*args, **kwargs)

    @functools.wraps(current_columns)
    def columns_with_suppression(spec, *args, **kwargs):
        if not _suppressed():
            return current_columns(spec, *args, **kwargs)
        try:
            count = int(spec)
        except Exception:
            try:
                count = len(spec)
            except Exception:
                count = 1
        return [_NullBlock() for _ in range(max(count, 1))]

    def context_wrapper(current: Callable[..., Any]):
        @functools.wraps(current)
        def wrapped(*args, **kwargs):
            if _suppressed():
                return _NullBlock()
            return current(*args, **kwargs)

        return wrapped

    def false_wrapper(current: Callable[..., Any]):
        @functools.wraps(current)
        def wrapped(*args, **kwargs):
            if _suppressed():
                return False
            return current(*args, **kwargs)

        return wrapped

    def value_wrapper(current: Callable[..., Any], kind: str):
        @functools.wraps(current)
        def wrapped(*args, **kwargs):
            if _suppressed():
                return _widget_default(args, kwargs, kind=kind)
            return current(*args, **kwargs)

        return wrapped

    @functools.wraps(current_file_uploader)
    def file_uploader_with_suppression(*args, **kwargs):
        if _suppressed():
            return None
        return current_file_uploader(*args, **kwargs)

    @functools.wraps(current_rerun)
    def rerun_with_suppression(*args, **kwargs):
        if _suppressed():
            return None
        return current_rerun(*args, **kwargs)

    @functools.wraps(current_stop)
    def stop_with_suppression(*args, **kwargs):
        if _suppressed():
            return None
        return current_stop(*args, **kwargs)

    def make_output_wrapper(name: str, current: Callable[..., Any]):
        @functools.wraps(current)
        def wrapped(*args, **kwargs):
            if _suppressed():
                return None
            return current(*args, **kwargs)

        wrapped.__name__ = f"{name}_with_repository_suppression"
        return wrapped

    st.tabs = tabs_with_exclusive_repository_section
    st.markdown = markdown_with_suppression
    st.columns = columns_with_suppression
    st.expander = context_wrapper(current_expander)
    st.form = context_wrapper(current_form)
    st.container = context_wrapper(current_container)
    st.button = false_wrapper(current_button)
    st.form_submit_button = false_wrapper(current_form_submit_button)
    st.text_input = value_wrapper(current_text_input, "text_input")
    st.text_area = value_wrapper(current_text_area, "text_area")
    st.selectbox = value_wrapper(current_selectbox, "selectbox")
    st.multiselect = value_wrapper(current_multiselect, "multiselect")
    st.file_uploader = file_uploader_with_suppression
    st.rerun = rerun_with_suppression
    st.stop = stop_with_suppression

    for name, current in current_outputs.items():
        setattr(st, name, make_output_wrapper(name, current))

    setattr(tabs_with_exclusive_repository_section, _MARKER, True)
