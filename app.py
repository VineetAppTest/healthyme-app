from __future__ import annotations

import runpy
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

import streamlit as st


# Streamlit reruns reuse the same Python process. Always restore the process-level
# routing primitives before installing the current production wrapper.
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


from native_bridge import root_authorization_ui as _router_authorization_ui  # noqa: E402
from native_bridge import root_authorization_ui_h13r7e as _root_authorization_ui  # noqa: E402


BUILD = "H13R9-pr205-one-time-refresh-v1"
ROLLBACK_BUILD = "H13R5-production-direct-login-v1"


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


def _install_one_time_post_oauth_reload() -> None:
    """Restore the PR #205 browser refresh after OAuth identity is created.

    Streamlit Cloud can expose a clean server-side route while the top-level browser
    still shows the consumed ``authorization_id`` callback. PR #205 proved that one
    guarded full browser reload reconciles those states and then lets the registered
    role router land on the canonical Member/Admin route.
    """
    if not _native_identity_present():
        return

    st.html(
        r"""
        <script>
        (() => {
          let topWindow;
          try {
            topWindow = window.top || window.parent || window;
          } catch (_error) {
            topWindow = window;
          }

          let currentUrl;
          try {
            currentUrl = new URL(topWindow.location.href);
          } catch (_error) {
            return;
          }

          const authorizationId = currentUrl.searchParams.get("authorization_id");
          if (!authorizationId) {
            return;
          }

          const key = `hm_h13r2_oauth_reload:${authorizationId}`;
          let shouldReload = true;

          try {
            const storage = topWindow.sessionStorage;
            if (storage.getItem(key) === "done") {
              storage.removeItem(key);
              shouldReload = false;
            } else {
              storage.setItem(key, "done");
            }
          } catch (_storageError) {
            const marker = `|${key}|`;
            const currentName = String(topWindow.name || "");
            if (currentName.includes(marker)) {
              topWindow.name = currentName.replace(marker, "");
              shouldReload = false;
            } else {
              topWindow.name = `${currentName}${marker}`;
            }
          }

          if (!shouldReload) {
            return;
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

          topWindow.setTimeout(() => topWindow.location.reload(), 40);
        })();
        </script>
        """,
        unsafe_allow_javascript=True,
    )


# Keep the accepted H13R7E HealthyMe-branded authorizer. Once native identity exists,
# leave the consumed request for the PR #205 refresh and registered role router.
_BASE_AUTHORIZER = getattr(
    _root_authorization_ui,
    "_hm_h13r9_base_render_root_authorization_ui",
    None,
)
if _BASE_AUTHORIZER is None:
    _BASE_AUTHORIZER = _root_authorization_ui.render_root_authorization_ui
    _root_authorization_ui._hm_h13r9_base_render_root_authorization_ui = (
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

# The compiled full Member/Admin runtime imports the legacy authorizer module.
# Point it to the accepted H13R7E wrapper without altering the login-page UX.
_router_authorization_ui.render_root_authorization_ui = (
    _render_root_authorization_ui_for_native_router
)


def _navigation_with_authenticated_root_canonicalization(
    pages: Any,
    *args: Any,
    **kwargs: Any,
) -> Any:
    selected_page = _BASE_NAVIGATION(pages, *args, **kwargs)

    # After the guarded browser refresh, an authenticated callback can re-enter at
    # the app root. Move through the registered Login page with an empty query set;
    # the existing role router then selects Member_Home or the correct Admin route.
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
                "H13R9 could not locate the registered Login page for OAuth canonicalization."
            )
        _BASE_SWITCH_PAGE(login_page, query_params={})
        st.stop()

    return selected_page


st.navigation = _navigation_with_authenticated_root_canonicalization
_install_one_time_post_oauth_reload()


CUTOVER_ENTRY = (
    Path(__file__).resolve().parent
    / "production_cutover"
    / "production_live_cutover_app.py"
)

runpy.run_path(
    str(CUTOVER_ENTRY),
    run_name="__hm_h13r9_pr205_one_time_refresh__",
)
