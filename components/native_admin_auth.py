from __future__ import annotations

from typing import Any

import streamlit as st

from components.admin_role_model import (
    apply_app_user_to_session,
    is_admin_role,
    is_member_role,
    resolve_app_user,
)


NATIVE_ADMIN_BUILD = "H13R1-native-admin-auth-v1"

_DERIVED_AUTH_CONTEXT_KEYS = {
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
    "is_member",
    "is_admin",
    "admin_logged_in",
    "_hm_expected_login_role",
    "_hm_access_recovery_message",
    "signed_out",
    "logout_requested",
    "logout_in_progress",
    "_hm_native_member_auth_active",
    "_hm_native_admin_auth_active",
}


def native_identity_present() -> bool:
    try:
        return bool(st.user and st.user.is_logged_in)
    except Exception:
        return False


def native_claim(name: str) -> str:
    try:
        value = st.user.get(name)
    except Exception:
        try:
            value = getattr(st.user, name, "")
        except Exception:
            value = ""
    return str(value or "").strip()


def clear_native_application_context() -> None:
    for key in _DERIVED_AUTH_CONTEXT_KEYS:
        st.session_state.pop(key, None)


def ensure_native_admin_context() -> tuple[bool, str]:
    """Resolve the current native identity to an active HealthyMe Admin."""
    if not native_identity_present():
        return False, "Native Streamlit identity is absent."

    email = native_claim("email").lower()
    subject = native_claim("sub")
    if not email and not subject:
        return False, "The native identity does not contain an email or subject claim."

    current_role = st.session_state.get("user_role") or st.session_state.get("role")
    current_email = str(
        st.session_state.get("oidc_email")
        or st.session_state.get("user_email")
        or ""
    ).strip().lower()
    if (
        st.session_state.get("logged_in")
        and st.session_state.get("_hm_auth_role_resolved")
        and is_admin_role(current_role)
        and (not email or current_email == email)
    ):
        st.session_state["_hm_native_admin_auth_active"] = True
        st.session_state["_hm_legacy_admin_auth_active"] = False
        st.session_state["_hm_native_admin_auth_build"] = NATIVE_ADMIN_BUILD
        return True, "Native Admin context already resolved."

    ok, app_user, message = resolve_app_user(
        email=email,
        auth_user_id=subject,
    )
    if not ok or not app_user:
        return False, message or "No active HealthyMe user mapping was returned."

    role = str(app_user.get("role") or "").strip().lower()
    if not is_admin_role(role):
        return False, f"The resolved HealthyMe role is {role or 'blank'}, not Admin."

    apply_app_user_to_session(
        app_user,
        email=email,
        auth_provider="supabase",
        auth_user_id=subject,
    )
    st.session_state["_hm_native_admin_auth_active"] = True
    st.session_state["_hm_legacy_admin_auth_active"] = False
    st.session_state["_hm_native_admin_auth_build"] = NATIVE_ADMIN_BUILD
    return True, message or "Native Admin context resolved."


def require_native_admin() -> None:
    """Admin page guard backed only by st.user and HealthyMe role resolution."""
    ok, message = ensure_native_admin_context()
    if not ok:
        st.error("Admin access could not be confirmed from the native Supabase identity.")
        st.caption(message)
        st.stop()

    st.session_state["is_admin"] = True
    st.session_state["admin_logged_in"] = True


def logout_native_identity() -> bool:
    """Clear derived HealthyMe state and end the native Streamlit OIDC session."""
    clear_native_application_context()
    try:
        st.logout()
    finally:
        st.stop()
    return True


def native_role_utility_bar(*args: Any, **kwargs: Any) -> None:
    role = st.session_state.get("user_role") or st.session_state.get("role")
    if is_admin_role(role):
        role_label = "Active admin"
    elif is_member_role(role):
        role_label = "Active member"
    else:
        role_label = "Active user"

    email = (
        st.session_state.get("user_email")
        or st.session_state.get("oidc_email")
        or native_claim("email")
        or "user"
    )
    identity_col, logout_col = st.columns([6.8, 1.1], gap="small")
    with identity_col:
        st.markdown(
            "<div class='utility-bar'><span class='utility-user'>Signed in as: "
            f"<b>{email}</b><span class='utility-role'>{role_label}</span>"
            "</span></div>",
            unsafe_allow_html=True,
        )
    with logout_col:
        if st.button(
            "Logout",
            key="h13r1_native_role_logout",
            use_container_width=True,
        ):
            logout_native_identity()


def _no_legacy_keepalive(*args: Any, **kwargs: Any) -> None:
    st.session_state["_hm_legacy_admin_keepalive_used"] = False
    return None


def install_native_admin_adapters() -> dict[str, Any]:
    """Install the Step 4 Admin adapter without broadening role permissions."""
    import components.auth_session as auth_session
    import components.guards as guards
    import components.ui_common as ui_common

    guards.require_admin = require_native_admin
    auth_session.logout_current_user = logout_native_identity
    ui_common.logout_current_user = logout_native_identity
    ui_common.utility_logout_bar = native_role_utility_bar

    keepalive_names: list[str] = []
    for name in dir(ui_common):
        if name.startswith("inject_keepalive"):
            setattr(ui_common, name, _no_legacy_keepalive)
            keepalive_names.append(name)

    st.session_state["_hm_legacy_admin_auth_active"] = False
    st.session_state["_hm_native_admin_auth_build"] = NATIVE_ADMIN_BUILD
    st.session_state["_hm_legacy_admin_keepalive_used"] = False

    return {
        "build": NATIVE_ADMIN_BUILD,
        "native_admin_guard_installed": guards.require_admin is require_native_admin,
        "native_logout_installed": (
            auth_session.logout_current_user is logout_native_identity
            and ui_common.logout_current_user is logout_native_identity
        ),
        "native_role_utility_bar_installed": (
            ui_common.utility_logout_bar is native_role_utility_bar
        ),
        "legacy_keepalive_functions_disabled": sorted(keepalive_names),
        "legacy_admin_auth_active": False,
        "auth0_restore_used": False,
        "durable_auth_session_used": False,
        "custom_browser_marker_used": False,
        "nutritionist_role_promoted_to_admin": False,
    }
