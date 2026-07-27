from __future__ import annotations

import runpy
from pathlib import Path
from urllib.parse import urlsplit

import streamlit as st


# Streamlit reruns reuse the same Python process. The H13R2 integration temporarily
# wraps these routing callables while assembling the real Member/Admin application.
# Restore the process-level originals before every production run so wrappers cannot
# stack and duplicate page registries.
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

_BASE_PAGE = getattr(st, "_hm_h13r2_base_page")
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


def _authorization_query_present() -> bool:
    try:
        return bool(str(st.query_params.get("authorization_id", "") or "").strip())
    except Exception:
        return False


# Cache the accepted authorizer once. When Streamlit has already created the native
# identity, the production entrypoint completes the route handoff instead of asking
# the authorizer to clear query parameters or rerun itself.
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


def _complete_authenticated_oauth_handoff() -> None:
    """Move the authenticated callback to clean /Login without browser JavaScript.

    Streamlit Cloud can return the authenticated browser to the app root with the
    one-time ``authorization_id`` still visible. Register a lightweight temporary
    Login page and switch to it using Streamlit's native multipage navigation. This
    clears the stale query and starts a clean run before the full Member/Admin runtime
    or any database-backed page is loaded.
    """
    if not _native_identity_present():
        return
    if not (_authorization_query_present() or _browser_path() == "/"):
        return

    def _login_handoff_page() -> None:
        st.caption("Finalising secure login…")

    login_handoff_page = _BASE_PAGE(
        _login_handoff_page,
        title="Login",
        url_path="Login",
        default=True,
    )
    _BASE_NAVIGATION([login_handoff_page], position="hidden")
    _BASE_SWITCH_PAGE(login_handoff_page, query_params={})
    st.stop()


_complete_authenticated_oauth_handoff()


CUTOVER_ENTRY = (
    Path(__file__).resolve().parent
    / "production_cutover"
    / "production_live_cutover_app.py"
)

runpy.run_path(
    str(CUTOVER_ENTRY),
    run_name="__hm_h13r2_production_entry__",
)
