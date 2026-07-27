from __future__ import annotations

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


def _install_one_time_post_oauth_reload() -> None:
    """Refresh the browser once when the consumed OAuth URL is still visible.

    Streamlit Cloud can expose a clean server-side page context while the top-level
    browser still shows ``?authorization_id=...``. A real browser refresh reliably
    reconciles those two states. The per-authorization sessionStorage/window.name
    marker prevents refresh loops and leaves normal Member/Admin pages untouched.
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


# Cache the unmodified authorizer once, then reinstall the H13R2 wrapper on every
# rerun. When Streamlit has already created the native identity, leave the consumed
# authorization request behind and let registered multipage navigation canonicalize
# the browser path. Unauthenticated requests still render the accepted authorizer.
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


def _navigation_with_authenticated_root_canonicalization(
    pages: Any,
    *args: Any,
    **kwargs: Any,
) -> Any:
    selected_page = _BASE_NAVIGATION(pages, *args, **kwargs)

    # Streamlit's OAuth return can restore the app root in the browser while the
    # native identity and remembered selected page are already active. Detect that
    # mismatch from st.context.url instead of relying on st.query_params, which is
    # not consistently populated on the restored callback request in Cloud.
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

        # The clean Login run retains st.user, resolves the HealthyMe role, and then
        # switches to the canonical Member/Admin destination. Passing an empty query
        # dictionary explicitly clears the consumed OAuth authorization parameter.
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
    run_name="__hm_h13r2_production_entry__",
)
