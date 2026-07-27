from __future__ import annotations

import json
import runpy
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

import streamlit as st


# Streamlit reruns reuse the same Python process. The H13R2 integration temporarily
# wraps these routing callables while assembling the real Member/Admin application.
# Always restore the process-level originals before starting a new run so wrappers
# cannot stack and append the same page registry more than once.
_ROUTING_PRIMITIVES = {
    "Page": "_hm_h13r2_base_page",
    "navigation": "_hm_h13r2_base_navigation",
    "switch_page": "_hm_h13r2_base_switch_page",
}
for public_name, cache_name in _ROUTING_PRIMITIVES.items():
    current_callable = getattr(st, public_name)
    base_callable = getattr(st, cache_name, None)
    if base_callable is None:
        setattr(st, cache_name, current_callable)
    else:
        setattr(st, public_name, base_callable)

_BASE_NAVIGATION = getattr(st, "_hm_h13r2_base_navigation")
_BASE_SWITCH_PAGE = getattr(st, "_hm_h13r2_base_switch_page")


from native_bridge import root_authorization_ui as _root_authorization_ui  # noqa: E402


def _native_identity_present() -> bool:
    try:
        return bool(st.user and st.user.is_logged_in)
    except Exception:
        return False


def _browser_path() -> str:
    try:
        raw_url = str(st.context.url or "").strip()
        path = urlsplit(raw_url).path or "/"
        return path.rstrip("/") or "/"
    except Exception:
        return ""


def _iter_pages(pages: Any) -> Iterable[Any]:
    if isinstance(pages, Mapping):
        for section_pages in pages.values():
            yield from _iter_pages(section_pages)
        return
    if isinstance(pages, (list, tuple)):
        for page in pages:
            yield page
        return
    yield pages


# Cache the unmodified authorizer once, then reinstall the H13R2 wrapper on every
# rerun. When Streamlit has already created the native identity, leave the consumed
# authorization request behind and let the production entrypoint finalize the URL.
# Unauthenticated requests still render the accepted authorizer.
_BASE_AUTHORIZER = getattr(
    _root_authorization_ui,
    "_hm_h13r2_base_render_root_authorization_ui",
    None,
)
if _BASE_AUTHORIZER is None:
    _BASE_AUTHORIZER = _root_authorization_ui.render_root_authorization_ui
    _root_authorization_ui._hm_h13r2_base_render_root_authorization_ui = (
        _BASE_AUTHORIZER
    )
else:
    _root_authorization_ui.render_root_authorization_ui = _BASE_AUTHORIZER


def _render_root_authorization_ui_for_native_router(authorization_id: str) -> None:
    if _native_identity_present():
        return
    _BASE_AUTHORIZER(authorization_id)


_root_authorization_ui.render_root_authorization_ui = (
    _render_root_authorization_ui_for_native_router
)


def _fast_finalize_authenticated_root() -> None:
    """Move an authenticated OAuth callback to clean /Login before app boot.

    The previous implementation allowed the full Member/Admin runtime to render and
    then refreshed the browser. That worked functionally but added visible delay.
    When the native identity is present and the browser is still at the app root,
    render only a lightweight finalization overlay, replace the top-level URL with
    the configured clean Login URL, and stop this run before heavy pages load.
    """
    if not _native_identity_present() or _browser_path() != "/":
        return

    clean_login_url = _root_authorization_ui._secret(
        "AUTH_CLIENT_LOGIN_URL",
        _root_authorization_ui.DEFAULT_CLIENT_LOGIN_URL,
    )
    st.html(
        """
        <script>
        (() => {
          let topWindow;
          try {
            topWindow = window.top || window.parent || window;
          } catch (_error) {
            topWindow = window;
          }

          try {
            const doc = topWindow.document;
            if (doc && doc.body && !doc.getElementById("hm-h13r2-login-finalising")) {
              const overlay = doc.createElement("div");
              overlay.id = "hm-h13r2-login-finalising";
              overlay.textContent = "Finalising secure login…";
              overlay.style.cssText = [
                "position:fixed",
                "inset:0",
                "z-index:2147483647",
                "display:flex",
                "align-items:center",
                "justify-content:center",
                "background:#fffaf2",
                "color:#073b2c",
                "font:600 16px system-ui,sans-serif"
              ].join(";");
              doc.body.appendChild(overlay);
            }
          } catch (_overlayError) {}

          const cleanLoginUrl = __CLEAN_LOGIN_URL__;
          topWindow.setTimeout(() => {
            try {
              topWindow.location.replace(cleanLoginUrl);
            } catch (_redirectError) {
              window.location.replace(cleanLoginUrl);
            }
          }, 10);
        })();
        </script>
        """.replace("__CLEAN_LOGIN_URL__", json.dumps(clean_login_url)),
        unsafe_allow_javascript=True,
    )
    st.stop()


def _navigation_with_authenticated_root_canonicalization(
    pages: Any,
    *args: Any,
    **kwargs: Any,
) -> Any:
    selected_page = _BASE_NAVIGATION(pages, *args, **kwargs)

    # Fallback for environments where the early browser redirect cannot run. The
    # registered Login page clears the stale OAuth query and lets the accepted role
    # router select canonical Member/Admin Home on the next run.
    if _native_identity_present() and _browser_path() == "/":
        login_page = next(
            (
                page
                for page in _iter_pages(pages)
                if str(getattr(page, "url_path", "") or "") == "Login"
            ),
            None,
        )
        if login_page is None:
            raise RuntimeError(
                "H13R2 could not locate the registered Login page for OAuth canonicalization."
            )
        _BASE_SWITCH_PAGE(login_page, query_params={})
        st.stop()

    return selected_page


st.navigation = _navigation_with_authenticated_root_canonicalization
_fast_finalize_authenticated_root()


CUTOVER_ENTRY = (
    Path(__file__).resolve().parent
    / "production_cutover"
    / "production_live_cutover_app.py"
)

runpy.run_path(
    str(CUTOVER_ENTRY),
    run_name="__hm_h13r2_production_entry__",
)
