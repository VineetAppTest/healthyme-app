from __future__ import annotations

import runpy
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlsplit

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


def _native_identity_present() -> bool:
    try:
        return bool(st.user and st.user.is_logged_in)
    except Exception:
        return False


def _browser_request() -> tuple[str, dict[str, list[str]]]:
    try:
        raw_url = str(st.context.url or "").strip()
        parsed = urlsplit(raw_url)
        path = (parsed.path or "/").rstrip("/") or "/"
        return path, parse_qs(parsed.query, keep_blank_values=True)
    except Exception:
        return "", {}


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


def _page_for_path(pages: Any, browser_path: str) -> Any | None:
    normalized_path = browser_path.strip("/")
    for page in _iter_pages(pages):
        page_path = str(getattr(page, "url_path", "") or "").strip("/")
        if page_path == normalized_path:
            return page
    return None


# Cache the unmodified authorizer once, then reinstall the production wrapper on
# every rerun. Unauthenticated authorization requests render the HealthyMe
# credential screen. Once native identity exists, the consumed request is left for
# the registered navigation wrapper to canonicalize without showing another screen.
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

# The accepted Gate 4/full-member runtime imports the legacy authorizer module
# directly. Point that module at the H13R7E wrapper before the production runtime is
# compiled, otherwise production continues to render the previous abstract-art UI.
_router_authorization_ui.render_root_authorization_ui = (
    _render_root_authorization_ui_for_native_router
)


def _navigation_with_authenticated_url_cleanup(
    pages: Any,
    *args: Any,
    **kwargs: Any,
) -> Any:
    selected_page = _BASE_NAVIGATION(pages, *args, **kwargs)

    if not _native_identity_present():
        return selected_page

    browser_path, query = _browser_request()

    # The OAuth authorization_id is one-time technical state. Never leave it on a
    # Member/Admin URL. Re-open the same registered page with an empty query string.
    if "authorization_id" in query:
        target_page = _page_for_path(pages, browser_path) or selected_page
        _BASE_SWITCH_PAGE(target_page, query_params={})
        st.stop()

    # Streamlit can restore an authenticated callback at the root path. Move through
    # the registered Login page so the existing role router selects Member/Admin.
    if browser_path == "/":
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
                "H13R5 could not locate the registered Login page for OAuth canonicalization."
            )
        _BASE_SWITCH_PAGE(login_page, query_params={})
        st.stop()

    return selected_page


st.navigation = _navigation_with_authenticated_url_cleanup


CUTOVER_ENTRY = (
    Path(__file__).resolve().parent
    / "production_cutover"
    / "production_live_cutover_app.py"
)

runpy.run_path(
    str(CUTOVER_ENTRY),
    run_name="__hm_h13r5_production_entry__",
)
