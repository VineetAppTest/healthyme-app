import os
from typing import Tuple

import streamlit as st

from components.db import find_user_by_email
from components.normalized_store import find_user_by_email_fast


SUPABASE_SESSION_KEY = "_hm_supabase_auth_session"


def _setting(name: str, default: str = "") -> str:
    value = os.environ.get(name)
    if value:
        return value
    try:
        value = st.secrets.get(name, default)
        return str(value) if value is not None else default
    except Exception:
        return default


def supabase_auth_configured() -> bool:
    return bool(_setting("SUPABASE_URL") and _setting("SUPABASE_ANON_KEY"))


def _client():
    from supabase import create_client

    return create_client(_setting("SUPABASE_URL"), _setting("SUPABASE_ANON_KEY"))


def _apply_supabase_user_to_session(app_user: dict, email: str) -> bool:
    clean_email = (email or "").strip().lower()
    st.session_state["logged_in"] = True
    st.session_state["user_id"] = app_user["id"]
    st.session_state["user_role"] = app_user["role"]
    st.session_state["user_name"] = app_user.get("name") or clean_email or "User"
    st.session_state["must_reset_password"] = False
    st.session_state["oidc_email"] = clean_email
    st.session_state["supabase_auth_email"] = clean_email
    st.session_state["auth_provider"] = "supabase"
    st.session_state["_hm_auth_role_resolved"] = True
    return True


def _find_authorized_user(email: str):
    clean_email = (email or "").strip().lower()
    if not clean_email:
        return None

    ok, fast_user, _ = find_user_by_email_fast(clean_email)
    app_user = fast_user if ok and fast_user else None
    if not app_user:
        app_user = find_user_by_email(clean_email)
    return app_user


def restore_supabase_login_from_session() -> bool:
    if st.session_state.get("signed_out") or st.session_state.get("logout_requested"):
        return False

    if st.session_state.get("auth_provider") != "supabase":
        return False

    email = (st.session_state.get("supabase_auth_email") or "").strip().lower()
    if not email:
        return False

    if (
        st.session_state.get("logged_in")
        and st.session_state.get("_hm_auth_role_resolved")
        and st.session_state.get("supabase_auth_email") == email
    ):
        return True

    app_user = _find_authorized_user(email)
    if not app_user:
        st.session_state["logged_in"] = False
        st.session_state["auth_error"] = f"{email or 'This email'} is authenticated but not authorized in HealthyMe."
        return False

    return _apply_supabase_user_to_session(app_user, email)


def sign_in_with_supabase(email: str, password: str) -> Tuple[bool, str]:
    clean_email = (email or "").strip().lower()
    clean_password = password or ""

    if not supabase_auth_configured():
        return False, "Supabase Auth is not configured for this Streamlit app yet."

    if not clean_email or not clean_password:
        return False, "Please enter both email and password."

    try:
        auth_response = _client().auth.sign_in_with_password({"email": clean_email, "password": clean_password})
        auth_email = (
            getattr(getattr(auth_response, "user", None), "email", None)
            or getattr(getattr(getattr(auth_response, "session", None), "user", None), "email", None)
            or clean_email
        )
        clean_auth_email = (auth_email or "").strip().lower()

        app_user = _find_authorized_user(clean_auth_email)
        if not app_user:
            st.session_state["auth_error"] = f"{clean_auth_email or 'This email'} is authenticated but not authorized in HealthyMe."
            return False, st.session_state["auth_error"]

        st.session_state[SUPABASE_SESSION_KEY] = True
        _apply_supabase_user_to_session(app_user, clean_auth_email)
        return True, "Signed in with Supabase Auth."
    except Exception as exc:
        return False, f"Supabase login failed: {exc}"


def clear_supabase_auth_session() -> None:
    for key in [SUPABASE_SESSION_KEY, "supabase_auth_email"]:
        st.session_state.pop(key, None)
