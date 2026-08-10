from __future__ import annotations

import inspect
import json
import os
import re
import runpy
import sys
from pathlib import Path
from typing import Any, Callable

import streamlit as st


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from native_bridge.full_member_route_registry import (  # noqa: E402
    MemberRouteSpec,
    discover_member_page_specs,
)


BUILD = "H13Q7-native-full-member-app-v1"
ROLLBACK_BUILD = "H13Q6-native-gate4-real-todays-plan-v1"
GATE4_ENTRY = REPOSITORY_ROOT / "native_bridge" / "native_bridge_gate4_app.py"

_ORIGINAL_PAGE = st.Page
_ORIGINAL_NAVIGATION = st.navigation
_ORIGINAL_SWITCH_PAGE = st.switch_page

_GATE4_GLOBALS: dict[str, Any] = {}
_CORE_PAGES: dict[str, Any] = {}
_FILE_TO_PAGE: dict[str, Any] = {}
_URL_TO_PAGE: dict[str, Any] = {}
_ROUTE_SPECS: list[MemberRouteSpec] = []
_EXTRA_ROUTE_PATHS: set[str] = set()
_SELECTED_PATH = ""
_PENDING_RERUN_PATH_KEY = "_hm_h13r9e_pending_rerun_path"


class _Missing:
    pass


_MISSING = _Missing()


def _normalise_target(target: Any) -> str:
    if not isinstance(target, str):
        return ""
    clean = target.strip().replace("\\", "/")
    while clean.startswith("./"):
        clean = clean[2:]
    return clean


def _route_key(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_]+", "_", value).strip("_").lower() or "member"


def _gate4_context() -> dict[str, Any]:
    context = _GATE4_GLOBALS.get("ROUTER_CONTEXT")
    return context if isinstance(context, dict) else {}


def _native_logout() -> None:
    logout_fn = _GATE4_GLOBALS.get("_native_logout")
    if callable(logout_fn):
        logout_fn()
        st.stop()
    st.logout()
    st.stop()


def _claim(name: str) -> str:
    claim_fn = _GATE4_GLOBALS.get("_claim")
    if callable(claim_fn):
        try:
            return str(claim_fn(name) or "").strip()
        except Exception:
            pass
    try:
        return str(st.user.get(name) or "").strip()
    except Exception:
        return ""


def _safe_cookie_snapshot() -> dict[str, Any]:
    snapshot_fn = _GATE4_GLOBALS.get("_safe_cookie_snapshot")
    if callable(snapshot_fn):
        try:
            value = snapshot_fn()
            if isinstance(value, dict):
                return value
        except Exception:
            pass
    return {
        "native_identity_cookie_present": False,
        "native_identity_cookie_piece_count": 0,
        "native_tokens_cookie_present": False,
        "native_tokens_cookie_piece_count": 0,
        "cookie_values_displayed": False,
    }


def _resolve_page(target: Any) -> Any | None:
    if not isinstance(target, str):
        return None
    clean = _normalise_target(target)
    if clean in _FILE_TO_PAGE:
        return _FILE_TO_PAGE[clean]
    if clean.startswith("/"):
        clean = clean[1:]
    if clean in _URL_TO_PAGE:
        return _URL_TO_PAGE[clean]
    return None


def _global_switch_page(target: Any, *args: Any, **kwargs: Any) -> Any:
    global _SELECTED_PATH

    # Gate 4's original role block only knows Member Home and Today's Plan.
    # When Streamlit has selected one of the newly registered Member routes,
    # suppress that single fallback redirect and allow selected_page.run().
    member_page = _CORE_PAGES.get("Member_Home")
    role_category = str(_gate4_context().get("role_category") or "")
    if (
        _SELECTED_PATH in _EXTRA_ROUTE_PATHS
        and role_category == "Member"
        and member_page is not None
        and target is member_page
    ):
        return None

    resolved = _resolve_page(target)
    if resolved is not None:
        return _ORIGINAL_SWITCH_PAGE(resolved)
    return _ORIGINAL_SWITCH_PAGE(target, *args, **kwargs)


def _embedded_switch_handler(
    _original_switch_page: Callable[..., Any],
    target: Any,
) -> None:
    resolved = _resolve_page(target)
    if resolved is not None:
        resolved_path = (
            str(getattr(resolved, "url_path", "") or "").strip().strip("/")
        )
        if resolved_path:
            st.session_state[_PENDING_RERUN_PATH_KEY] = resolved_path
        _ORIGINAL_SWITCH_PAGE(resolved)
        st.stop()

    clean = _normalise_target(target)
    st.warning(
        "This destination is not registered in the consolidated native Member "
        f"router: {clean or type(target).__name__}. The current page remains active."
    )


def _native_utility_bar(route_key: str, *args: Any, **kwargs: Any) -> None:
    email = (
        st.session_state.get("user_email")
        or st.session_state.get("oidc_email")
        or _claim("email")
        or "member"
    )
    identity_col, logout_col = st.columns([6.8, 1.1], gap="small")
    with identity_col:
        st.markdown(
            "<div class='utility-bar'><span class='utility-user'>Signed in as: "
            f"<b>{email}</b><span class='utility-role'>Active member</span>"
            "</span></div>",
            unsafe_allow_html=True,
        )
    with logout_col:
        if st.button(
            "Logout",
            key=f"h13q7_{_route_key(route_key)}_logout",
            use_container_width=True,
        ):
            _native_logout()


def _save_attr(obj: Any, name: str) -> Any:
    return getattr(obj, name, _MISSING)


def _restore_attr(obj: Any, name: str, value: Any) -> None:
    if value is _MISSING:
        try:
            delattr(obj, name)
        except Exception:
            pass
    else:
        setattr(obj, name, value)


def _render_member_route(spec: MemberRouteSpec) -> None:
    context = _gate4_context()
    if str(context.get("role_category") or "") != "Member":
        admin_page = _CORE_PAGES.get("Admin_Dashboard")
        if admin_page is not None:
            _ORIGINAL_SWITCH_PAGE(admin_page)
            st.stop()
        st.error("The native router rejected this Member route.")
        st.stop()

    import components.auth_session as auth_session
    import components.guards as guards
    import components.ui_common as ui_common

    saved = {
        ("guards", "require_member"): _save_attr(guards, "require_member"),
        ("auth_session", "logout_current_user"): _save_attr(
            auth_session, "logout_current_user"
        ),
        ("ui_common", "logout_current_user"): _save_attr(
            ui_common, "logout_current_user"
        ),
        ("ui_common", "utility_logout_bar"): _save_attr(
            ui_common, "utility_logout_bar"
        ),
        ("streamlit", "set_page_config"): st.set_page_config,
        ("streamlit", "switch_page"): st.switch_page,
    }
    keepalive_saved: dict[str, Any] = {}
    for name in dir(ui_common):
        if name.startswith("inject_keepalive"):
            keepalive_saved[name] = getattr(ui_common, name)

    guards.require_member = lambda: None
    auth_session.logout_current_user = _native_logout
    ui_common.logout_current_user = _native_logout
    ui_common.utility_logout_bar = (
        lambda *args, **kwargs: _native_utility_bar(spec.url_path, *args, **kwargs)
    )
    for name in keepalive_saved:
        setattr(ui_common, name, lambda *args, **kwargs: None)
    st.set_page_config = lambda *args, **kwargs: None
    st.switch_page = lambda target, *args, **kwargs: _embedded_switch_handler(
        _ORIGINAL_SWITCH_PAGE,
        target,
    )

    st.session_state["_hm_native_full_member_embedded"] = True
    st.session_state["_hm_native_full_member_route"] = spec.source_path
    context["real_member_home_loaded"] = False
    context["real_todays_plan_loaded"] = False
    context["full_member_page_loaded"] = True
    context["active_member_source"] = spec.source_path
    context["active_member_checkpoint"] = spec.checkpoint

    source_file = REPOSITORY_ROOT / spec.source_path
    try:
        runpy.run_path(
            str(source_file),
            run_name=f"__hm_h13q7_{_route_key(spec.filename)}__",
        )
    except Exception as exc:
        if type(exc).__name__ in {"StopException", "RerunException"}:
            raise
        st.error(
            "This HealthyMe Member page could not complete under the native router. "
            "The native identity remains active so the failing route can be isolated."
        )
        st.code(
            json.dumps(
                {
                    "build": BUILD,
                    "source_page": spec.source_path,
                    "url_path": f"/{spec.url_path}",
                    "checkpoint": spec.checkpoint,
                    "error_type": type(exc).__name__,
                    "error_message": str(exc),
                    "rollback_build": ROLLBACK_BUILD,
                },
                indent=2,
                sort_keys=True,
            ),
            language="json",
        )
    finally:
        _restore_attr(guards, "require_member", saved[("guards", "require_member")])
        _restore_attr(
            auth_session,
            "logout_current_user",
            saved[("auth_session", "logout_current_user")],
        )
        _restore_attr(
            ui_common,
            "logout_current_user",
            saved[("ui_common", "logout_current_user")],
        )
        _restore_attr(
            ui_common,
            "utility_logout_bar",
            saved[("ui_common", "utility_logout_bar")],
        )
        for name, value in keepalive_saved.items():
            setattr(ui_common, name, value)
        st.set_page_config = saved[("streamlit", "set_page_config")]
        st.switch_page = saved[("streamlit", "switch_page")]

def _make_member_page(spec: MemberRouteSpec) -> Callable[[], None]:
    def _page() -> None:
        _render_member_route(spec)

    _page.__name__ = f"h13q7_{_route_key(spec.url_path)}"
    return _page


def _login_page() -> None:
    context = _gate4_context()
    provider = str(context.get("provider") or "supabaseoidc")
    route_counts = {
        "read": sum(1 for item in _ROUTE_SPECS if item.checkpoint == "A-read"),
        "write": sum(1 for item in _ROUTE_SPECS if item.checkpoint == "B-write"),
        "remaining": sum(
            1 for item in _ROUTE_SPECS if item.checkpoint == "C-remaining"
        ),
    }
    st.title("HealthyMe native full-member router")
    st.caption(
        "Consolidated Gate 5–7 integration: the accepted Gate 4 identity and role "
        "router now registers the current read, write and remaining Member pages."
    )
    st.code(BUILD)
    st.metric("Native Streamlit identity", "Absent")
    st.code(
        json.dumps(
            {
                "build": BUILD,
                "rollback_build": ROLLBACK_BUILD,
                "native_identity_present": False,
                "full_member_route_count": len(_ROUTE_SPECS) + 2,
                "route_groups": route_counts,
                "real_admin_dashboard_loaded": False,
                "application_session_state_auth_source": False,
                "legacy_page_guard_used": False,
                "custom_browser_marker_used": False,
                "durable_auth_session_used": False,
                "local_storage_used": False,
                **_safe_cookie_snapshot(),
            },
            indent=2,
            sort_keys=True,
        ),
        language="json",
    )
    if st.button(
        "Continue with Supabase OIDC",
        key="h13q7_continue_oidc",
        type="primary",
        use_container_width=True,
    ):
        st.login(provider)
        st.stop()


def _admin_page() -> None:
    context = _gate4_context()
    allowed = str(context.get("role_category") or "") == "Admin"
    st.title("Admin Dashboard — consolidated Member gate regression route")
    if allowed:
        st.success(
            "Native identity was restored, HealthyMe resolved the Admin role, and "
            "the central router kept all real Member pages inaccessible."
        )
    else:
        st.error("The central router allowed an invalid Admin-route state.")
    st.caption(
        "The real Admin Dashboard remains outside this Member integration sprint."
    )
    st.code(BUILD)
    st.code(
        json.dumps(
            {
                "build": BUILD,
                "rollback_build": ROLLBACK_BUILD,
                "native_identity_present": bool(context.get("native_identity_present")),
                "healthyme_role_resolved": bool(context.get("role_resolved")),
                "resolved_role_category": context.get("role_category", "None"),
                "full_member_route_count": len(_ROUTE_SPECS) + 2,
                "real_admin_dashboard_loaded": False,
                "route_allowed_for_role": allowed,
                **_safe_cookie_snapshot(),
            },
            indent=2,
            sort_keys=True,
        ),
        language="json",
    )
    if st.button("Logout", key="h13q7_admin_logout", use_container_width=True):
        _native_logout()


def _rewrite_gate4_caption(original: Callable[[], Any]) -> Callable[[], Any]:
    def _wrapped() -> Any:
        original_caption = st.caption

        def _caption(body: Any, *args: Any, **kwargs: Any) -> Any:
            text = str(body or "")
            if text.startswith("Gate 4 test build:"):
                body = f"Full Member integration build: {BUILD}"
            return original_caption(body, *args, **kwargs)

        st.caption = _caption
        try:
            return original()
        finally:
            st.caption = original_caption

    return _wrapped


def _patched_page(page: Any, *args: Any, **kwargs: Any) -> Any:
    url_path = str(kwargs.get("url_path") or "")
    if url_path == "Login":
        page = _login_page
    elif url_path == "Admin_Dashboard":
        page = _admin_page
    return _ORIGINAL_PAGE(page, *args, **kwargs)


def _patched_navigation(pages: Any, *args: Any, **kwargs: Any) -> Any:
    global _GATE4_GLOBALS
    global _CORE_PAGES
    global _FILE_TO_PAGE
    global _URL_TO_PAGE
    global _ROUTE_SPECS
    global _EXTRA_ROUTE_PATHS
    global _SELECTED_PATH

    caller = inspect.currentframe().f_back
    gate4_globals = caller.f_globals if caller is not None else {}
    _GATE4_GLOBALS = gate4_globals
    gate4_globals["BUILD"] = BUILD

    base_pages = list(pages)
    core_pages = {
        str(getattr(item, "url_path", "")): item for item in base_pages
    }
    _CORE_PAGES = core_pages

    specs = discover_member_page_specs(REPOSITORY_ROOT)
    _ROUTE_SPECS = specs
    extra_pages: list[Any] = []
    for spec in specs:
        page_obj = _ORIGINAL_PAGE(
            _make_member_page(spec),
            title=spec.title,
            url_path=spec.url_path,
        )
        extra_pages.append(page_obj)

    _FILE_TO_PAGE = {
        "app.py": core_pages.get("Member_Home"),
        "pages/01_Login.py": core_pages.get("Login"),
        "pages/02_Member_Home.py": core_pages.get("Member_Home"),
        "pages/10_Admin_Dashboard.py": core_pages.get("Admin_Dashboard"),
        "pages/36_Todays_Journey.py": core_pages.get("Todays_Plan"),
    }
    _URL_TO_PAGE = {
        key: value for key, value in core_pages.items() if value is not None
    }
    for spec, page_obj in zip(specs, extra_pages):
        _FILE_TO_PAGE[spec.source_path] = page_obj
        _URL_TO_PAGE[spec.url_path] = page_obj
    _FILE_TO_PAGE = {
        key: value for key, value in _FILE_TO_PAGE.items() if value is not None
    }
    _EXTRA_ROUTE_PATHS = {spec.url_path for spec in specs}

    gate4_globals["_member_home_switch_handler"] = _embedded_switch_handler
    gate4_globals["_todays_plan_switch_handler"] = _embedded_switch_handler
    for name in ("_render_real_member_home", "_render_real_todays_plan"):
        original = gate4_globals.get(name)
        if callable(original):
            gate4_globals[name] = _rewrite_gate4_caption(original)

    context = _gate4_context()
    context["full_member_route_count"] = len(specs) + 2
    context["rollback_build"] = ROLLBACK_BUILD

    selected = _ORIGINAL_NAVIGATION(
        [*base_pages, *extra_pages],
        *args,
        **kwargs,
    )
    _SELECTED_PATH = str(getattr(selected, "url_path", "") or "")
    return selected


st.Page = _patched_page
st.navigation = _patched_navigation
st.switch_page = _global_switch_page
try:
    runpy.run_path(
        str(GATE4_ENTRY),
        run_name="__hm_h13q7_full_member_bootstrap__",
    )
finally:
    st.Page = _ORIGINAL_PAGE
    st.navigation = _ORIGINAL_NAVIGATION
    st.switch_page = _ORIGINAL_SWITCH_PAGE
