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
    is_admin_role,
    is_member_role,
    resolve_app_user,
)


BUILD = "H13Q4-native-role-protected-routing-gate2-v3.1-route-stability"
SUPPORTED_PROVIDER = "supabaseoidc"
ROUTER_CONTEXT: dict[str, Any] = {}


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
            if not name.startswith(prefix):
                continue
            suffix = name[len(prefix):]
            if suffix.isdigit():
                count += 1
        return count

    identity_piece_count = piece_count("_streamlit_user")
    token_piece_count = piece_count("_streamlit_user_tokens")
    return {
        "native_identity_cookie_present": identity_piece_count > 0,
        "native_identity_cookie_piece_count": identity_piece_count,
        "native_tokens_cookie_present": token_piece_count > 0,
        "native_tokens_cookie_piece_count": token_piece_count,
        "cookie_values_displayed": False,
    }


def _role_category(role: str) -> str:
    if is_admin_role(role):
        return "Admin"
    if is_member_role(role):
        return "Member"
    return "Unsupported"


def _base_snapshot(*, route_name: str, route_allowed: bool) -> dict[str, Any]:
    context = ROUTER_CONTEXT
    return {
        "build": BUILD,
        "configured_provider": context.get("provider", SUPPORTED_PROVIDER),
        "native_identity_present": bool(context.get("native_identity_present")),
        "email_claim_present": bool(context.get("email_claim_present")),
        "subject_claim_present": bool(context.get("subject_claim_present")),
        "healthyme_role_lookup_used": bool(context.get("role_lookup_used")),
        "healthyme_role_resolved": bool(context.get("role_resolved")),
        "resolved_role_category": context.get("role_category", "None"),
        "selected_route": route_name,
        "selected_navigation_path": context.get("selected_navigation_path", ""),
        "protected_page_routing_used": True,
        "route_allowed_for_role": route_allowed,
        "central_router_executed_first": True,
        "authorization_ui_separate_app": True,
        "oauth_consent_route_registered": False,
        "application_session_state_required": False,
        "custom_browser_marker_used": False,
        "durable_auth_session_used": False,
        "legacy_page_guard_used": False,
        "local_storage_used": False,
        **_safe_cookie_snapshot(),
    }


def _logout_button(key: str) -> None:
    if st.button("Logout", key=key, use_container_width=True):
        st.logout()
        st.stop()


def _root_page() -> None:
    st.empty()


def _login_page() -> None:
    st.title("HealthyMe native role router")
    st.caption(
        "Gate 2 v3 keeps the Supabase authorization UI in a separate app. This app "
        "owns only native Streamlit identity, HealthyMe role lookup and protected routing."
    )
    st.code(BUILD)
    st.metric("Native Streamlit identity", "Absent")
    st.code(
        json.dumps(
            {
                "build": BUILD,
                "configured_provider": ROUTER_CONTEXT.get("provider", SUPPORTED_PROVIDER),
                "native_identity_present": False,
                "healthyme_role_lookup_used": False,
                "healthyme_role_resolved": False,
                "selected_navigation_path": ROUTER_CONTEXT.get("selected_navigation_path", ""),
                "protected_page_routing_used": True,
                "central_router_executed_first": True,
                "authorization_ui_separate_app": True,
                "oauth_consent_route_registered": False,
                "application_session_state_required": False,
                "custom_browser_marker_used": False,
                "durable_auth_session_used": False,
                "legacy_page_guard_used": False,
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


def _admin_page() -> None:
    role_category = ROUTER_CONTEXT.get("role_category")
    route_allowed = role_category == "Admin"

    st.title("Admin Dashboard — Gate 2 protected route")
    if route_allowed:
        st.success(
            "Native identity was restored, HealthyMe resolved the Admin role, and the "
            "central router allowed this protected route."
        )
    else:
        st.error("The central router allowed an invalid Admin-route state.")
    st.caption(
        "This is intentionally not the real Admin Dashboard. No legacy page guard, "
        "navigation shell, dashboard data or application Session State is used."
    )
    st.code(BUILD)
    st.code(
        json.dumps(
            _base_snapshot(
                route_name="/Admin_Dashboard",
                route_allowed=route_allowed,
            ),
            indent=2,
            sort_keys=True,
        ),
        language="json",
    )
    _logout_button("h13q4_admin_logout")


def _member_page() -> None:
    role_category = ROUTER_CONTEXT.get("role_category")
    route_allowed = role_category == "Member"

    st.title("Member Home — Gate 2 protected route")
    if route_allowed:
        st.success(
            "Native identity was restored, HealthyMe resolved the Member role, and the "
            "central router allowed this protected route."
        )
    else:
        st.error("The central router allowed an invalid Member-route state.")
    st.caption(
        "This is intentionally not the real Member Home. No legacy page guard, member "
        "defaults, feature visibility code or application Session State is used."
    )
    st.code(BUILD)
    st.code(
        json.dumps(
            _base_snapshot(
                route_name="/Member_Home",
                route_allowed=route_allowed,
            ),
            indent=2,
            sort_keys=True,
        ),
        language="json",
    )
    _logout_button("h13q4_member_logout")


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
                "build": BUILD,
                "native_identity_present": True,
                "email_claim_present": bool(ROUTER_CONTEXT.get("email_claim_present")),
                "subject_claim_present": bool(ROUTER_CONTEXT.get("subject_claim_present")),
                "healthyme_role_lookup_used": True,
                "healthyme_role_resolved": False,
                "role_lookup_completed": bool(role_lookup_ok),
                "selected_navigation_path": ROUTER_CONTEXT.get("selected_navigation_path", ""),
                "protected_page_routing_used": True,
                "central_router_executed_first": True,
                "authorization_ui_separate_app": True,
                "oauth_consent_route_registered": False,
                "application_session_state_required": False,
                "custom_browser_marker_used": False,
                "durable_auth_session_used": False,
                "legacy_page_guard_used": False,
                "local_storage_used": False,
                **_safe_cookie_snapshot(),
            },
            indent=2,
            sort_keys=True,
        ),
        language="json",
    )
    st.caption(lookup_message or "No active HealthyMe role mapping was returned.")
    _logout_button("h13q4_mapping_logout")
    st.stop()


st.set_page_config(
    page_title="HealthyMe Native Role Router",
    page_icon="🌿",
    layout="centered",
    initial_sidebar_state="collapsed",
)

provider = _secret("AUTH_BRIDGE_PROVIDER", SUPPORTED_PROVIDER).lower()
if provider != SUPPORTED_PROVIDER:
    st.error("AUTH_BRIDGE_PROVIDER must be 'supabaseoidc' for this Gate 2 deployment.")
    st.stop()

root_page = st.Page(
    _root_page,
    title="HealthyMe",
    icon="🌿",
    default=True,
)
login_page = st.Page(
    _login_page,
    title="Login",
    url_path="Login",
)
admin_page = st.Page(
    _admin_page,
    title="Admin Dashboard",
    url_path="Admin_Dashboard",
)
member_page = st.Page(
    _member_page,
    title="Member Home",
    url_path="Member_Home",
)

selected_page = st.navigation(
    [root_page, login_page, admin_page, member_page],
    position="hidden",
)
selected_path = str(selected_page.url_path or "")
ROUTER_CONTEXT["provider"] = provider
ROUTER_CONTEXT["selected_navigation_path"] = selected_path
native_identity_present = _native_identity_present()
ROUTER_CONTEXT["native_identity_present"] = native_identity_present

if not native_identity_present:
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
    if selected_path != admin_page.url_path:
        st.switch_page(admin_page)
    selected_page.run()
    st.stop()

if role_category == "Member":
    if selected_path != member_page.url_path:
        st.switch_page(member_page)
    selected_page.run()
    st.stop()

_show_role_resolution_failure(
    role_lookup_ok=True,
    lookup_message="The mapped role is outside the Gate 2 Admin/Member boundary.",
)
