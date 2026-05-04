import streamlit as st
from components.db import find_user_by_email

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

def restore_login_from_token():
    """Compatibility name retained, but now uses Streamlit OIDC identity.

    No URL token.
    No custom cookie token.
    No app-created browser session token.
    """
    if not oidc_is_logged_in():
        return False

    email = get_oidc_email()
    app_user = find_user_by_email(email)

    if not app_user:
        st.session_state["logged_in"] = False
        st.session_state["auth_error"] = f"{email or 'This email'} is authenticated but not authorized in HealthyMe."
        return False

    st.session_state["logged_in"] = True
    st.session_state["user_id"] = app_user["id"]
    st.session_state["user_role"] = app_user["role"]
    st.session_state["user_name"] = app_user.get("name") or get_oidc_name()
    st.session_state["must_reset_password"] = False
    st.session_state["oidc_email"] = email
    return True

def logout_current_user():
    for k in list(st.session_state.keys()):
        del st.session_state[k]
    st.logout()