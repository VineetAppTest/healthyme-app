import os
import time
from typing import Any, Dict, Tuple

import streamlit as st

from components.admin_role_model import apply_app_user_to_session, resolve_app_user


SUPABASE_SESSION_KEY = "_hm_supabase_auth_session"
SUPABASE_LOGIN_JUST_COMPLETED_KEY = "_hm_supabase_login_just_completed"
SUPABASE_REFRESH_TOKEN_KEY = "_hm_supabase_refresh_token"
SUPABASE_EXPIRES_AT_KEY = "_hm_supabase_expires_at"
LEGACY_SUPABASE_BROWSER_COOKIE_NAME = "hm_supabase_sid_v1"
TOKEN_REFRESH_SKEW_SECONDS = 90


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


def _get_secret(name: str, default: str = "") -> str:
    value = os.environ.get(name)
    if value:
        return value
    try:
        value = st.secrets.get(name, default)
        return str(value) if value is not None else default
    except Exception:
        return default


def clear_stale_app_identity_before_supabase_login() -> None:
    """Remove stale app/Auth0 role state before a Supabase login."""
    for key in ROLE_SESSION_KEYS:
        st.session_state.pop(key, None)
    st.session_state.pop("signed_out", None)
    st.session_state.pop("logout_requested", None)


def supabase_auth_configured() -> bool:
    return bool(_get_secret("SUPABASE_URL") and _get_secret("SUPABASE_ANON_KEY"))


def supabase_password_auth_configured() -> bool:
    """Compatibility alias retained for earlier auth migration code."""
    return supabase_auth_configured()


def _client():
    from supabase import create_client

    return create_client(_get_secret("SUPABASE_URL"), _get_secret("SUPABASE_ANON_KEY"))


def browser_has_legacy_supabase_marker() -> bool:
    """Detect the retired PR #128 marker without trusting it for authentication."""
    try:
        return bool(st.context.cookies.get(LEGACY_SUPABASE_BROWSER_COOKIE_NAME))
    except Exception:
        return False


def _value(source: Any, key: str, default: Any = None) -> Any:
    if isinstance(source, dict):
        return source.get(key, default)
    return getattr(source, key, default)


def _model_dump(value: Any) -> Dict[str, Any]:
    if isinstance(value, dict):
        return value
    try:
        return value.model_dump()
    except Exception:
        return {}


def _extract_session_payload(response: Any) -> Dict[str, Any]:
    session = _value(response, "session")
    if session is None:
        session = _model_dump(response).get("session") or {}

    payload = {
        "access_token": str(_value(session, "access_token", "") or "").strip(),
        "refresh_token": str(_value(session, "refresh_token", "") or "").strip(),
        "expires_at": _value(session, "expires_at"),
    }
    return payload


def _extract_email(response: Any) -> str:
    user = _value(response, "user")
    if user is not None:
        email = _value(user, "email", "") or ""
        if str(email).strip():
            return str(email).strip().lower()

    session = _value(response, "session")
    session_user = _value(session, "user") if session is not None else None
    if session_user is not None:
        email = _value(session_user, "email", "") or ""
        if str(email).strip():
            return str(email).strip().lower()

    data = _model_dump(response)
    email = (
        ((data.get("user") or {}).get("email"))
        or (((data.get("session") or {}).get("user") or {}).get("email"))
        or ""
    )
    return str(email).strip().lower()


def _extract_user_id(response: Any) -> str:
    user = _value(response, "user")
    if user is not None:
        user_id = _value(user, "id", "") or ""
        if str(user_id).strip():
            return str(user_id).strip()

    session = _value(response, "session")
    session_user = _value(session, "user") if session is not None else None
    if session_user is not None:
        user_id = _value(session_user, "id", "") or ""
        if str(user_id).strip():
            return str(user_id).strip()

    data = _model_dump(response)
    user_id = (
        ((data.get("user") or {}).get("id"))
        or (((data.get("session") or {}).get("user") or {}).get("id"))
        or ""
    )
    return str(user_id).strip()


def _store_session_payload(payload: Dict[str, Any]) -> None:
    access_token = str(payload.get("access_token") or "").strip()
    refresh_token = str(payload.get("refresh_token") or "").strip()
    expires_at = payload.get("expires_at")

    if access_token:
        st.session_state["supabase_access_token"] = access_token
    if refresh_token:
        st.session_state[SUPABASE_REFRESH_TOKEN_KEY] = refresh_token
    if expires_at not in (None, ""):
        st.session_state[SUPABASE_EXPIRES_AT_KEY] = expires_at


def _token_needs_refresh() -> bool:
    expires_at = st.session_state.get(SUPABASE_EXPIRES_AT_KEY)
    refresh_token = str(st.session_state.get(SUPABASE_REFRESH_TOKEN_KEY) or "").strip()
    if not refresh_token or expires_at in (None, ""):
        return False
    try:
        return float(expires_at) <= time.time() + TOKEN_REFRESH_SKEW_SECONDS
    except (TypeError, ValueError):
        return False


def _refresh_session_if_needed(force: bool = False) -> bool:
    access_token = str(st.session_state.get("supabase_access_token") or "").strip()
    refresh_token = str(st.session_state.get(SUPABASE_REFRESH_TOKEN_KEY) or "").strip()
    if not access_token or not refresh_token:
        return True
    if not force and not _token_needs_refresh():
        return True

    try:
        client = _client()
        client.auth.set_session(access_token, refresh_token)
        response = client.auth.refresh_session(refresh_token)
        payload = _extract_session_payload(response)
        if not payload.get("access_token"):
            return False
        _store_session_payload(payload)
        return True
    except Exception:
        return False


def _apply_supabase_user_to_session(
    app_user: dict,
    email: str,
    auth_user_id: str = "",
    access_token: str = "",
) -> bool:
    resolved_auth_user_id = (auth_user_id or app_user.get("auth_user_id") or "").strip()
    ok = apply_app_user_to_session(
        app_user,
        email=email,
        auth_provider="supabase",
        auth_user_id=resolved_auth_user_id,
    )
    if access_token:
        st.session_state["supabase_access_token"] = access_token
    if resolved_auth_user_id:
        st.session_state["supabase_auth_user_id"] = resolved_auth_user_id
    return ok


def _find_authorized_user(email: str, auth_user_id: str = ""):
    ok, app_user, _message = resolve_app_user(email=email, auth_user_id=auth_user_id)
    return app_user if ok else None


def restore_supabase_login_from_session(force_refresh: bool = False) -> bool:
    """Restore a resolved Supabase identity from the active Streamlit session.

    No Auth0 identity, URL token, browser local storage, or legacy cookie marker is
    trusted here. A full server restart therefore requires a fresh sign-in.
    """
    already_resolved_supabase = (
        st.session_state.get("logged_in")
        and st.session_state.get("_hm_auth_role_resolved")
        and (
            st.session_state.get("auth_provider") == "supabase"
            or st.session_state.get("auth_login_method") == "supabase"
        )
    )
    if st.session_state.get(SUPABASE_LOGIN_JUST_COMPLETED_KEY) or already_resolved_supabase:
        st.session_state.pop("signed_out", None)
        st.session_state.pop("logout_requested", None)
    elif st.session_state.get("signed_out") or st.session_state.get("logout_requested"):
        return False

    if (
        st.session_state.get("auth_provider") != "supabase"
        and st.session_state.get("auth_login_method") != "supabase"
    ):
        return False

    email = (
        st.session_state.get("supabase_auth_email")
        or st.session_state.get("user_email")
        or st.session_state.get("oidc_email")
        or ""
    ).strip().lower()
    auth_user_id = str(st.session_state.get("supabase_auth_user_id") or "").strip()
    if not email and not auth_user_id:
        return False

    if not _refresh_session_if_needed(force=force_refresh):
        st.session_state["auth_error"] = "Your Supabase session expired. Please sign in again."
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
        st.session_state["auth_error"] = (
            f"{email or 'This Supabase user'} is authenticated but not authorized in HealthyMe."
        )
        return False

    ok = _apply_supabase_user_to_session(
        app_user,
        email,
        auth_user_id=auth_user_id,
        access_token=str(st.session_state.get("supabase_access_token") or "").strip(),
    )
    if ok:
        st.session_state.pop(SUPABASE_LOGIN_JUST_COMPLETED_KEY, None)
    return ok


def sign_in_with_supabase(email: str, password: str) -> Tuple[bool, str]:
    clean_email = (email or "").strip().lower()
    clean_password = password or ""

    if not supabase_auth_configured():
        return False, "Supabase Auth is not configured for this Streamlit app yet."
    if not clean_email or not clean_password:
        return False, "Please enter both email and password."

    try:
        clear_stale_app_identity_before_supabase_login()
        auth_response = _client().auth.sign_in_with_password(
            {"email": clean_email, "password": clean_password}
        )
        clean_auth_email = _extract_email(auth_response) or clean_email
        auth_user_id = _extract_user_id(auth_response)
        session_payload = _extract_session_payload(auth_response)

        app_user = _find_authorized_user(clean_auth_email, auth_user_id)
        if not app_user:
            st.session_state["auth_error"] = (
                f"{clean_auth_email or 'This email'} is authenticated but not authorized in "
                "HealthyMe. Confirm the active user and role mapping."
            )
            return False, st.session_state["auth_error"]

        st.session_state[SUPABASE_SESSION_KEY] = True
        st.session_state[SUPABASE_LOGIN_JUST_COMPLETED_KEY] = True
        st.session_state["supabase_auth_user_id"] = auth_user_id
        st.session_state.pop("signed_out", None)
        st.session_state.pop("logout_requested", None)
        _store_session_payload(session_payload)
        _apply_supabase_user_to_session(
            app_user,
            clean_auth_email,
            auth_user_id=auth_user_id,
            access_token=str(session_payload.get("access_token") or "").strip(),
        )
        st.session_state.pop("auth_error", None)
        return True, "Signed in with Supabase Auth."
    except Exception as exc:
        return False, f"Supabase login failed: {exc}"


def sign_in_with_supabase_password(
    email: str,
    password: str,
) -> Tuple[bool, str, str]:
    """Compatibility helper retained for the earlier auth scaffold."""
    ok, message = sign_in_with_supabase(email, password)
    if not ok:
        return False, "", message
    return True, st.session_state.get("supabase_auth_email", ""), message


def clear_supabase_auth_session() -> bool:
    """Revoke the current Supabase refresh session, then clear local auth state."""
    remote_logout_ok = True
    access_token = str(st.session_state.get("supabase_access_token") or "").strip()
    refresh_token = str(st.session_state.get(SUPABASE_REFRESH_TOKEN_KEY) or "").strip()

    if access_token and refresh_token and supabase_auth_configured():
        try:
            client = _client()
            client.auth.set_session(access_token, refresh_token)
            try:
                client.auth.sign_out({"scope": "local"})
            except TypeError:
                client.auth.sign_out()
        except Exception:
            remote_logout_ok = False

    for key in [
        SUPABASE_SESSION_KEY,
        SUPABASE_LOGIN_JUST_COMPLETED_KEY,
        SUPABASE_REFRESH_TOKEN_KEY,
        SUPABASE_EXPIRES_AT_KEY,
        "supabase_auth_email",
        "supabase_auth_user_id",
        "supabase_access_token",
    ]:
        st.session_state.pop(key, None)
    return remote_logout_ok
