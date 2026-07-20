import datetime
import os
import secrets
import threading
import time
from typing import Any, Dict, Tuple

import streamlit as st

from components.admin_role_model import apply_app_user_to_session, resolve_app_user


SUPABASE_SESSION_KEY = "_hm_supabase_auth_session"
SUPABASE_LOGIN_JUST_COMPLETED_KEY = "_hm_supabase_login_just_completed"
SUPABASE_REFRESH_TOKEN_KEY = "_hm_supabase_refresh_token"
SUPABASE_EXPIRES_AT_KEY = "_hm_supabase_expires_at"
SUPABASE_BROWSER_SESSION_ID_KEY = "_hm_supabase_browser_session_id"
SUPABASE_BROWSER_COOKIE_NAME = "hm_supabase_sid_v2"
LEGACY_SUPABASE_BROWSER_COOKIE_NAME = "hm_supabase_sid_v1"
SUPABASE_BROWSER_COOKIE_WRITE_KEY = "_hm_supabase_browser_cookie_write_emitted"
SUPABASE_ROLE_REFRESHED_AT_KEY = "_hm_supabase_role_refreshed_at"
SUPABASE_BROWSER_SESSION_TTL_SECONDS_DEFAULT = 12 * 60 * 60
SUPABASE_ROLE_REFRESH_INTERVAL_SECONDS_DEFAULT = 5 * 60
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

RECOVERY_SESSION_KEYS = [
    "_hm_expected_login_role",
    "_hm_access_recovery_message",
    "_hm_legacy_supabase_marker_detected",
    "_hm_member_restore_retry",
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


def _positive_int_secret(name: str, default: int, minimum: int) -> int:
    raw_value = _get_secret(name, str(default))
    try:
        parsed = int(float(raw_value))
    except Exception:
        parsed = default
    return max(parsed, minimum)


def _browser_session_ttl_seconds() -> int:
    return _positive_int_secret(
        "SUPABASE_BROWSER_SESSION_TTL_SECONDS",
        SUPABASE_BROWSER_SESSION_TTL_SECONDS_DEFAULT,
        5 * 60,
    )


def _role_refresh_interval_seconds() -> int:
    return _positive_int_secret(
        "SUPABASE_ROLE_REFRESH_INTERVAL_SECONDS",
        SUPABASE_ROLE_REFRESH_INTERVAL_SECONDS_DEFAULT,
        30,
    )


def _clear_recovery_flags() -> None:
    for key in RECOVERY_SESSION_KEYS:
        st.session_state.pop(key, None)


def clear_stale_app_identity_before_supabase_login() -> None:
    """Remove stale app/Auth0 role and recovery state before a Supabase login."""
    for key in ROLE_SESSION_KEYS:
        st.session_state.pop(key, None)
    _clear_recovery_flags()
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


@st.cache_resource(show_spinner=False)
def _browser_session_store() -> Dict[str, object]:
    """Process-local secure token store shared across Streamlit browser sessions."""
    return {
        "records": {},
        "lock": threading.RLock(),
    }


def _records_and_lock():
    store = _browser_session_store()
    return store["records"], store["lock"]


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
    return {
        "access_token": str(_value(session, "access_token", "") or "").strip(),
        "refresh_token": str(_value(session, "refresh_token", "") or "").strip(),
        "expires_at": _value(session, "expires_at"),
    }


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
    if ok:
        st.session_state[SUPABASE_ROLE_REFRESHED_AT_KEY] = time.time()
        _clear_recovery_flags()
    return ok


def _find_authorized_user(email: str, auth_user_id: str = ""):
    ok, app_user, _message = resolve_app_user(email=email, auth_user_id=auth_user_id)
    return app_user if ok else None


def _browser_cookie_is_secure() -> bool:
    try:
        return str(st.context.url or "").lower().startswith("https://")
    except Exception:
        return True


def _cookie_manager():
    import extra_streamlit_components as stx

    return stx.CookieManager(key="hm_supabase_cookie_manager_v2")


def _browser_cookie_marker(cookie_name: str = SUPABASE_BROWSER_COOKIE_NAME) -> str:
    try:
        return str(st.context.cookies.get(cookie_name) or "").strip()
    except Exception:
        return ""


def browser_has_legacy_supabase_marker() -> bool:
    """Compatibility helper; the retired marker is never trusted for authentication."""
    return bool(_browser_cookie_marker(LEGACY_SUPABASE_BROWSER_COOKIE_NAME))


def _write_browser_cookie(marker: str) -> bool:
    clean_marker = str(marker or "").strip()
    if not clean_marker:
        return False
    try:
        manager = _cookie_manager()
        manager.set(
            SUPABASE_BROWSER_COOKIE_NAME,
            clean_marker,
            key=f"hm_supabase_cookie_set_{clean_marker[:12]}",
            path="/",
            expires_at=datetime.datetime.now() + datetime.timedelta(
                seconds=_browser_session_ttl_seconds()
            ),
            secure=_browser_cookie_is_secure(),
            same_site="strict",
        )
        st.session_state[SUPABASE_BROWSER_SESSION_ID_KEY] = clean_marker
        st.session_state[SUPABASE_BROWSER_COOKIE_WRITE_KEY] = True
        return True
    except Exception:
        return False


def _expire_browser_cookies() -> None:
    try:
        manager = _cookie_manager()
        expired_at = datetime.datetime.now() - datetime.timedelta(days=1)
        for cookie_name, key_suffix in (
            (SUPABASE_BROWSER_COOKIE_NAME, "v2"),
            (LEGACY_SUPABASE_BROWSER_COOKIE_NAME, "v1"),
        ):
            manager.set(
                cookie_name,
                "",
                key=f"hm_supabase_cookie_expire_{key_suffix}",
                path="/",
                expires_at=expired_at,
                secure=_browser_cookie_is_secure(),
                same_site="strict",
            )
    except Exception:
        pass
    st.session_state.pop(SUPABASE_BROWSER_COOKIE_WRITE_KEY, None)


def _current_browser_session_id() -> str:
    return (
        str(st.session_state.get(SUPABASE_BROWSER_SESSION_ID_KEY) or "").strip()
        or _browser_cookie_marker()
    )


def _record_expired(record: Dict[str, Any]) -> bool:
    try:
        return time.time() >= float(record.get("marker_expires_at") or 0)
    except Exception:
        return True


def _prune_expired_records_locked(records: Dict[str, Dict[str, Any]]) -> None:
    expired_markers = [
        marker
        for marker, record in records.items()
        if not isinstance(record, dict) or _record_expired(record)
    ]
    for marker in expired_markers:
        records.pop(marker, None)


def _store_browser_session(
    auth_response: Any,
    email: str,
    auth_user_id: str,
    app_user: Dict[str, Any],
) -> str:
    payload = _extract_session_payload(auth_response)
    refresh_token = str(payload.get("refresh_token") or "").strip()
    if not refresh_token:
        return ""

    previous_marker = _current_browser_session_id()
    marker = secrets.token_urlsafe(32)
    now = time.time()
    record = {
        **payload,
        "email": (email or "").strip().lower(),
        "auth_user_id": (auth_user_id or "").strip(),
        "app_user": dict(app_user or {}),
        "role_checked_at": now,
        "updated_at": now,
        "marker_expires_at": now + _browser_session_ttl_seconds(),
    }

    records, lock = _records_and_lock()
    with lock:
        _prune_expired_records_locked(records)
        if previous_marker:
            records.pop(previous_marker, None)
        records[marker] = record

    st.session_state[SUPABASE_SESSION_KEY] = True
    st.session_state[SUPABASE_BROWSER_SESSION_ID_KEY] = marker
    st.session_state[SUPABASE_BROWSER_COOKIE_WRITE_KEY] = False

    # Emit now and once more on the destination page. The second emission protects
    # the cookie write when st.switch_page follows immediately after authentication.
    _write_browser_cookie(marker)
    st.session_state[SUPABASE_BROWSER_COOKIE_WRITE_KEY] = False
    return marker


def _ensure_browser_cookie_for_resolved_session() -> None:
    marker = str(
        st.session_state.get(SUPABASE_BROWSER_SESSION_ID_KEY) or ""
    ).strip()
    if not marker or st.session_state.get(SUPABASE_BROWSER_COOKIE_WRITE_KEY):
        return
    _write_browser_cookie(marker)


def _token_needs_refresh(expires_at: Any, refresh_token: str) -> bool:
    if not refresh_token or expires_at in (None, ""):
        return False
    try:
        return float(expires_at) <= time.time() + TOKEN_REFRESH_SKEW_SECONDS
    except (TypeError, ValueError):
        return False


def _refresh_record_if_needed(
    record: Dict[str, Any],
    force: bool = False,
) -> Tuple[bool, Dict[str, Any]]:
    access_token = str(record.get("access_token") or "").strip()
    refresh_token = str(record.get("refresh_token") or "").strip()
    if not refresh_token:
        return False, record
    if not force and not _token_needs_refresh(record.get("expires_at"), refresh_token):
        return True, record

    try:
        client = _client()
        if access_token:
            try:
                client.auth.set_session(access_token, refresh_token)
            except Exception:
                pass
        response = client.auth.refresh_session(refresh_token)
        payload = _extract_session_payload(response)
        if not payload.get("access_token"):
            return False, record
        refreshed = dict(record)
        refreshed.update(payload)
        refreshed["email"] = _extract_email(response) or refreshed.get("email", "")
        refreshed["auth_user_id"] = (
            _extract_user_id(response) or refreshed.get("auth_user_id", "")
        )
        refreshed["updated_at"] = time.time()
        return True, refreshed
    except Exception:
        return False, record


def _resolve_record_user(record: Dict[str, Any], force: bool = False):
    cached_user = record.get("app_user")
    try:
        role_age = time.time() - float(record.get("role_checked_at") or 0)
    except Exception:
        role_age = _role_refresh_interval_seconds() + 1

    if (
        not force
        and isinstance(cached_user, dict)
        and cached_user
        and role_age < _role_refresh_interval_seconds()
    ):
        return cached_user, record

    email = str(record.get("email") or "").strip().lower()
    auth_user_id = str(record.get("auth_user_id") or "").strip()
    app_user = _find_authorized_user(email, auth_user_id)
    if not app_user:
        return None, record

    updated = dict(record)
    updated["app_user"] = dict(app_user)
    updated["role_checked_at"] = time.time()
    return app_user, updated


def _restore_from_browser_cookie() -> bool:
    marker = _browser_cookie_marker()
    if not marker:
        return False

    records, lock = _records_and_lock()
    with lock:
        _prune_expired_records_locked(records)
        stored = records.get(marker)
        record = dict(stored) if isinstance(stored, dict) else None

    if not record:
        _expire_browser_cookies()
        st.session_state["_hm_access_recovery_message"] = (
            "Your secure session ended after the app service restarted. Please sign in again."
        )
        return False

    refresh_ok, record = _refresh_record_if_needed(record)
    if not refresh_ok:
        with lock:
            records.pop(marker, None)
        _expire_browser_cookies()
        st.session_state["auth_error"] = (
            "Your Supabase session expired and could not be refreshed. Please sign in again."
        )
        return False

    app_user, record = _resolve_record_user(record)
    if not app_user:
        with lock:
            records.pop(marker, None)
        _expire_browser_cookies()
        st.session_state["auth_error"] = (
            f"{str(record.get('email') or 'This Supabase user')} is no longer authorized in HealthyMe."
        )
        return False

    now = time.time()
    record["updated_at"] = now
    record["marker_expires_at"] = now + _browser_session_ttl_seconds()
    with lock:
        records[marker] = record

    st.session_state[SUPABASE_SESSION_KEY] = True
    st.session_state[SUPABASE_BROWSER_SESSION_ID_KEY] = marker
    st.session_state[SUPABASE_BROWSER_COOKIE_WRITE_KEY] = True
    st.session_state.pop("signed_out", None)
    st.session_state.pop("logout_requested", None)
    _store_session_payload(record)

    return _apply_supabase_user_to_session(
        app_user,
        str(record.get("email") or "").strip().lower(),
        auth_user_id=str(record.get("auth_user_id") or "").strip(),
        access_token=str(record.get("access_token") or "").strip(),
    )


def _update_current_browser_record() -> None:
    marker = str(
        st.session_state.get(SUPABASE_BROWSER_SESSION_ID_KEY) or ""
    ).strip()
    if not marker:
        return

    records, lock = _records_and_lock()
    with lock:
        current = records.get(marker)
        if not isinstance(current, dict):
            return
        current.update(
            {
                "access_token": str(
                    st.session_state.get("supabase_access_token") or ""
                ).strip(),
                "refresh_token": str(
                    st.session_state.get(SUPABASE_REFRESH_TOKEN_KEY) or ""
                ).strip(),
                "expires_at": st.session_state.get(SUPABASE_EXPIRES_AT_KEY),
                "email": str(
                    st.session_state.get("supabase_auth_email")
                    or st.session_state.get("user_email")
                    or ""
                ).strip().lower(),
                "auth_user_id": str(
                    st.session_state.get("supabase_auth_user_id") or ""
                ).strip(),
                "updated_at": time.time(),
            }
        )
        records[marker] = current


def _refresh_active_session_if_needed(force: bool = False) -> bool:
    record = {
        "access_token": str(
            st.session_state.get("supabase_access_token") or ""
        ).strip(),
        "refresh_token": str(
            st.session_state.get(SUPABASE_REFRESH_TOKEN_KEY) or ""
        ).strip(),
        "expires_at": st.session_state.get(SUPABASE_EXPIRES_AT_KEY),
        "email": str(
            st.session_state.get("supabase_auth_email")
            or st.session_state.get("user_email")
            or ""
        ).strip().lower(),
        "auth_user_id": str(
            st.session_state.get("supabase_auth_user_id") or ""
        ).strip(),
    }
    if not record["refresh_token"]:
        return True
    ok, refreshed = _refresh_record_if_needed(record, force=force)
    if ok:
        _store_session_payload(refreshed)
        _update_current_browser_record()
    return ok


def restore_supabase_login_from_session(force_refresh: bool = False) -> bool:
    """Restore Supabase auth from active state or an opaque browser-session marker.

    Supabase credentials remain server-side. The browser cookie contains only a
    random marker and cannot authenticate without its matching server record.
    """
    if st.session_state.get("signed_out") or st.session_state.get("logout_requested"):
        return False

    already_resolved_supabase = (
        st.session_state.get("logged_in")
        and st.session_state.get("_hm_auth_role_resolved")
        and (
            st.session_state.get("auth_provider") == "supabase"
            or st.session_state.get("auth_login_method") == "supabase"
        )
    )

    if already_resolved_supabase:
        if not _refresh_active_session_if_needed(force=force_refresh):
            st.session_state["auth_error"] = (
                "Your Supabase session expired. Please sign in again."
            )
            return False
        _ensure_browser_cookie_for_resolved_session()
        _clear_recovery_flags()
        st.session_state.pop(SUPABASE_LOGIN_JUST_COMPLETED_KEY, None)
        return True

    return _restore_from_browser_cookie()


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
        _store_browser_session(
            auth_response,
            clean_auth_email,
            auth_user_id,
            app_user,
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
    """Revoke Supabase auth, remove server record and expire browser markers."""
    remote_logout_ok = True
    marker = _current_browser_session_id()
    access_token = str(st.session_state.get("supabase_access_token") or "").strip()
    refresh_token = str(st.session_state.get(SUPABASE_REFRESH_TOKEN_KEY) or "").strip()

    if marker and (not access_token or not refresh_token):
        records, lock = _records_and_lock()
        with lock:
            record = records.get(marker)
            if isinstance(record, dict):
                access_token = access_token or str(
                    record.get("access_token") or ""
                ).strip()
                refresh_token = refresh_token or str(
                    record.get("refresh_token") or ""
                ).strip()

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

    if marker:
        records, lock = _records_and_lock()
        with lock:
            records.pop(marker, None)

    _expire_browser_cookies()

    for key in [
        SUPABASE_SESSION_KEY,
        SUPABASE_LOGIN_JUST_COMPLETED_KEY,
        SUPABASE_REFRESH_TOKEN_KEY,
        SUPABASE_EXPIRES_AT_KEY,
        SUPABASE_BROWSER_SESSION_ID_KEY,
        SUPABASE_BROWSER_COOKIE_WRITE_KEY,
        SUPABASE_ROLE_REFRESHED_AT_KEY,
        "supabase_auth_email",
        "supabase_auth_user_id",
        "supabase_access_token",
    ]:
        st.session_state.pop(key, None)
    _clear_recovery_flags()
    return remote_logout_ok
