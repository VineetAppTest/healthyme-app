import streamlit as st
from components.db import find_user_by_email
from components.normalized_store import find_user_by_email_fast


SECURE_LOGOUT_MESSAGE_KEY = "_hm_secure_logout_feedback"
SECURE_LOGOUT_SUCCESS_MESSAGE = "Complete secure logout successful. Please open a fresh login session before switching users."
SECURE_LOGOUT_WARNING_MESSAGE = "Complete secure logout could not be fully confirmed. Please close this browser/incognito window before switching users."


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
    ok, fast_user, _ = find_user_by_email_fast(email)
    app_user = fast_user if ok and fast_user else None
    if not app_user:
        app_user = find_user_by_email(email)
    return app_user


def _apply_user_to_session(app_user, email, auth_method="auth0"):
    st.session_state["logged_in"] = True
    st.session_state["user_id"] = app_user["id"]
    st.session_state["user_role"] = app_user["role"]
    st.session_state["user_name"] = app_user.get("name") or get_oidc_name()
    st.session_state["must_reset_password"] = False
    st.session_state["oidc_email"] = email
    st.session_state["auth_login_method"] = auth_method
    st.session_state["auth_provider"] = "oidc" if auth_method == "auth0" else auth_method
    st.session_state["_hm_auth_role_resolved"] = True
    return True


def restore_login_from_token():
    if st.session_state.get("signed_out") or st.session_state.get("logout_requested"):
        return False
    if not oidc_is_logged_in():
        return False
    email = get_oidc_email()
    if (
        st.session_state.get("logged_in")
        and st.session_state.get("_hm_auth_role_resolved")
        and st.session_state.get("oidc_email") == email
    ):
        return True
    app_user = _resolve_app_user_by_email(email)
    if not app_user:
        st.session_state["logged_in"] = False
        st.session_state["auth_error"] = f"{email or 'This email'} is authenticated but not authorized in HealthyMe."
        return False
    return _apply_user_to_session(app_user, email, auth_method="auth0")


def login_with_supabase_password(email, password):
    from components.supabase_auth_session import sign_in_with_supabase
    ok, message = sign_in_with_supabase(email, password)
    if not ok:
        st.session_state["logged_in"] = False
        st.session_state["auth_error"] = message
        return False
    return True


def _set_secure_logout_feedback(level="success", message=SECURE_LOGOUT_SUCCESS_MESSAGE):
    st.session_state[SECURE_LOGOUT_MESSAGE_KEY] = {
        "level": level,
        "message": message,
    }


def pop_secure_logout_feedback():
    feedback = st.session_state.pop(SECURE_LOGOUT_MESSAGE_KEY, None)
    if isinstance(feedback, dict):
        return feedback
    return None


def clear_app_session_for_logout(feedback_level="success", feedback_message=SECURE_LOGOUT_SUCCESS_MESSAGE):
    for k in list(st.session_state.keys()):
        try:
            del st.session_state[k]
        except Exception:
            pass
    st.session_state["signed_out"] = True
    st.session_state["logout_requested"] = True
    _set_secure_logout_feedback(feedback_level, feedback_message)


def _clear_supabase_pilot_session_for_logout() -> bool:
    try:
        from components.supabase_auth_session import clear_supabase_auth_session

        return bool(clear_supabase_auth_session())
    except Exception:
        return False


def logout_current_user():
    provider = st.session_state.get("auth_provider")
    login_method = st.session_state.get("auth_login_method")
    had_oidc_session = oidc_is_logged_in()
    had_supabase_session = provider == "supabase" or login_method == "supabase"
    supabase_cleared = _clear_supabase_pilot_session_for_logout()
    logout_warning = not supabase_cleared

    if had_supabase_session:
        clear_app_session_for_logout(
            feedback_level="warning" if logout_warning else "success",
            feedback_message=SECURE_LOGOUT_WARNING_MESSAGE if logout_warning else SECURE_LOGOUT_SUCCESS_MESSAGE,
        )
        return

    clear_app_session_for_logout(
        feedback_level="warning" if logout_warning else "success",
        feedback_message=SECURE_LOGOUT_WARNING_MESSAGE if logout_warning else SECURE_LOGOUT_SUCCESS_MESSAGE,
    )
    if had_oidc_session:
        try:
            st.logout()
        except Exception:
            clear_app_session_for_logout(
                feedback_level="warning",
                feedback_message=SECURE_LOGOUT_WARNING_MESSAGE,
            )
