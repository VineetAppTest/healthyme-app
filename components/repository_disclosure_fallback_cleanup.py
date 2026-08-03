from __future__ import annotations

import functools
import inspect
from typing import Any

import streamlit as st


_MARKER = "_hm_repository_disclosure_fallback_cleanup_v1"
_REPOSITORY_PAGES = {
    "pages/15_Admin_Recipe_Manager.py",
    "pages/16_Admin_Exercise_Manager.py",
    "pages/39_Admin_Supplement_Manager.py",
}

_DISCLOSURE_CSS = """
<style>
/* Streamlit 1.59 can expose the material-icon ligature text (for example,
   keyboard_arrow_down) when its native expander icon is suppressed. Keep the
   accepted page-owned circular + / minus marker and hide only that fallback. */
div[data-testid="stExpander"] summary [data-testid="stExpanderToggleIcon"],
div[data-testid="stExpander"] summary [data-testid="stIconMaterial"],
div[data-testid="stExpander"] summary span[translate="no"],
div[data-testid="stExpander"] summary span[aria-hidden="true"],
div[data-testid="stExpander"] summary span[class*="material-symbols"]{
  display:none!important;
  visibility:hidden!important;
  width:0!important;
  min-width:0!important;
  max-width:0!important;
  height:0!important;
  margin:0!important;
  padding:0!important;
  overflow:hidden!important;
  color:transparent!important;
  font-size:0!important;
  line-height:0!important;
}
</style>
"""


def _repository_page() -> bool:
    frame = inspect.currentframe()
    frame = frame.f_back if frame is not None else None
    while frame is not None:
        path = str((frame.f_globals or {}).get("__file__") or "").replace("\\", "/")
        if any(path.endswith(suffix) for suffix in _REPOSITORY_PAGES):
            return True
        frame = frame.f_back
    return False


def _options(args: tuple[Any, ...], kwargs: dict[str, Any]) -> list[str]:
    values = args[0] if args else kwargs.get("tabs", kwargs.get("options", []))
    try:
        return [str(value) for value in values]
    except Exception:
        return []


def install_repository_disclosure_fallback_cleanup() -> None:
    current_tabs = st.tabs
    if getattr(current_tabs, _MARKER, False):
        return

    current_markdown = st.markdown

    @functools.wraps(current_tabs)
    def tabs_with_disclosure_fallback_cleanup(*args, **kwargs):
        options = _options(args, kwargs)
        if (
            _repository_page()
            and len(options) == 2
            and options[0] == "Current Repository"
        ):
            current_markdown(_DISCLOSURE_CSS, unsafe_allow_html=True)
        return current_tabs(*args, **kwargs)

    setattr(tabs_with_disclosure_fallback_cleanup, _MARKER, True)
    st.tabs = tabs_with_disclosure_fallback_cleanup
