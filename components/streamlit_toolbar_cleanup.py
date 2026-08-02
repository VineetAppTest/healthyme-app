from __future__ import annotations

import functools
import json
import re

import streamlit as st


_MARKER = "_hm_streamlit_toolbar_cleanup_v4"
_BASE_CONFIG_ATTR = "_hm_streamlit_toolbar_base_page_config"
_STYLE_RENDER_MARKER = "_hm_zero_height_style_renderer_v1"
_STYLE_ONLY_MARKUP = re.compile(r"^\s*<style\b[^>]*>.*</style>\s*$", re.IGNORECASE | re.DOTALL)

_TOOLBAR_SELECTORS = (
    "#MainMenu",
    'header[data-testid="stHeader"]',
    'header[data-testid="stHeader"] *',
    '[data-testid="stToolbar"]',
    '[data-testid="stToolbar"] *',
    '[data-testid="stToolbarActions"]',
    '[data-testid="stToolbarActions"] *',
    '[data-testid="stHeaderActionElements"]',
    '[data-testid="stHeaderActionElements"] *',
    '[data-testid="stAppToolbar"]',
    '[data-testid="stAppToolbar"] *',
    '[data-testid="stDecoration"]',
    '[data-testid="stAppDeployButton"]',
    '[data-testid="stMainMenu"]',
    '[data-testid="stShareButton"]',
    '[data-testid="stFavoriteButton"]',
    '[data-testid="stEditButton"]',
    '[data-testid*="Toolbar"]',
    '[data-testid*="toolbar"]',
    '[data-testid*="HeaderAction"]',
    '[data-testid*="DeployButton"]',
    'button[data-testid="stBaseButton-header"]',
    'button[data-testid^="stBaseButton-header"]',
    'button[kind="header"]',
    'button[aria-label="Share"]',
    'button[aria-label*="favorite" i]',
    'button[aria-label*="edit" i]',
    'button[aria-label*="more" i]',
)
_TOOLBAR_SELECTOR_TEXT = ",\n".join(_TOOLBAR_SELECTORS)
_TOOLBAR_HIDE_DECLARATIONS = """
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
"""
_TOP_DOCUMENT_CSS = f"{_TOOLBAR_SELECTOR_TEXT} {{{_TOOLBAR_HIDE_DECLARATIONS}}}"

_TOOLBAR_CSS = f"""
<style id="hm-streamlit-toolbar-cleanup-v4">
/* Streamlit Cloud owner/share controls. Keep this global and selector-tolerant. */
{_TOP_DOCUMENT_CSS}

/* The global stylesheet itself must not recreate the blank top band. */
div[data-testid="stElementContainer"]:has(style#hm-streamlit-toolbar-cleanup-v4),
div.element-container:has(style#hm-streamlit-toolbar-cleanup-v4) {{
    display: none !important;
    height: 0 !important;
    min-height: 0 !important;
    margin: 0 !important;
    padding: 0 !important;
    overflow: hidden !important;
}}
</style>
"""

_TOOLBAR_GUARD_SCRIPT = """
<script id="hm-streamlit-toolbar-reconnect-guard-v4">
(() => {
  let hostWindow = window;
  try {
    hostWindow = window.top || window;
  } catch (_topError) {}

  let doc = document;
  try {
    doc = hostWindow.document || document;
  } catch (_documentError) {}
  if (!doc || !doc.documentElement) return;

  const styleId = "hm-streamlit-toolbar-top-document-v4";
  const stateKey = "__healthymeToolbarReconnectGuardV4";
  const selectors = __SELECTORS__;
  const cssText = __CSS_TEXT__;
  const hiddenProperties = [
    ["display", "none"],
    ["visibility", "hidden"],
    ["width", "0"],
    ["min-width", "0"],
    ["max-width", "0"],
    ["height", "0"],
    ["min-height", "0"],
    ["max-height", "0"],
    ["margin", "0"],
    ["padding", "0"],
    ["border", "0"],
    ["overflow", "hidden"],
    ["pointer-events", "none"]
  ];

  const ensureStyle = () => {
    let style = doc.getElementById(styleId);
    if (!style) {
      style = doc.createElement("style");
      style.id = styleId;
      (doc.head || doc.documentElement).appendChild(style);
    }
    if (style.textContent !== cssText) style.textContent = cssText;
  };

  const hideToolbar = () => {
    let nodes = [];
    try {
      nodes = doc.querySelectorAll(selectors);
    } catch (_selectorError) {
      return;
    }
    nodes.forEach((node) => {
      hiddenProperties.forEach(([property, value]) => {
        try { node.style.setProperty(property, value, "important"); } catch (_styleError) {}
      });
      try { node.setAttribute("aria-hidden", "true"); } catch (_ariaError) {}
    });
  };

  const apply = () => {
    ensureStyle();
    hideToolbar();
  };

  const previous = hostWindow[stateKey];
  if (previous && previous.observer && typeof previous.observer.disconnect === "function") {
    previous.observer.disconnect();
  }

  apply();

  const Observer = hostWindow.MutationObserver || window.MutationObserver;
  let observer = null;
  if (typeof Observer === "function") {
    observer = new Observer((mutations) => {
      if (mutations.some((mutation) => mutation.addedNodes && mutation.addedNodes.length)) {
        apply();
      }
    });
    observer.observe(doc.documentElement, { childList: true, subtree: true });
  }

  hostWindow[stateKey] = { observer, apply };
  [50, 250, 1000, 3000].forEach((delay) => hostWindow.setTimeout(apply, delay));
})();
</script>
""".replace("__SELECTORS__", json.dumps(_TOOLBAR_SELECTOR_TEXT)).replace(
    "__CSS_TEXT__", json.dumps(_TOP_DOCUMENT_CSS)
)


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
    """Render toolbar CSS into the app DOM without leaving layout space."""

    original_markdown = getattr(st.markdown, "_hm_original_markdown", st.markdown)
    original_markdown(_TOOLBAR_CSS, unsafe_allow_html=True)


def _render_toolbar_reconnect_guard() -> None:
    """Keep owner controls hidden when Community Cloud remounts chrome after idle.

    The static stylesheet is sufficient during an ordinary Streamlit rerun. After a
    long idle period, Community Cloud can recreate its top-level owner toolbar without
    recreating the page's style node. This zero-height script places the same rule in
    the top document and observes later DOM additions. It changes presentation only.
    """

    html_renderer = getattr(st, "html", None)
    if not callable(html_renderer):
        return
    html_renderer(_TOOLBAR_GUARD_SCRIPT, unsafe_allow_javascript=True)


def install_streamlit_toolbar_cleanup() -> None:
    """Hide Streamlit owner controls and keep the global header at the top.

    The wrapper calls Streamlit's real ``set_page_config`` first, then injects a
    presentation-only global CSS rule and idle/reconnect guard. It does not alter the
    browser URL, OAuth callback, authentication state, navigation, role routing or
    page content.
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
        _render_toolbar_reconnect_guard()
        return result

    setattr(set_page_config_without_owner_toolbar, _MARKER, True)
    st.set_page_config = set_page_config_without_owner_toolbar
