from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any

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
from native_bridge.root_authorization_ui import (  # noqa: E402
    render_root_authorization_ui,
)


BUILD = "H13Q8-production-parity-native-router-v1"
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


def _clear_derived_application_context() -> None:
    for key in _DERIVED_CONTEXT_KEYS:
        st.session_state.pop(key, None)


def _native_logout() -> None:
    _clear_derived_application_context()
    st.logout()
    st.stop()


def _role_category(role: str) -> str:
    if is_admin_role(role):
        return "Admin"
    if is_member_role(role):
        return "Member"
    return "Unsupported"


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


def _diagnostics(route_name: str, route_allowed: bool) -> dict[str, Any]:
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
        "route_allowed_for_role": route_allowed,
        "protected_page_routing_used": True,
        "central_router_executed_first": True,
        "application_session_state_auth_source": False,
        "legacy_page_guard_used": False,
        "custom_browser_marker_used": False,
        "durable_auth_session_used": False,
        "local_storage_used": False,
        **_safe_cookie_snapshot(),
    }


def _root_page() -> None:
    st.empty()


def _login_page() -> None:
    st.title("HealthyMe production-parity native router")
    st.caption(
        "H13Q8 Step 1 validates native Supabase identity, HealthyMe role resolution "
        "and protected Member/Admin shell routing against the production codebase."
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
                "protected_page_routing_used": True,
                "central_router_executed_first": True,
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
        type="primary",
        use_container_width=True,
    ):
        st.login(ROUTER_CONTEXT.get("provider", SUPPORTED_PROVIDER))
        st.stop()


def _logout_button(key: str) -> None:
    if st.button("Logout", key=key, use_container_width=True):
        _native_logout()


def _member_page() -> None:
    allowed = ROUTER_CONTEXT.get("role_category") == "Member"
    st.title("Member Home — H13Q8 production-parity shell")
    if allowed:
        st.success(
            "Native identity was restored, HealthyMe resolved the Member role, and "
            "the central router allowed the protected Member shell."
        )
    else:
        st.error("The central router allowed an invalid Member-route state.")
    st.caption(
        "Step 1 validates the production-parity protected shell only. The full Member "
        "application is connected in Step 2."
    )
    st.code(BUILD)
    st.code(
        json.dumps(_diagnostics("/Member_Home", allowed), indent=2, sort_keys=True),
        language="json",
    )
    _logout_button("h13q8_member_logout")


def _admin_page() -> None:
    allowed = ROUTER_CONTEXT.get("role_category") == "Admin"
    st.title("Admin Dashboard — H13Q8 production-parity shell")
    if allowed:
        st.success(
            "Native identity was restored, HealthyMe resolved the Admin role, and "
            "the central router allowed the protected Admin shell."
        )
    else:
        st.error("The central router allowed an invalid Admin-route state.")
    st.caption(
        "Step 1 validates the production-parity protected shell only. The real "
        "Admin/Nutritionist application is connected in Step 4."
    )
    st.code(BUILD)
    st.code(
        json.dumps(_diagnostics("/Admin_Dashboard", allowed), indent=2, sort_keys=True),
        language="json",
    )
    _logout_button("h13q8_admin_logout")


def _show_role_resolution_failure(message: str) -> None:
    st.title("HealthyMe access mapping unavailable")
    st.warning(
        "The native Supabase identity is active, but HealthyMe could not resolve an "
        "authorized Admin or Member role. This is not a logout."
    )
    st.code(BUILD)
    st.caption(message or "No active HealthyMe role mapping was returned.")
    _logout_button("h13q8_mapping_logout")
    st.stop()


st.set_page_config(
    page_title="HealthyMe H13Q8 Production Parity",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="collapsed",
)

provider = _secret("AUTH_BRIDGE_PROVIDER", SUPPORTED_PROVIDER).lower()
if provider != SUPPORTED_PROVIDER:
    st.error("AUTH_BRIDGE_PROVIDER must be 'supabaseoidc' for this deployment.")
    st.stop()

try:
    authorization_id = str(st.query_params.get("authorization_id") or "").strip()
except Exception:
    authorization_id = ""
if authorization_id:
    render_root_authorization_ui(authorization_id)

root_page = st.Page(_root_page, title="HealthyMe", icon="🌿", default=True)
login_page = st.Page(_login_page, title="Login", url_path="Login")
member_page = st.Page(_member_page, title="Member Home", url_path="Member_Home")
admin_page = st.Page(_admin_page, title="Admin Dashboard", url_path="Admin_Dashboard")

selected_page = st.navigation(
    [root_page, login_page, member_page, admin_page],
    position="hidden",
)
selected_path = str(selected_page.url_path or "")
ROUTER_CONTEXT["provider"] = provider
ROUTER_CONTEXT["selected_navigation_path"] = selected_path
ROUTER_CONTEXT["native_identity_present"] = _native_identity_present()

if not ROUTER_CONTEXT["native_identity_present"]:
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
    _show_role_resolution_failure("Neither the email nor subject claim is available.")

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
    _show_role_resolution_failure(lookup_message)

role = str(app_user.get("role") or "").strip().lower()
role_category = _role_category(role)
ROUTER_CONTEXT["role_category"] = role_category

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
            f"{type(exc).__name__}: Member compatibility context could not be built."
        )
    if selected_path != member_page.url_path:
        st.switch_page(member_page)
    selected_page.run()
    st.stop()

if role_category == "Admin":
    _clear_derived_application_context()
    if selected_path != admin_page.url_path:
        st.switch_page(admin_page)
    selected_page.run()
    st.stop()

_show_role_resolution_failure(f"Unsupported HealthyMe role: {role or 'blank'}")
