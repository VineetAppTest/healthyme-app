import json
import os
import runpy
import sys
from pathlib import Path
from typing import Any, Callable

import streamlit as st

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from components.admin_role_model import (  # noqa: E402
    apply_app_user_to_session,
    is_admin_role,
    is_member_role,
    resolve_app_user,
)
from native_bridge.root_authorization_ui import render_root_authorization_ui  # noqa: E402


BUILD = "H13Q6-native-gate4-real-todays-plan-v1"
SUPPORTED_PROVIDER = "supabaseoidc"
ROUTER_CONTEXT: dict[str, Any] = {}

_DERIVED_CONTEXT_KEYS = {
    "logged_in",
    "user_id",
    "user_role",
    "role",
    "user_name",
    "user_email",
    "must_reset_password",
    "oidc_email",
    "auth_login_method",
    "auth_provider",
    "_hm_auth_role_resolved",
    "_hm_role_model",
    "supabase_auth_email",
    "supabase_auth_user_id",
    "is_admin",
    "admin_logged_in",
    "is_member",
    "_hm_native_gate4_embedded",
    "_hm_gate4_blocked_target",
    "hm_daily_log_target_tab",
}


def _secret(name: str, default: str = "") -> str:
    value = os.environ.get(name)
    if value is not None:
        return str(value).strip()
    try:
        value = st.secrets.get(name)
    except Exception:
        value = None
    return str(value if value is not None else default).strip()


def _native_identity_present() -> bool:
    try:
        return bool(st.user and st.user.is_logged_in)
    except Exception:
        return False


def _claim(name: str) -> str:
    try:
        value = st.user.get(name)
    except Exception:
        try:
            value = getattr(st.user, name, "")
        except Exception:
            value = ""
    return str(value or "").strip()


def _safe_cookie_snapshot() -> dict[str, Any]:
    try:
        names = {str(name) for name in st.context.cookies.keys()}
    except Exception:
        names = set()

    def piece_count(base_name: str) -> int:
        count = 1 if base_name in names else 0
        prefix = f"{base_name}_"
        for name in names:
            if name.startswith(prefix) and name[len(prefix):].isdigit():
                count += 1
        return count

    identity_count = piece_count("_streamlit_user")
    token_count = piece_count("_streamlit_user_tokens")
    return {
        "native_identity_cookie_present": identity_count > 0,
        "native_identity_cookie_piece_count": identity_count,
        "native_tokens_cookie_present": token_count > 0,
        "native_tokens_cookie_piece_count": token_count,
        "cookie_values_displayed": False,
    }


def _role_category(role: str) -> str:
    if is_admin_role(role):
        return "Admin"
    if is_member_role(role):
        return "Member"
    return "Unsupported"


def _clear_derived_application_context() -> None:
    for key in _DERIVED_CONTEXT_KEYS:
        st.session_state.pop(key, None)


def _native_logout() -> None:
    _clear_derived_application_context()
    st.logout()
    st.stop()


def _snapshot(route_name: str, route_allowed: bool) -> dict[str, Any]:
    return {
        "build": BUILD,
        "configured_provider": ROUTER_CONTEXT.get("provider", SUPPORTED_PROVIDER),
        "native_identity_present": bool(ROUTER_CONTEXT.get("native_identity_present")),
        "email_claim_present": bool(ROUTER_CONTEXT.get("email_claim_present")),
        "subject_claim_present": bool(ROUTER_CONTEXT.get("subject_claim_present")),
        "healthyme_role_lookup_used": bool(ROUTER_CONTEXT.get("role_lookup_used")),
        "healthyme_role_resolved": bool(ROUTER_CONTEXT.get("role_resolved")),
        "resolved_role_category": ROUTER_CONTEXT.get("role_category", "None"),
        "selected_route": route_name,
        "selected_navigation_path": ROUTER_CONTEXT.get("selected_navigation_path", ""),
        "protected_page_routing_used": True,
        "route_allowed_for_role": route_allowed,
        "central_router_executed_first": True,
        "authorization_ui_root_hosted": True,
        "application_session_state_auth_source": False,
        "derived_application_context_applied": bool(
            ROUTER_CONTEXT.get("derived_application_context_applied")
        ),
        "real_member_home_loaded": bool(ROUTER_CONTEXT.get("real_member_home_loaded")),
        "real_todays_plan_loaded": bool(ROUTER_CONTEXT.get("real_todays_plan_loaded")),
        "legacy_page_guard_used": False,
        "legacy_keepalive_guard_used": False,
        "legacy_logout_used": False,
        "custom_browser_marker_used": False,
        "durable_auth_session_used": False,
        "local_storage_used": False,
        **_safe_cookie_snapshot(),
    }


def _root_page() -> None:
    st.empty()


def _login_page() -> None:
    st.title("HealthyMe native role router")
    st.caption(
        "Gate 4 retains the accepted native identity, real Member Home and central "
        "router, then connects the real Today's Plan as the first downstream route."
    )
    st.code(BUILD)
    st.metric("Native Streamlit identity", "Absent")
    st.code(
        json.dumps(
            {
                "build": BUILD,
                "native_identity_present": False,
                "healthyme_role_lookup_used": False,
                "healthyme_role_resolved": False,
                "selected_navigation_path": ROUTER_CONTEXT.get(
                    "selected_navigation_path", ""
                ),
                "protected_page_routing_used": True,
                "central_router_executed_first": True,
                "authorization_ui_root_hosted": True,
                "application_session_state_auth_source": False,
                "real_member_home_loaded": False,
                "real_todays_plan_loaded": False,
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
        type="primary",
        use_container_width=True,
    ):
        st.login(ROUTER_CONTEXT.get("provider", SUPPORTED_PROVIDER))
        st.stop()


def _logout_button(key: str) -> None:
    if st.button("Logout", key=key, use_container_width=True):
        _native_logout()


def _admin_page() -> None:
    allowed = ROUTER_CONTEXT.get("role_category") == "Admin"
    st.title("Admin Dashboard — Gate 4 protected route")
    if allowed:
        st.success(
            "Native identity was restored, HealthyMe resolved the Admin role, and "
            "the central router allowed this protected route."
        )
    else:
        st.error("The central router allowed an invalid Admin-route state.")
    st.caption(
        "Gate 4 changes only the Member Home → Today's Plan route. The real Admin "
        "Dashboard remains outside this sprint."
    )
    st.code(BUILD)
    st.code(
        json.dumps(
            _snapshot("/Admin_Dashboard", allowed),
            indent=2,
            sort_keys=True,
        ),
        language="json",
    )
    _logout_button("h13q6_admin_logout")


def _blocked_destination(target: Any, *, source: str) -> None:
    clean_target = str(target or "").strip()
    st.session_state["_hm_gate4_blocked_target"] = clean_target
    st.warning(
        f"Gate 4 currently validates {source} only. This destination has not yet "
        "been connected to the native protected router."
    )


def _member_home_switch_handler(
    original_switch_page: Callable[..., Any],
    target: Any,
) -> None:
    clean_target = str(target or "").strip()
    if clean_target == "pages/36_Todays_Journey.py":
        original_switch_page(todays_plan_page)
        st.stop()
    _blocked_destination(clean_target, source="Member Home and Today's Plan")


def _todays_plan_switch_handler(
    original_switch_page: Callable[..., Any],
    target: Any,
) -> None:
    clean_target = str(target or "").strip()
    if clean_target == "pages/02_Member_Home.py":
        original_switch_page(member_page)
        st.stop()
    _blocked_destination(clean_target, source="the real Today's Plan")


def _native_member_utility_bar() -> None:
    email = (
        st.session_state.get("user_email")
        or st.session_state.get("oidc_email")
        or _claim("email")
        or "member"
    )
    identity_col, logout_col = st.columns([6.8, 1.1], gap="small")
    with identity_col:
        st.markdown(
            f"<div class='utility-bar'><span class='utility-user'>Signed in as: "
            f"<b>{email}</b><span class='utility-role'>Active member</span></span></div>",
            unsafe_allow_html=True,
        )
    with logout_col:
        if st.button(
            "Logout",
            key="h13q6_todays_plan_logout",
            use_container_width=True,
        ):
            _native_logout()


def _native_todays_plan_nav(
    original_switch_page: Callable[..., Any],
    *args: Any,
    **kwargs: Any,
) -> None:
    st.markdown("<div class='hm-bottom-nav-shell'></div>", unsafe_allow_html=True)
    if st.button(
        "Back to Member Home",
        key="h13q6_todays_plan_back_home",
        use_container_width=True,
    ):
        original_switch_page(member_page)
        st.stop()


def _render_real_member_home() -> None:
    import components.auth_session as auth_session
    import components.guards as guards
    import components.ui_common as ui_common

    original_require_member = guards.require_member
    original_auth_logout = auth_session.logout_current_user
    original_ui_logout = ui_common.logout_current_user
    original_keepalive = ui_common.inject_keepalive_guard_v96_11
    original_set_page_config = st.set_page_config
    original_switch_page = st.switch_page

    guards.require_member = lambda: None
    auth_session.logout_current_user = _native_logout
    ui_common.logout_current_user = _native_logout
    ui_common.inject_keepalive_guard_v96_11 = lambda: None
    st.set_page_config = lambda *args, **kwargs: None
    st.switch_page = lambda target, *args, **kwargs: _member_home_switch_handler(
        original_switch_page, target
    )

    st.session_state["_hm_native_gate4_embedded"] = True
    ROUTER_CONTEXT["real_member_home_loaded"] = True
    ROUTER_CONTEXT["real_todays_plan_loaded"] = False

    try:
        runpy.run_path(
            str(REPOSITORY_ROOT / "pages" / "02_Member_Home.py"),
            run_name="__hm_gate4_real_member_home__",
        )
    finally:
        guards.require_member = original_require_member
        auth_session.logout_current_user = original_auth_logout
        ui_common.logout_current_user = original_ui_logout
        ui_common.inject_keepalive_guard_v96_11 = original_keepalive
        st.set_page_config = original_set_page_config
        st.switch_page = original_switch_page

    st.caption(f"Gate 4 test build: {BUILD}")


def _render_real_todays_plan() -> None:
    import components.auth_session as auth_session
    import components.guards as guards
    import components.ui_common as ui_common

    original_require_member = guards.require_member
    original_auth_logout = auth_session.logout_current_user
    original_ui_logout = ui_common.logout_current_user
    original_utility_logout_bar = ui_common.utility_logout_bar
    original_render_page_nav = ui_common.render_page_nav
    original_set_page_config = st.set_page_config
    original_switch_page = st.switch_page

    guards.require_member = lambda: None
    auth_session.logout_current_user = _native_logout
    ui_common.logout_current_user = _native_logout
    ui_common.utility_logout_bar = _native_member_utility_bar
    ui_common.render_page_nav = (
        lambda *args, **kwargs: _native_todays_plan_nav(
            original_switch_page, *args, **kwargs
        )
    )
    st.set_page_config = lambda *args, **kwargs: None
    st.switch_page = lambda target, *args, **kwargs: _todays_plan_switch_handler(
        original_switch_page, target
    )

    st.session_state["_hm_native_gate4_embedded"] = True
    ROUTER_CONTEXT["real_member_home_loaded"] = False
    ROUTER_CONTEXT["real_todays_plan_loaded"] = True

    try:
        runpy.run_path(
            str(REPOSITORY_ROOT / "pages" / "36_Todays_Journey.py"),
            run_name="__hm_gate4_real_todays_plan__",
        )
    finally:
        guards.require_member = original_require_member
        auth_session.logout_current_user = original_auth_logout
        ui_common.logout_current_user = original_ui_logout
        ui_common.utility_logout_bar = original_utility_logout_bar
        ui_common.render_page_nav = original_render_page_nav
        st.set_page_config = original_set_page_config
        st.switch_page = original_switch_page

    st.caption(f"Gate 4 test build: {BUILD}")


def _member_home_page() -> None:
    if ROUTER_CONTEXT.get("role_category") != "Member":
        st.error("The central router allowed an invalid Member Home state.")
        st.code(json.dumps(_snapshot("/Member_Home", False), indent=2, sort_keys=True))
        st.stop()
    _render_real_member_home()


def _todays_plan_page() -> None:
    if ROUTER_CONTEXT.get("role_category") != "Member":
        st.error("The central router allowed an invalid Today's Plan state.")
        st.code(json.dumps(_snapshot("/Todays_Plan", False), indent=2, sort_keys=True))
        st.stop()
    _render_real_todays_plan()


def _show_role_resolution_failure(
    *,
    role_lookup_ok: bool,
    lookup_message: str,
) -> None:
    st.title("HealthyMe access mapping unavailable")
    st.warning(
        "The native Supabase OIDC identity is active, but HealthyMe could not resolve "
        "an authorized Admin or Member role. This is not a logout."
    )
    st.code(BUILD)
    st.code(
        json.dumps(
            {
                **_snapshot("", False),
                "role_lookup_completed": bool(role_lookup_ok),
            },
            indent=2,
            sort_keys=True,
        ),
        language="json",
    )
    st.caption(lookup_message or "No active HealthyMe role mapping was returned.")
    _logout_button("h13q6_mapping_logout")
    st.stop()


st.set_page_config(
    page_title="HealthyMe Native Gate 4",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="collapsed",
)

provider = _secret("AUTH_BRIDGE_PROVIDER", SUPPORTED_PROVIDER).lower()
if provider != SUPPORTED_PROVIDER:
    st.error("AUTH_BRIDGE_PROVIDER must be 'supabaseoidc' for this deployment.")
    st.stop()

authorization_id = str(st.query_params.get("authorization_id") or "").strip()
if authorization_id:
    render_root_authorization_ui(authorization_id)

root_page = st.Page(_root_page, title="HealthyMe", icon="🌿", default=True)
login_page = st.Page(_login_page, title="Login", url_path="Login")
admin_page = st.Page(
    _admin_page,
    title="Admin Dashboard",
    url_path="Admin_Dashboard",
)
member_page = st.Page(
    _member_home_page,
    title="Member Home",
    url_path="Member_Home",
)
todays_plan_page = st.Page(
    _todays_plan_page,
    title="Today's Plan",
    url_path="Todays_Plan",
)

selected_page = st.navigation(
    [root_page, login_page, admin_page, member_page, todays_plan_page],
    position="hidden",
)
selected_path = str(selected_page.url_path or "")
ROUTER_CONTEXT["provider"] = provider
ROUTER_CONTEXT["selected_navigation_path"] = selected_path
native_identity_present = _native_identity_present()
ROUTER_CONTEXT["native_identity_present"] = native_identity_present

if not native_identity_present:
    _clear_derived_application_context()
    if selected_path != login_page.url_path:
        st.switch_page(login_page)
    selected_page.run()
    st.stop()

email = _claim("email").lower()
subject = _claim("sub")
ROUTER_CONTEXT["email_claim_present"] = bool(email)
ROUTER_CONTEXT["subject_claim_present"] = bool(subject)

if not email and not subject:
    ROUTER_CONTEXT["role_lookup_used"] = False
    ROUTER_CONTEXT["role_resolved"] = False
    _show_role_resolution_failure(
        role_lookup_ok=False,
        lookup_message="Neither the email nor subject claim is available.",
    )

role_lookup_ok = False
app_user = None
lookup_message = ""
try:
    role_lookup_ok, app_user, lookup_message = resolve_app_user(
        email=email,
        auth_user_id=subject,
    )
except Exception as exc:
    lookup_message = f"{type(exc).__name__}: role lookup could not complete."

ROUTER_CONTEXT["role_lookup_used"] = True
ROUTER_CONTEXT["role_resolved"] = bool(role_lookup_ok and app_user)

if not role_lookup_ok or not app_user:
    _show_role_resolution_failure(
        role_lookup_ok=role_lookup_ok,
        lookup_message=lookup_message,
    )

role = str(app_user.get("role") or "").strip().lower()
role_category = _role_category(role)
ROUTER_CONTEXT["role_category"] = role_category
ROUTER_CONTEXT["lookup_message"] = lookup_message

if role_category == "Admin":
    _clear_derived_application_context()
    ROUTER_CONTEXT["derived_application_context_applied"] = False
    ROUTER_CONTEXT["real_member_home_loaded"] = False
    ROUTER_CONTEXT["real_todays_plan_loaded"] = False
    if selected_path != admin_page.url_path:
        st.switch_page(admin_page)
    selected_page.run()
    st.stop()

if role_category == "Member":
    try:
        apply_app_user_to_session(
            app_user,
            email=email,
            auth_provider="supabase",
            auth_user_id=subject,
        )
    except Exception as exc:
        _show_role_resolution_failure(
            role_lookup_ok=True,
            lookup_message=(
                f"{type(exc).__name__}: Member compatibility context could not be built."
            ),
        )

    ROUTER_CONTEXT["derived_application_context_applied"] = True
    allowed_member_paths = {member_page.url_path, todays_plan_page.url_path}
    if selected_path not in allowed_member_paths:
        st.switch_page(member_page)
    selected_page.run()
    st.stop()

_show_role_resolution_failure(
    role_lookup_ok=True,
    lookup_message=f"Unsupported HealthyMe role: {role or 'blank'}",
)
