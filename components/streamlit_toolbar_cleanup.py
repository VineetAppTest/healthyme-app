from __future__ import annotations

import functools

import streamlit as st


_MARKER = "_hm_streamlit_toolbar_cleanup_v1"
_BASE_CONFIG_ATTR = "_hm_streamlit_toolbar_base_page_config"

_TOOLBAR_CSS = """
<style id="hm-streamlit-toolbar-cleanup-v1">
#MainMenu,
header[data-testid="stHeader"],
[data-testid="stToolbar"],
[data-testid="stToolbarActions"],
[data-testid="stHeaderActionElements"],
[data-testid="stAppToolbar"],
[data-testid="stDecoration"],
button[data-testid="stBaseButton-header"],
button[kind="header"] {
    display: none !important;
    visibility: hidden !important;
    width: 0 !important;
    min-width: 0 !important;
    max-width: 0 !important;
    height: 0 !important;
    min-height: 0 !important;
    max-height: 0 !important;
    margin: 0 !important;
    padding: 0 !important;
    border: 0 !important;
    overflow: hidden !important;
}
</style>
"""


def install_streamlit_toolbar_cleanup() -> None:
    """Hide Streamlit Cloud owner controls after every page configuration.

    The wrapper calls Streamlit's real ``set_page_config`` first, then injects a
    presentation-only CSS rule. It does not alter the browser URL, OAuth callback,
    authentication state, navigation, role routing or page content.
    """

    current = st.set_page_config
    if getattr(current, _MARKER, False):
        return

    base = getattr(st, _BASE_CONFIG_ATTR, None)
    if not callable(base):
        base = current
        setattr(st, _BASE_CONFIG_ATTR, base)

    @functools.wraps(base)
    def set_page_config_without_owner_toolbar(*args, **kwargs):
        result = base(*args, **kwargs)
        st.markdown(_TOOLBAR_CSS, unsafe_allow_html=True)
        return result

    setattr(set_page_config_without_owner_toolbar, _MARKER, True)
    st.set_page_config = set_page_config_without_owner_toolbar
