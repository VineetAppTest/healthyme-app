from __future__ import annotations

import json
import runpy
from pathlib import Path

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


# Supabase can return the browser to the one-time authorization URL after the
# native Streamlit identity has already been created. Streamlit query mutation
# can trigger a rerun before browser-level JavaScript executes. Use only a
# top-window redirect so the stale authorization URL is replaced deterministically.
from native_bridge import root_authorization_ui as _root_authorization_ui  # noqa: E402


def _native_identity_present() -> bool:
    try:
        return bool(st.user and st.user.is_logged_in)
    except Exception:
        return False


if not getattr(
    _root_authorization_ui,
    "_hm_h13r2_consumed_query_patch_installed",
    False,
):
    _original_render_root_authorization_ui = (
        _root_authorization_ui.render_root_authorization_ui
    )

    def _render_root_authorization_ui_with_clean_redirect(
        authorization_id: str,
    ) -> None:
        if _native_identity_present():
            clean_login_url = _root_authorization_ui._secret(
                "AUTH_CLIENT_LOGIN_URL",
                _root_authorization_ui.DEFAULT_CLIENT_LOGIN_URL,
            )
            st.html(
                "<script>"
                f"window.top.location.replace({json.dumps(clean_login_url)});"
                "</script>",
                unsafe_allow_javascript=True,
            )
            st.stop()
        _original_render_root_authorization_ui(authorization_id)

    _root_authorization_ui.render_root_authorization_ui = (
        _render_root_authorization_ui_with_clean_redirect
    )
    _root_authorization_ui._hm_h13r2_consumed_query_patch_installed = True


CUTOVER_ENTRY = (
    Path(__file__).resolve().parent
    / "production_cutover"
    / "production_live_cutover_app.py"
)

runpy.run_path(
    str(CUTOVER_ENTRY),
    run_name="__hm_h13r2_production_entry__",
)
