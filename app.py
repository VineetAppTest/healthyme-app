from __future__ import annotations

import runpy
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any

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
_AUTH_CANONICAL_SWITCH_FLAG = "_hm_h13r2_force_canonical_after_authorization"


from native_bridge import root_authorization_ui as _root_authorization_ui  # noqa: E402


def _native_identity_present() -> bool:
    try:
        return bool(st.user and st.user.is_logged_in)
    except Exception:
        return False


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


# Cache the unmodified authorizer once, then reinstall the current H13R2 wrapper on
# every rerun. This avoids process-level wrapper accumulation while preserving the
# unauthenticated Supabase authorization screen.
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
        # The OAuth request has already created the native Streamlit identity. Defer
        # canonicalization until st.navigation has registered its real Login page.
        st.session_state[_AUTH_CANONICAL_SWITCH_FLAG] = True
        return
    _BASE_AUTHORIZER(authorization_id)


_root_authorization_ui.render_root_authorization_ui = (
    _render_root_authorization_ui_for_native_router
)


def _navigation_with_post_oauth_canonical_switch(
    pages: Any,
    *args: Any,
    **kwargs: Any,
) -> Any:
    selected_page = _BASE_NAVIGATION(pages, *args, **kwargs)

    if st.session_state.get(_AUTH_CANONICAL_SWITCH_FLAG):
        login_page = next(
            (
                page
                for page in _iter_pages(pages)
                if str(getattr(page, "url_path", "") or "") == "Login"
            ),
            None,
        )
        st.session_state.pop(_AUTH_CANONICAL_SWITCH_FLAG, None)
        if login_page is None:
            raise RuntimeError(
                "H13R2 could not locate the registered Login page after OAuth authorization."
            )

        # Streamlit multipage navigation clears non-embed query parameters when
        # query_params is omitted/empty. The next native-router run sees the existing
        # identity on /Login and resolves it to canonical Member/Admin destination.
        _BASE_SWITCH_PAGE(login_page, query_params={})
        st.stop()

    return selected_page


st.navigation = _navigation_with_post_oauth_canonical_switch


CUTOVER_ENTRY = (
    Path(__file__).resolve().parent
    / "production_cutover"
    / "production_live_cutover_app.py"
)

runpy.run_path(
    str(CUTOVER_ENTRY),
    run_name="__hm_h13r2_production_entry__",
)
