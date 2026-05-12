import streamlit as st
from components.db import find_user_by_email
from components.normalized_store import find_user_by_email_fast

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

def _apply_user_to_session(app_user, email):
    st.session_state["logged_in"] = True
    st.session_state["user_id"] = app_user["id"]
    st.session_state["user_role"] = app_user["role"]
    st.session_state["user_name"] = app_user.get("name") or get_oidc_name()
    st.session_state["must_reset_password"] = False
    st.session_state["oidc_email"] = email
    st.session_state["_hm_auth_role_resolved"] = True
    return True

def restore_login_from_token():
    """Compatibility name retained, but now uses Streamlit OIDC identity.

    Speed improvement:
    - If role was already resolved in this Streamlit session, do not query DB again.
    - On first Auth0 callback, try fast hm_users lookup first.
    - Fallback to legacy JSONB lookup only if normalized lookup is unavailable.
    """
    if not oidc_is_logged_in():
        return False

    email = get_oidc_email()

    if (
        st.session_state.get("logged_in")
        and st.session_state.get("_hm_auth_role_resolved")
        and st.session_state.get("oidc_email") == email
    ):
        return True

    ok, fast_user, fast_msg = find_user_by_email_fast(email)
    app_user = fast_user if ok and fast_user else None

    if not app_user:
        # Fallback for cases where normalized tables are not migrated yet.
        app_user = find_user_by_email(email)

    if not app_user:
        st.session_state["logged_in"] = False
        st.session_state["auth_error"] = f"{email or 'This email'} is authenticated but not authorized in HealthyMe."
        return False

    return _apply_user_to_session(app_user, email)

def logout_current_user():
    """Logout through Streamlit native OIDC.

    Streamlit removes the identity cookie and starts a new session.
    """
    st.logout()