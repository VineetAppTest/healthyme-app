import streamlit as st
from components.db import find_user_by_email
from components.normalized_store import find_user_by_email_fast
from components.supabase_auth_session import sign_in_with_supabase_password


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
    ok, fast_user, fast_msg = find_user_by_email_fast(email)
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
    st.session_state["_hm_auth_role_resolved"] = True
    return True


def restore_login_from_token():
    """Compatibility name retained, but now uses Streamlit OIDC identity."""
    # v49: after logout, do not auto-restore in the same app session.
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
    """Supabase Auth pilot login path for AUTH_MODE=dual/supabase.

    This validates the Supabase Auth identity, then reuses the existing HealthyMe
    app authorization check by email. It does not create users and does not change
    workflow/state.
    """
    ok, resolved_email, message = sign_in_with_supabase_password(email, password)
    if not ok:
        st.session_state["logged_in"] = False
        st.session_state["auth_error"] = message
        return False

    app_user = _resolve_app_user_by_email(resolved_email)
    if not app_user:
        st.session_state["logged_in"] = False
        st.session_state["auth_error"] = f"{resolved_email or 'This email'} is authenticated by Supabase but not authorized in HealthyMe."
        return False

    st.session_state.pop("signed_out", None)
    st.session_state.pop("logout_requested", None)
    st.session_state.pop("auth_error", None)
    return _apply_user_to_session(app_user, resolved_email, auth_method="supabase")


def clear_app_session_for_logout():
    """Clear HealthyMe app-level session keys before logout."""
    for k in list(st.session_state.keys()):
        try:
            del st.session_state[k]
        except Exception:
            pass
    st.session_state["signed_out"] = True
    st.session_state["logout_requested"] = True


def logout_current_user():
    """Clear app session and call native Streamlit/OIDC logout when needed.

    Do not call st.rerun() or st.switch_page() after this function.
    """
    had_oidc_session = oidc_is_logged_in()
    clear_app_session_for_logout()
    if had_oidc_session:
        st.logout()
