import streamlit as st

from components.admin_role_model import apply_app_user_to_session, resolve_app_user
from components.auth_mode import supabase_oidc_poc_enabled


SECURE_LOGOUT_MESSAGE_KEY = "_hm_secure_logout_feedback"
SECURE_LOGOUT_SUCCESS_MESSAGE = "You have been signed out securely."
SECURE_LOGOUT_WARNING_MESSAGE = (
    "Your HealthyMe session was cleared, but Supabase could not confirm remote sign-out. "
    "Please close this browser tab before switching users."
)

RECOVERY_SESSION_KEYS = (
    "_hm_expected_login_role",
    "_hm_access_recovery_message",
    "_hm_legacy_supabase_marker_detected",
    "_hm_member_restore_retry",
)


def _clear_recovery_flags():
    for key in RECOVERY_SESSION_KEYS:
        st.session_state.pop(key, None)


def oidc_is_logged_in():
    try:
        return bool(st.user and st.user.is_logged_in)
    except Exception:
        return False


def get_oidc_email():
    try:
        return (st.user.get("email") or "").strip().lower()
    except Exception:
        try:
            return (getattr(st.user, "email", "") or "").strip().lower()
        except Exception:
            return ""


def get_oidc_subject():
    try:
        return str(st.user.get("sub") or "").strip()
    except Exception:
        try:
            return str(getattr(st.user, "sub", "") or "").strip()
        except Exception:
            return ""


def get_oidc_name():
    for key in ["name", "given_name", "nickname"]:
        try:
            value = st.user.get(key)
            if value:
                return str(value)
        except Exception:
            pass
        try:
            value = getattr(st.user, key, "")
            if value:
                return str(value)
        except Exception:
            pass
    return get_oidc_email() or "User"


def _resolve_app_user_by_email(email):
    ok, app_user, _ = resolve_app_user(email=email)
    return app_user if ok else None


def _apply_user_to_session(
    app_user,
    email,
    auth_method="auth0",
    auth_user_id="",
):
    ok = apply_app_user_to_session(
        app_user,
        email=email,
        auth_provider=auth_method,
        auth_user_id=auth_user_id,
    )
    if ok:
        _clear_recovery_flags()
    return ok


def restore_login_from_token():
    if st.session_state.get("signed_out") or st.session_state.get("logout_requested"):
        return False
    if not oidc_is_logged_in():
        return False

    email = get_oidc_email()
    subject = get_oidc_subject()
    auth_method = "supabase_oidc" if supabase_oidc_poc_enabled() else "auth0"

    if (
        st.session_state.get("logged_in")
        and st.session_state.get("_hm_auth_role_resolved")
        and st.session_state.get("oidc_email") == email
    ):
        _clear_recovery_flags()
        return True

    ok, app_user, message = resolve_app_user(
        email=email,
        auth_user_id=subject if supabase_oidc_poc_enabled() else "",
    )
    if not ok or not app_user:
        st.session_state["logged_in"] = False
        st.session_state["auth_error"] = (
            f"{email or 'This email'} is authenticated but not authorized in HealthyMe. {message}"
        )
        return False
    return _apply_user_to_session(
        app_user,
        email,
        auth_method=auth_method,
        auth_user_id=subject,
    )


def login_with_supabase_password(email, password):
    from components.supabase_auth_session import sign_in_with_supabase

    st.session_state.pop("auth_error", None)
    ok, message = sign_in_with_supabase(email, password)
    if not ok:
        st.session_state["logged_in"] = False
        st.session_state["auth_error"] = message
        return False
    _clear_recovery_flags()
    return True


def _set_secure_logout_feedback(
    level="success",
    message=SECURE_LOGOUT_SUCCESS_MESSAGE,
):
    st.session_state[SECURE_LOGOUT_MESSAGE_KEY] = {
        "level": level,
        "message": message,
    }


def pop_secure_logout_feedback():
    feedback = st.session_state.pop(SECURE_LOGOUT_MESSAGE_KEY, None)
    if isinstance(feedback, dict):
        return feedback
    return None


def clear_app_session_for_logout(
    feedback_level="success",
    feedback_message=SECURE_LOGOUT_SUCCESS_MESSAGE,
):
    for key in list(st.session_state.keys()):
        try:
            del st.session_state[key]
        except Exception:
            pass
    st.session_state["signed_out"] = True
    st.session_state["logout_requested"] = True
    _set_secure_logout_feedback(feedback_level, feedback_message)


def logout_current_user():
    provider = st.session_state.get("auth_provider")
    login_method = st.session_state.get("auth_login_method")
    had_oidc_session = oidc_is_logged_in()

    if provider == "supabase" or login_method == "supabase":
        remote_logout_ok = True
        try:
            from components.supabase_auth_session import clear_supabase_auth_session

            remote_logout_ok = bool(clear_supabase_auth_session())
        except Exception:
            remote_logout_ok = False

        clear_app_session_for_logout(
            feedback_level="success" if remote_logout_ok else "warning",
            feedback_message=(
                SECURE_LOGOUT_SUCCESS_MESSAGE
                if remote_logout_ok
                else SECURE_LOGOUT_WARNING_MESSAGE
            ),
        )
        return remote_logout_ok

    clear_app_session_for_logout()
    if had_oidc_session:
        try:
            st.logout()
        except Exception:
            clear_app_session_for_logout(
                feedback_level="warning",
                feedback_message=(
                    "Your HealthyMe session was cleared, but the browser identity "
                    "session could not be fully confirmed. Please close this browser tab."
                ),
            )
            return False
    return True
