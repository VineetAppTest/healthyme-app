import os
from typing import Tuple

import streamlit as st

from components.admin_role_model import apply_app_user_to_session, resolve_app_user


SUPABASE_SESSION_KEY = "_hm_supabase_auth_session"


def _get_secret(name: str, default: str = "") -> str:
    value = os.environ.get(name)
    if value:
        return value
    try:
        value = st.secrets.get(name, default)
        return str(value) if value is not None else default
    except Exception:
        return default




ROLE_SESSION_KEYS = [
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
    "is_admin",
    "admin_logged_in",
    "is_member",
    "auth_error",
]


def clear_stale_app_identity_before_supabase_login() -> None:
    """Remove stale Auth0/admin/member role state before a Supabase pilot login.

    Streamlit keeps session_state across page navigation. During dual-mode testing,
    an Auth0 admin session and a Supabase member pilot login can otherwise overlap
    in the same browser session. Clearing app identity first makes direct admin
    page guards rely only on the fresh Supabase role resolution.
    """
    for key in ROLE_SESSION_KEYS:
        st.session_state.pop(key, None)
    st.session_state.pop("signed_out", None)
    st.session_state.pop("logout_requested", None)

def supabase_auth_configured() -> bool:
    return bool(_get_secret("SUPABASE_URL") and _get_secret("SUPABASE_ANON_KEY"))


def supabase_password_auth_configured() -> bool:
    """Compatibility alias retained for the PR #7 scaffold."""
    return supabase_auth_configured()


def _client():
    from supabase import create_client

    return create_client(_get_secret("SUPABASE_URL"), _get_secret("SUPABASE_ANON_KEY"))


def _extract_email(response) -> str:
    user = getattr(response, "user", None)
    if user is not None:
        email = getattr(user, "email", "") or ""
        if str(email).strip():
            return str(email).strip().lower()

    session = getattr(response, "session", None)
    session_user = getattr(session, "user", None) if session is not None else None
    if session_user is not None:
        email = getattr(session_user, "email", "") or ""
        if str(email).strip():
            return str(email).strip().lower()

    try:
        data = response.model_dump()
        email = (
            ((data.get("user") or {}).get("email"))
            or (((data.get("session") or {}).get("user") or {}).get("email"))
            or ""
        )
        return str(email).strip().lower()
    except Exception:
        return ""


def _extract_user_id(response) -> str:
    user = getattr(response, "user", None)
    if user is not None:
        user_id = getattr(user, "id", "") or ""
        if str(user_id).strip():
            return str(user_id).strip()

    session = getattr(response, "session", None)
    session_user = getattr(session, "user", None) if session is not None else None
    if session_user is not None:
        user_id = getattr(session_user, "id", "") or ""
        if str(user_id).strip():
            return str(user_id).strip()

    try:
        data = response.model_dump()
        user_id = (
            ((data.get("user") or {}).get("id"))
            or (((data.get("session") or {}).get("user") or {}).get("id"))
            or ""
        )
        return str(user_id).strip()
    except Exception:
        return ""


def _extract_access_token(response) -> str:
    session = getattr(response, "session", None)
    token = getattr(session, "access_token", "") if session is not None else ""
    if str(token).strip():
        return str(token).strip()
    try:
        data = response.model_dump()
        return str((data.get("session") or {}).get("access_token") or "").strip()
    except Exception:
        return ""


def _apply_supabase_user_to_session(app_user: dict, email: str, auth_user_id: str = "", access_token: str = "") -> bool:
    ok = apply_app_user_to_session(app_user, email=email, auth_provider="supabase", auth_user_id=auth_user_id)
    if access_token:
        st.session_state["supabase_access_token"] = access_token
    return ok


def _find_authorized_user(email: str, auth_user_id: str = ""):
    ok, app_user, message = resolve_app_user(email=email, auth_user_id=auth_user_id)
    return app_user if ok else None


def restore_supabase_login_from_session(force_refresh: bool = False) -> bool:
    if st.session_state.get("signed_out") or st.session_state.get("logout_requested"):
        return False

    if st.session_state.get("auth_provider") != "supabase":
        return False

    email = (st.session_state.get("supabase_auth_email") or "").strip().lower()
    auth_user_id = (st.session_state.get("supabase_auth_user_id") or "").strip()
    if not email and not auth_user_id:
        return False

    if (
        not force_refresh
        and st.session_state.get("logged_in")
        and st.session_state.get("_hm_auth_role_resolved")
        and (st.session_state.get("supabase_auth_email") == email or auth_user_id)
    ):
        return True

    app_user = _find_authorized_user(email, auth_user_id)
    if not app_user:
        st.session_state["logged_in"] = False
        st.session_state["auth_error"] = f"{email or 'This Supabase user'} is authenticated but not authorized in HealthyMe."
        return False

    return _apply_supabase_user_to_session(app_user, email, auth_user_id=auth_user_id)


def sign_in_with_supabase(email: str, password: str) -> Tuple[bool, str]:
    clean_email = (email or "").strip().lower()
    clean_password = password or ""

    if not supabase_auth_configured():
        return False, "Supabase Auth is not configured for this Streamlit app yet."

    if not clean_email or not clean_password:
        return False, "Please enter both email and password."

    try:
        clear_stale_app_identity_before_supabase_login()
        auth_response = _client().auth.sign_in_with_password({"email": clean_email, "password": clean_password})
        clean_auth_email = _extract_email(auth_response) or clean_email
        auth_user_id = _extract_user_id(auth_response)
        access_token = _extract_access_token(auth_response)

        app_user = _find_authorized_user(clean_auth_email, auth_user_id)
        if not app_user:
            st.session_state["auth_error"] = f"{clean_auth_email or 'This email'} is authenticated but not authorized in HealthyMe. Confirm hm_users.role and hm_users.auth_user_id/email mapping."
            return False, st.session_state["auth_error"]

        st.session_state[SUPABASE_SESSION_KEY] = True
        st.session_state["supabase_auth_user_id"] = auth_user_id
        _apply_supabase_user_to_session(app_user, clean_auth_email, auth_user_id=auth_user_id, access_token=access_token)
        return True, "Signed in with Supabase Auth."
    except Exception as exc:
        return False, f"Supabase login failed: {exc}"


def sign_in_with_supabase_password(email: str, password: str) -> Tuple[bool, str, str]:
    """Compatibility helper retained for the PR #7 scaffold."""
    ok, message = sign_in_with_supabase(email, password)
    if not ok:
        return False, "", message
    return True, st.session_state.get("supabase_auth_email", ""), message


def clear_supabase_auth_session() -> None:
    for key in [SUPABASE_SESSION_KEY, "supabase_auth_email", "supabase_auth_user_id", "supabase_access_token"]:
        st.session_state.pop(key, None)
