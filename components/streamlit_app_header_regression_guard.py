from __future__ import annotations

import functools

import streamlit as st


_MARKER = "_hm_streamlit_app_header_regression_guard_v1"
_CSS = """
<style id="hm-streamlit-app-header-regression-guard-v1">
/* Streamlit Cloud 2026 app-header controls shown in SS2. */
[data-testid="stAppHeader"],
[data-testid="stAppHeader"] *,
[data-testid="stAppHeaderActions"],
[data-testid="stAppHeaderActions"] *,
[data-testid="stAppHeaderToolbar"],
[data-testid="stAppHeaderToolbar"] *,
[class*="stAppHeader"],
[class*="stAppHeader"] *,
button[aria-label="Share this app"],
button[aria-label*="star" i],
button[aria-label*="favorite" i],
button[aria-label*="edit app" i],
button[aria-label*="manage app" i] {
  display:none!important;
  visibility:hidden!important;
  width:0!important;
  min-width:0!important;
  max-width:0!important;
  height:0!important;
  min-height:0!important;
  max-height:0!important;
  margin:0!important;
  padding:0!important;
  border:0!important;
  overflow:hidden!important;
  pointer-events:none!important;
}
div[data-testid="stElementContainer"]:has(style#hm-streamlit-app-header-regression-guard-v1),
div.element-container:has(style#hm-streamlit-app-header-regression-guard-v1){
  display:none!important;height:0!important;min-height:0!important;
  margin:0!important;padding:0!important;overflow:hidden!important;
}
</style>
"""


def _render_css() -> None:
    original_markdown = getattr(st.markdown, "_hm_original_markdown", st.markdown)
    original_markdown(_CSS, unsafe_allow_html=True)


def install_streamlit_app_header_regression_guard() -> None:
    current = st.set_page_config
    if getattr(current, _MARKER, False):
        return

    @functools.wraps(current)
    def set_page_config_without_app_header(*args, **kwargs):
        result = current(*args, **kwargs)
        _render_css()
        return result

    setattr(set_page_config_without_app_header, _MARKER, True)
    st.set_page_config = set_page_config_without_app_header
