import os
from typing import Tuple


def _get_secret(name: str, default: str = "") -> str:
    value = os.environ.get(name)
    if value:
        return value
    try:
        import streamlit as st
        value = st.secrets.get(name, default)
        return str(value) if value is not None else default
    except Exception:
        return default


def supabase_password_auth_configured() -> bool:
    return bool(_get_secret("SUPABASE_URL") and _get_secret("SUPABASE_ANON_KEY"))


def _supabase_auth_client():
    from supabase import create_client

    url = _get_secret("SUPABASE_URL")
    anon_key = _get_secret("SUPABASE_ANON_KEY")
    return create_client(url, anon_key)


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
        email = (((data.get("user") or {}).get("email")) or ((data.get("session") or {}).get("user") or {}).get("email") or "")
        return str(email).strip().lower()
    except Exception:
        return ""


def sign_in_with_supabase_password(email: str, password: str) -> Tuple[bool, str, str]:
    """Validate email/password against Supabase Auth using the public anon key.

    Returns (ok, normalized_email, message).
    This helper does not persist tokens in HealthyMe app state and does not create users.
    """
    clean_email = (email or "").strip().lower()
    clean_password = (password or "").strip()

    if not clean_email or not clean_password:
        return False, "", "Please enter both email and password."

    if not supabase_password_auth_configured():
        return False, "", "Supabase login is not configured yet. Please use Auth0 login."

    try:
        client = _supabase_auth_client()
        response = client.auth.sign_in_with_password({"email": clean_email, "password": clean_password})
        resolved_email = _extract_email(response) or clean_email
        return True, resolved_email, "Supabase authentication successful."
    except Exception as exc:
        message = str(exc).strip() or "Supabase login failed."
        return False, "", f"Supabase login failed: {message}"
