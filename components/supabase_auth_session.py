import datetime
import os
import secrets
import threading
import time
from typing import Dict, Tuple

import streamlit as st

from components.admin_role_model import apply_app_user_to_session, resolve_app_user


SUPABASE_SESSION_KEY = "_hm_supabase_auth_session"
SUPABASE_LOGIN_JUST_COMPLETED_KEY = "_hm_supabase_login_just_completed"
SUPABASE_BROWSER_SESSION_ID_KEY = "_hm_supabase_browser_session_id"
SUPABASE_BROWSER_COOKIE_NAME = "hm_supabase_sid_v1"
SUPABASE_BROWSER_COOKIE_WRITE_KEY = "_hm_supabase_browser_cookie_write_emitted"
SUPABASE_ROLE_REFRESHED_AT_KEY = "_hm_supabase_role_refreshed_at"
SUPABASE_BROWSER_SESSION_TTL_SECONDS_DEFAULT = 12 * 60 * 60
SUPABASE_ROLE_REFRESH_INTERVAL_SECONDS_DEFAULT = 5 * 60


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


def clear_stale_app_identity_before_supabase_login() -> None:
    """Remove stale Auth0/admin/member role state before a Supabase login."""
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


@st.cache_resource(show_spinner=False)
def _browser_session_store() -> Dict[str, object]:
    """Process-local secure token store shared across Streamlit sessions."""
    return {
        "records": {},
        "lock": threading.RLock(),
    }


def _records_and_lock():
    store = _browser_session_store()
    return store["records"], store["lock"]


def _value(source, key: str, default=None):
    if isinstance(source, dict):
        return source.get(key, default)
    return getattr(source, key, default)


def _model_dump(value) -> dict:
    if isinstance(value, dict):
        return value
    try:
        return value.model_dump()
    except Exception:
        return {}


def _extract_session_payload(response) -> dict:
    session = _value(response, "session")
    if session is None:
        session = _model_dump(response).get("session") or {}

    payload = {
        "access_token": str(_value(session, "access_token", "") or "").strip(),
        "refresh_token": str(_value(session, "refresh_token", "") or "").strip(),
        "expires_at": _value(session, "expires_at"),
    }
    return {
        key: value
        for key, value in payload.items()
        if value is not None and str(value).strip()
    }


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
    return str(_extract_session_payload(response).get("access_token") or "").strip()


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
    return ok


def _find_authorized_user(email: str, auth_user_id: str = ""):
    ok, app_user, _message = resolve_app_user(
        email=email,
        auth_user_id=auth_user_id,
    )
    return app_user if ok else None


def _browser_cookie_is_secure() -> bool:
    try:
        return str(st.context.url or "").lower().startswith("https://")
    except Exception:
        return True


def _cookie_manager():
    import extra_streamlit_components as stx

    return stx.CookieManager(key="hm_supabase_cookie_manager")


def _browser_cookie_marker() -> str:
    try:
        return str(st.context.cookies.get(SUPABASE_BROWSER_COOKIE_NAME) or "").strip()
    except Exception:
        return ""


def _write_browser_cookie(marker: str) -> bool:
    clean_marker = str(marker or "").strip()
    if not clean_marker:
        return False

    try:
        expires_at = datetime.datetime.now() + datetime.timedelta(
            seconds=_browser_session_ttl_seconds()
        )
        manager = _cookie_manager()
        manager.set(
            SUPABASE_BROWSER_COOKIE_NAME,
            clean_marker,
            key=f"hm_supabase_cookie_set_{clean_marker[:12]}",
            path="/",
            expires_at=expires_at,
            secure=_browser_cookie_is_secure(),
            same_site="strict",
        )
        st.session_state[SUPABASE_BROWSER_SESSION_ID_KEY] = clean_marker
        st.session_state[SUPABASE_BROWSER_COOKIE_WRITE_KEY] = True
        return True
    except Exception:
        return False


def _expire_browser_cookie() -> None:
    try:
        manager = _cookie_manager()
        manager.set(
            SUPABASE_BROWSER_COOKIE_NAME,
            "",
            key="hm_supabase_cookie_expire",
            path="/",
            expires_at=datetime.datetime.now() - datetime.timedelta(days=1),
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


def _record_expired(record: dict) -> bool:
    try:
        return time.time() >= float(record.get("marker_expires_at") or 0)
    except Exception:
        return True


def _prune_expired_records_locked(records: dict) -> None:
    expired_markers = [
        marker
        for marker, record in records.items()
        if not isinstance(record, dict) or _record_expired(record)
    ]
    for marker in expired_markers:
        records.pop(marker, None)


def _store_browser_session(auth_response, email: str, auth_user_id: str) -> str:
    payload = _extract_session_payload(auth_response)
    refresh_token = str(payload.get("refresh_token") or "").strip()
    if not refresh_token:
        return ""

    previous_marker = _current_browser_session_id()
    marker = secrets.token_urlsafe(32)
    records, lock = _records_and_lock()
    with lock:
        _prune_expired_records_locked(records)
        if previous_marker:
            records.pop(previous_marker, None)
        records[marker] = {
            **payload,
            "email": (email or "").strip().lower(),
            "auth_user_id": (auth_user_id or "").strip(),
            "updated_at": time.time(),
            "marker_expires_at": time.time() + _browser_session_ttl_seconds(),
        }

    st.session_state[SUPABASE_SESSION_KEY] = True
    st.session_state[SUPABASE_BROWSER_SESSION_ID_KEY] = marker
    st.session_state[SUPABASE_BROWSER_COOKIE_WRITE_KEY] = False

    # Emit once on the login page, then once more on the destination page.
    # The second emission protects against an immediate st.switch_page transition.
    _write_browser_cookie(marker)
    st.session_state[SUPABASE_BROWSER_COOKIE_WRITE_KEY] = False
    return marker


def _ensure_browser_cookie_for_resolved_session() -> None:
    marker = str(
        st.session_state.get(SUPABASE_BROWSER_SESSION_ID_KEY) or ""
    ).strip()
    if not marker:
        return
    if st.session_state.get(SUPABASE_BROWSER_COOKIE_WRITE_KEY):
        return
    _write_browser_cookie(marker)


def _clear_browser_session(marker: str = "") -> None:
    clean_marker = str(marker or _current_browser_session_id() or "").strip()
    if clean_marker:
        records, lock = _records_and_lock()
        with lock:
            records.pop(clean_marker, None)
    _expire_browser_cookie()
    for key in [
        SUPABASE_SESSION_KEY,
        SUPABASE_BROWSER_SESSION_ID_KEY,
        SUPABASE_BROWSER_COOKIE_WRITE_KEY,
        SUPABASE_ROLE_REFRESHED_AT_KEY,
        "supabase_auth_email",
        "supabase_auth_user_id",
        "supabase_access_token",
    ]:
        st.session_state.pop(key, None)


def _restore_from_browser_cookie() -> bool:
    marker = _browser_cookie_marker()
    if not marker:
        return False

    records, lock = _records_and_lock()
    with lock:
        _prune_expired_records_locked(records)
        record = records.get(marker)
        if not isinstance(record, dict):
            _expire_browser_cookie()
            return False

        access_token = str(record.get("access_token") or "").strip()
        refresh_token = str(record.get("refresh_token") or "").strip()
        if not refresh_token:
            records.pop(marker, None)
            _expire_browser_cookie()
            return False

        try:
            client = _client()
            if access_token:
                try:
                    auth_response = client.auth.set_session(
                        access_token,
                        refresh_token,
                    )
                except Exception:
                    auth_response = client.auth.refresh_session(refresh_token)
            else:
                auth_response = client.auth.refresh_session(refresh_token)
        except Exception:
            records.pop(marker, None)
            _expire_browser_cookie()
            st.session_state["auth_error"] = (
                "Your Supabase session could not be refreshed. Please sign in again."
            )
            return False

        clean_email = (
            _extract_email(auth_response)
            or str(record.get("email") or "").strip().lower()
        )
        auth_user_id = (
            _extract_user_id(auth_response)
            or str(record.get("auth_user_id") or "").strip()
        )
        app_user = _find_authorized_user(clean_email, auth_user_id)
        if not app_user:
            records.pop(marker, None)
            _expire_browser_cookie()
            st.session_state["auth_error"] = (
                f"{clean_email or 'This Supabase user'} is authenticated but not "
                "authorized in HealthyMe."
            )
            return False

        refreshed_payload = _extract_session_payload(auth_response)
        if refreshed_payload:
            record.update(refreshed_payload)
        record["email"] = clean_email
        record["auth_user_id"] = auth_user_id
        record["updated_at"] = time.time()
        record["marker_expires_at"] = (
            time.time() + _browser_session_ttl_seconds()
        )
        records[marker] = record

    st.session_state[SUPABASE_SESSION_KEY] = True
    st.session_state[SUPABASE_BROWSER_SESSION_ID_KEY] = marker
    st.session_state[SUPABASE_BROWSER_COOKIE_WRITE_KEY] = False
    st.session_state.pop("signed_out", None)
    st.session_state.pop("logout_requested", None)
    _write_browser_cookie(marker)

    return _apply_supabase_user_to_session(
        app_user,
        clean_email,
        auth_user_id=auth_user_id,
        access_token=_extract_access_token(auth_response),
    )


def _already_resolved_supabase_session() -> bool:
    return bool(
        st.session_state.get("logged_in")
        and st.session_state.get("_hm_auth_role_resolved")
        and (
            st.session_state.get("auth_provider") == "supabase"
            or st.session_state.get("auth_login_method") == "supabase"
        )
    )


def restore_supabase_login_from_session(force_refresh: bool = False) -> bool:
    """Restore Supabase identity across Streamlit reruns and browser refreshes."""
    already_resolved = _already_resolved_supabase_session()

    if st.session_state.get(SUPABASE_LOGIN_JUST_COMPLETED_KEY) or already_resolved:
        st.session_state.pop("signed_out", None)
        st.session_state.pop("logout_requested", None)
    elif st.session_state.get("signed_out") or st.session_state.get(
        "logout_requested"
    ):
        return False

    if already_resolved:
        _ensure_browser_cookie_for_resolved_session()
        st.session_state.pop(SUPABASE_LOGIN_JUST_COMPLETED_KEY, None)
        if not force_refresh:
            return True

        last_role_refresh = float(
            st.session_state.get(SUPABASE_ROLE_REFRESHED_AT_KEY) or 0
        )
        if (
            time.time() - last_role_refresh
            < _role_refresh_interval_seconds()
        ):
            return True

        email = (
            st.session_state.get("supabase_auth_email")
            or st.session_state.get("user_email")
            or st.session_state.get("oidc_email")
            or ""
        ).strip().lower()
        auth_user_id = (
            st.session_state.get("supabase_auth_user_id") or ""
        ).strip()
        app_user = _find_authorized_user(email, auth_user_id)
        if not app_user:
            st.session_state["auth_error"] = (
                f"{email or 'This Supabase user'} role refresh could not be "
                "confirmed. Existing resolved session retained for this request."
            )
            return True

        return _apply_supabase_user_to_session(
            app_user,
            email,
            auth_user_id=auth_user_id,
            access_token=str(
                st.session_state.get("supabase_access_token") or ""
            ).strip(),
        )

    if _restore_from_browser_cookie():
        return True

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
    auth_user_id = (
        st.session_state.get("supabase_auth_user_id") or ""
    ).strip()
    if not email and not auth_user_id:
        return False

    app_user = _find_authorized_user(email, auth_user_id)
    if not app_user:
        st.session_state["logged_in"] = False
        st.session_state["auth_error"] = (
            f"{email or 'This Supabase user'} is authenticated but not "
            "authorized in HealthyMe."
        )
        return False

    ok = _apply_supabase_user_to_session(
        app_user,
        email,
        auth_user_id=auth_user_id,
        access_token=str(
            st.session_state.get("supabase_access_token") or ""
        ).strip(),
    )
    if ok:
        st.session_state.pop(SUPABASE_LOGIN_JUST_COMPLETED_KEY, None)
        _ensure_browser_cookie_for_resolved_session()
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
        access_token = _extract_access_token(auth_response)

        app_user = _find_authorized_user(clean_auth_email, auth_user_id)
        if not app_user:
            st.session_state["auth_error"] = (
                f"{clean_auth_email or 'This email'} is authenticated but not "
                "authorized in HealthyMe. Confirm hm_users.role and "
                "hm_users.auth_user_id/email mapping."
            )
            return False, st.session_state["auth_error"]

        marker = _store_browser_session(
            auth_response,
            clean_auth_email,
            auth_user_id,
        )
        if not marker:
            return False, (
                "Supabase signed in, but a refreshable session could not be "
                "created. Please try again."
            )

        st.session_state[SUPABASE_LOGIN_JUST_COMPLETED_KEY] = True
        st.session_state["supabase_auth_user_id"] = auth_user_id
        st.session_state.pop("signed_out", None)
        st.session_state.pop("logout_requested", None)
        _apply_supabase_user_to_session(
            app_user,
            clean_auth_email,
            auth_user_id=auth_user_id,
            access_token=access_token,
        )
        return True, "Signed in with Supabase Auth."
    except Exception as exc:
        return False, f"Supabase login failed: {exc}"


def sign_in_with_supabase_password(
    email: str,
    password: str,
) -> Tuple[bool, str, str]:
    """Compatibility helper retained for the PR #7 scaffold."""
    ok, message = sign_in_with_supabase(email, password)
    if not ok:
        return False, "", message
    return True, st.session_state.get("supabase_auth_email", ""), message


def clear_supabase_auth_session() -> bool:
    marker = _current_browser_session_id()
    record = None
    records, lock = _records_and_lock()
    with lock:
        if marker:
            record = records.pop(marker, None)

    cleared = True
    if isinstance(record, dict):
        access_token = str(record.get("access_token") or "").strip()
        refresh_token = str(record.get("refresh_token") or "").strip()
        if refresh_token:
            try:
                client = _client()
                if access_token:
                    try:
                        client.auth.set_session(access_token, refresh_token)
                    except Exception:
                        client.auth.refresh_session(refresh_token)
                else:
                    client.auth.refresh_session(refresh_token)
                client.auth.sign_out()
            except Exception:
                cleared = False

    _clear_browser_session(marker)
    st.session_state.pop(SUPABASE_LOGIN_JUST_COMPLETED_KEY, None)
    return cleared
