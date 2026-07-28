from __future__ import annotations

from typing import Any

import streamlit as st

from components.admin_role_model import (
    apply_app_user_to_session,
    normalize_role,
    resolve_app_user,
)
from components.native_admin_auth import (
    logout_native_identity,
    native_claim,
    native_identity_present,
)


PROFILE_BUILDER_EDIT_ROLES = {"admin", "super_admin", "nutritionist"}
PROFILE_BUILDER_PUBLISH_ROLES = {"admin", "super_admin"}


def current_profile_builder_role() -> str:
    return normalize_role(
        st.session_state.get("user_role") or st.session_state.get("role")
    )


def current_profile_builder_user_can_publish() -> bool:
    return current_profile_builder_role() in PROFILE_BUILDER_PUBLISH_ROLES


def ensure_profile_builder_access() -> tuple[bool, str]:
    """Resolve a native identity to a role allowed on Profile Builder only.

    This does not broaden the general Admin guard. Nutritionists receive access to
    this one workflow while all other Admin routes remain protected by the existing
    Admin/Super Admin policy.
    """
    if not native_identity_present():
        return False, "Native Streamlit identity is absent."

    email = native_claim("email").lower()
    subject = native_claim("sub")
    current_role = current_profile_builder_role()
    current_email = str(
        st.session_state.get("oidc_email")
        or st.session_state.get("user_email")
        or ""
    ).strip().lower()

    if (
        st.session_state.get("logged_in")
        and st.session_state.get("_hm_auth_role_resolved")
        and current_role in PROFILE_BUILDER_EDIT_ROLES
        and (not email or current_email == email)
    ):
        st.session_state["_hm_profile_builder_access_active"] = True
        return True, "Profile Builder access already resolved."

    ok, app_user, message = resolve_app_user(
        email=email,
        auth_user_id=subject,
    )
    if not ok or not app_user:
        return False, message or "No active HealthyMe user mapping was returned."

    role = normalize_role(app_user.get("role"))
    if role not in PROFILE_BUILDER_EDIT_ROLES:
        return False, f"The resolved HealthyMe role is {role or 'blank'}, which cannot access Profile Builder."

    apply_app_user_to_session(
        app_user,
        email=email,
        auth_provider="supabase",
        auth_user_id=subject,
    )
    st.session_state["_hm_profile_builder_access_active"] = True
    st.session_state["_hm_profile_builder_publish_allowed"] = (
        role in PROFILE_BUILDER_PUBLISH_ROLES
    )
    return True, message or "Profile Builder access resolved."


def require_profile_builder_access() -> None:
    ok, message = ensure_profile_builder_access()
    if ok:
        return
    st.error("Recommendation Profile Builder access could not be confirmed.")
    st.caption(message)
    st.stop()


def profile_builder_role_utility_bar(*args: Any, **kwargs: Any) -> None:
    role = current_profile_builder_role()
    role_label = {
        "admin": "Active admin",
        "super_admin": "Active super admin",
        "nutritionist": "Active nutritionist",
    }.get(role, "Active user")
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
            key="hm_profile_builder_role_logout",
            use_container_width=True,
        ):
            logout_native_identity()
