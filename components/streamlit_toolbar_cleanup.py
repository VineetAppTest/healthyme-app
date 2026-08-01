from __future__ import annotations

import functools
import re

import streamlit as st


_MARKER = "_hm_streamlit_toolbar_cleanup_v2"
_BASE_CONFIG_ATTR = "_hm_streamlit_toolbar_base_page_config"
_STYLE_RENDER_MARKER = "_hm_zero_height_style_renderer_v1"
_STYLE_ONLY_MARKUP = re.compile(r"^\s*<style\b[^>]*>.*</style>\s*$", re.IGNORECASE | re.DOTALL)

_TOOLBAR_CSS = """
<style id="hm-streamlit-toolbar-cleanup-v2">
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


def _install_zero_height_style_renderer() -> None:
    """Render style-only markup without creating vertical Streamlit blocks.

    Streamlit places a normal ``st.markdown`` call inside an element container.
    Even when that call contains only CSS, the surrounding vertical layout can
    retain a gap. HealthyMe injects several global style blocks before the signed-in
    utility row, so those otherwise invisible containers can accumulate into a large
    empty band at the top of every page.

    Streamlit's ``st.html`` renders style-only content without consuming layout
    space. This wrapper redirects only complete, style-only strings; markdown that
    contains visible content continues through the original renderer unchanged.
    """

    current = st.markdown
    if getattr(current, _STYLE_RENDER_MARKER, False):
        return

    html_renderer = getattr(st, "html", None)
    if not callable(html_renderer):
        return

    @functools.wraps(current)
    def markdown_without_style_gap(body, *args, **kwargs):
        if isinstance(body, str) and _STYLE_ONLY_MARKUP.fullmatch(body):
            return html_renderer(body)
        return current(body, *args, **kwargs)

    setattr(markdown_without_style_gap, _STYLE_RENDER_MARKER, True)
    setattr(markdown_without_style_gap, "_hm_original_markdown", current)
    st.markdown = markdown_without_style_gap


def install_streamlit_toolbar_cleanup() -> None:
    """Hide Streamlit owner controls and keep the global header at the top.

    The wrapper calls Streamlit's real ``set_page_config`` first, then injects a
    presentation-only CSS rule through the zero-height style renderer. It does not
    alter the browser URL, OAuth callback, authentication state, navigation, role
    routing or page content.
    """

    _install_zero_height_style_renderer()

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
