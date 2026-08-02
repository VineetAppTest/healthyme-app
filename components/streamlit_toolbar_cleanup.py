from __future__ import annotations

import functools
import re

import streamlit as st


_MARKER = "_hm_streamlit_toolbar_cleanup_v3"
_BASE_CONFIG_ATTR = "_hm_streamlit_toolbar_base_page_config"
_STYLE_RENDER_MARKER = "_hm_zero_height_style_renderer_v1"
_STYLE_ONLY_MARKUP = re.compile(r"^\s*<style\b[^>]*>.*</style>\s*$", re.IGNORECASE | re.DOTALL)

_TOOLBAR_CSS = """
<style id="hm-streamlit-toolbar-cleanup-v3">
/* Streamlit Cloud owner/share controls. Keep this global and selector-tolerant. */
#MainMenu,
header[data-testid="stHeader"],
header[data-testid="stHeader"] *,
[data-testid="stToolbar"],
[data-testid="stToolbar"] *,
[data-testid="stToolbarActions"],
[data-testid="stToolbarActions"] *,
[data-testid="stHeaderActionElements"],
[data-testid="stHeaderActionElements"] *,
[data-testid="stAppToolbar"],
[data-testid="stAppToolbar"] *,
[data-testid="stDecoration"],
[data-testid="stAppDeployButton"],
[data-testid="stMainMenu"],
[data-testid="stShareButton"],
[data-testid="stFavoriteButton"],
[data-testid="stEditButton"],
[data-testid*="Toolbar"],
[data-testid*="toolbar"],
[data-testid*="HeaderAction"],
[data-testid*="DeployButton"],
button[data-testid="stBaseButton-header"],
button[data-testid^="stBaseButton-header"],
button[kind="header"],
button[aria-label="Share"],
button[aria-label*="favorite" i],
button[aria-label*="edit" i],
button[aria-label*="more" i] {
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
    pointer-events: none !important;
}

/* The global stylesheet itself must not recreate the blank top band. */
div[data-testid="stElementContainer"]:has(style#hm-streamlit-toolbar-cleanup-v3),
div.element-container:has(style#hm-streamlit-toolbar-cleanup-v3) {
    display: none !important;
    height: 0 !important;
    min-height: 0 !important;
    margin: 0 !important;
    padding: 0 !important;
    overflow: hidden !important;
}
</style>
"""


def _install_zero_height_style_renderer() -> None:
    """Render normal style-only markup without creating vertical Streamlit blocks.

    Streamlit places a normal ``st.markdown`` call inside an element container.
    Even when that call contains only CSS, the surrounding vertical layout can
    retain a gap. HealthyMe injects several global style blocks before the signed-in
    utility row, so those otherwise invisible containers can accumulate into a large
    empty band at the top of every page.

    Streamlit's ``st.html`` avoids that layout space for normal page styles. The
    owner-toolbar stylesheet is the one exception: it must be rendered through the
    original markdown path so its CSS reaches Streamlit Cloud's outer application
    chrome. Its own element container is collapsed by the stylesheet itself.
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


def _render_global_toolbar_css() -> None:
    """Render toolbar CSS into the outer app DOM without leaving layout space."""

    original_markdown = getattr(st.markdown, "_hm_original_markdown", st.markdown)
    original_markdown(_TOOLBAR_CSS, unsafe_allow_html=True)


def install_streamlit_toolbar_cleanup() -> None:
    """Hide Streamlit owner controls and keep the global header at the top.

    The wrapper calls Streamlit's real ``set_page_config`` first, then injects a
    presentation-only global CSS rule. It does not alter the browser URL, OAuth
    callback, authentication state, navigation, role routing or page content.
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
        _render_global_toolbar_css()
        return result

    setattr(set_page_config_without_owner_toolbar, _MARKER, True)
    st.set_page_config = set_page_config_without_owner_toolbar
