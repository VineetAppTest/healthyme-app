from __future__ import annotations

from typing import Any

import streamlit as st

from components.admin_role_model import (
    apply_app_user_to_session,
    is_member_role,
    resolve_app_user,
)


NATIVE_MEMBER_BUILD = "H13R0-native-member-auth-retirement-v1"

_MEMBER_UTILITY_CSS = """
<style id="hm-native-member-utility-v2">
div[data-testid="stElementContainer"]:has(style#hm-native-member-utility-v2),
div.element-container:has(style#hm-native-member-utility-v2){
  display:none!important;height:0!important;min-height:0!important;
  margin:0!important;padding:0!important;overflow:hidden!important;
}
.st-key-hm_native_member_utility_row{margin:0 0 .18rem!important;padding:0!important;}
.st-key-hm_native_member_utility_row div[data-testid="stHorizontalBlock"]{
  min-height:2.46rem!important;height:2.46rem!important;align-items:center!important;
  gap:.72rem!important;margin:0!important;padding:0!important;
}
.st-key-hm_native_member_utility_row :is(div[data-testid="stColumn"],div[data-testid="column"]){
  min-height:2.46rem!important;height:2.46rem!important;display:flex!important;
  align-items:center!important;margin:0!important;padding:0!important;
}
.st-key-hm_native_member_utility_row :is(div[data-testid="stColumn"],div[data-testid="column"])>div[data-testid="stVerticalBlock"]{
  width:100%!important;min-height:2.46rem!important;height:2.46rem!important;
  display:flex!important;flex-direction:column!important;justify-content:center!important;
  gap:0!important;margin:0!important;padding:0!important;
}
.st-key-hm_native_member_utility_row .utility-bar{
  width:100%!important;min-height:2.46rem!important;height:2.46rem!important;
  display:flex!important;align-items:center!important;box-sizing:border-box!important;
  margin:0!important;
}
.st-key-hm_native_member_profile [data-testid="stButton"]>button{
  width:2.34rem!important;min-width:2.34rem!important;max-width:2.34rem!important;
  height:2.34rem!important;min-height:2.34rem!important;max-height:2.34rem!important;
  border-radius:999px!important;padding:0!important;margin:0 auto!important;
  display:flex!important;align-items:center!important;justify-content:center!important;
}
.st-key-hm_native_member_logout [data-testid="stButton"]>button{
  min-height:2.46rem!important;height:2.46rem!important;max-height:2.46rem!important;
  margin:0!important;display:flex!important;align-items:center!important;justify-content:center!important;
}
@media(max-width:760px){
  .st-key-hm_native_member_utility_row div[data-testid="stHorizontalBlock"]{
    display:grid!important;grid-template-columns:minmax(0,1fr) 2.55rem 4.65rem!important;
    gap:.30rem!important;
  }
  .st-key-hm_native_member_utility_row .utility-user{
    min-width:0!important;overflow:hidden!important;text-overflow:ellipsis!important;
    white-space:nowrap!important;
  }
}
</style>
"""

_DERIVED_MEMBER_CONTEXT_KEYS = {
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
    "_hm_legacy_supabase_marker_detected",
    "_hm_member_restore_retry",
    "signed_out",
    "logout_requested",
    "logout_in_progress",
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


def _clear_member_context() -> None:
    for key in _DERIVED_MEMBER_CONTEXT_KEYS:
        st.session_state.pop(key, None)


def ensure_native_member_context() -> tuple[bool, str]:
    """Resolve the current native Streamlit identity to an active HealthyMe Member."""
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
        and is_member_role(current_role)
        and (not email or current_email == email)
    ):
        st.session_state["_hm_native_member_auth_active"] = True
        st.session_state["_hm_legacy_member_auth_retired"] = True
        st.session_state["_hm_native_member_auth_build"] = NATIVE_MEMBER_BUILD
        return True, "Native Member context already resolved."

    ok, app_user, message = resolve_app_user(
        email=email,
        auth_user_id=subject,
    )
    if not ok or not app_user:
        return False, message or "No active HealthyMe user mapping was returned."

    role = str(app_user.get("role") or "").strip().lower()
    if not is_member_role(role):
        return False, f"The resolved HealthyMe role is {role or 'blank'}, not Member."

    apply_app_user_to_session(
        app_user,
        email=email,
        auth_provider="supabase",
        auth_user_id=subject,
    )
    st.session_state["_hm_native_member_auth_active"] = True
    st.session_state["_hm_legacy_member_auth_retired"] = True
    st.session_state["_hm_native_member_auth_build"] = NATIVE_MEMBER_BUILD
    return True, message or "Native Member context resolved."


def require_native_member() -> None:
    """Member page guard backed only by st.user and HealthyMe role resolution."""
    ok, message = ensure_native_member_context()
    if not ok:
        st.error("Member access could not be confirmed from the native Supabase identity.")
        st.caption(message)
        st.stop()

    # Preserve the non-authentication page helpers that historically lived inside
    # guards.require_member, without invoking password-session restoration.
    try:
        import components.guards as guards

        current_page = guards._current_page_filename()
        guards._redirect_disabled_reference_page(current_page)
        guards._apply_member_page_defaults(current_page)
        guards._apply_member_feature_visibility(current_page)
        guards._apply_daily_log_ui_and_autosave(current_page)
    except Exception:
        # Authentication must not fail because an optional UI helper is unavailable.
        pass


def logout_native_member() -> bool:
    """Clear derived application state and end the native Streamlit OIDC session."""
    _clear_member_context()
    st.session_state["_hm_legacy_member_auth_retired"] = True
    try:
        st.logout()
    finally:
        st.stop()
    return True


def native_member_utility_bar(*args: Any, **kwargs: Any) -> None:
    email = (
        st.session_state.get("user_email")
        or st.session_state.get("oidc_email")
        or native_claim("email")
        or "member"
    )
    st.markdown(_MEMBER_UTILITY_CSS, unsafe_allow_html=True)
    with st.container(key="hm_native_member_utility_row"):
        identity_col, profile_col, logout_col = st.columns(
            [6.65, 0.42, 1.0],
            gap="small",
            vertical_alignment="center",
        )
        with identity_col:
            st.markdown(
                "<div class='utility-bar'><span class='utility-user'>Signed in as: "
                f"<b>{email}</b><span class='utility-role'>Active member</span>"
                "</span></div>",
                unsafe_allow_html=True,
            )
        with profile_col:
            with st.container(
                key="hm_native_member_profile",
                horizontal=True,
                horizontal_alignment="center",
                vertical_alignment="center",
            ):
                if st.button(
                    "👤",
                    key="h13r0_native_member_profile",
                    use_container_width=True,
                    help="My Profile",
                ):
                    st.switch_page("pages/07_My_Profile.py")
        with logout_col:
            with st.container(
                key="hm_native_member_logout",
                horizontal=True,
                horizontal_alignment="center",
                vertical_alignment="center",
            ):
                if st.button(
                    "Logout",
                    key="h13r0_native_member_logout",
                    use_container_width=True,
                ):
                    logout_native_member()


def _no_legacy_keepalive(*args: Any, **kwargs: Any) -> None:
    st.session_state["_hm_legacy_member_keepalive_used"] = False
    return None


def install_native_member_adapters() -> dict[str, Any]:
    """Install one permanent Member-only adapter layer for the Step 3 runtime.

    Admin/Auth0 functions remain in source for Step 4 and rollback, but the Member
    runtime no longer calls the password restore, durable session, custom marker,
    legacy page guard, keepalive, or legacy logout paths.
    """
    import components.auth_session as auth_session
    import components.guards as guards
    import components.ui_common as ui_common

    guards.require_member = require_native_member
    auth_session.logout_current_user = logout_native_member
    ui_common.logout_current_user = logout_native_member
    ui_common.utility_logout_bar = native_member_utility_bar

    keepalive_names: list[str] = []
    for name in dir(ui_common):
        if name.startswith("inject_keepalive"):
            setattr(ui_common, name, _no_legacy_keepalive)
            keepalive_names.append(name)

    st.session_state["_hm_native_member_auth_active"] = True
    st.session_state["_hm_legacy_member_auth_retired"] = True
    st.session_state["_hm_native_member_auth_build"] = NATIVE_MEMBER_BUILD
    st.session_state["_hm_legacy_member_keepalive_used"] = False

    return {
        "build": NATIVE_MEMBER_BUILD,
        "native_member_guard_installed": guards.require_member is require_native_member,
        "native_member_logout_installed": (
            auth_session.logout_current_user is logout_native_member
            and ui_common.logout_current_user is logout_native_member
        ),
        "native_member_utility_bar_installed": (
            ui_common.utility_logout_bar is native_member_utility_bar
        ),
        "legacy_keepalive_functions_disabled": sorted(keepalive_names),
        "member_password_restore_used": False,
        "durable_auth_session_used": False,
        "custom_browser_marker_used": False,
    }
