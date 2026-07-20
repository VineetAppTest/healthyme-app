"""Supabase authentication with durable refresh restoration for HealthyMe Streamlit.

H13C replaces the process-local session registry used by H13A/H13B. The browser
stores only a random opaque marker. Its SHA-256 hash and the refreshable Supabase
session are stored in a restricted Supabase table accessed with the service-role key.
"""

from __future__ import annotations

import datetime
import os
import secrets
import time
from typing import Any, Dict, Optional, Tuple

import streamlit as st

from components.admin_role_model import apply_app_user_to_session, resolve_app_user
from components.supabase_durable_session_store import (
    DurableSessionStoreError,
    cleanup_expired_sessions,
    create_session,
    durable_session_store_configured,
    load_session,
    revoke_session,
    touch_session,
    update_role_snapshot,
    update_tokens,
)

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

RESTORE_COOKIE_MANAGER_KEY = "_hm_h13c_restore_cookie_manager"
RESTORE_COOKIE_PROBE_STARTED_KEY = "_hm_h13c_restore_cookie_probe_started"
RESTORE_COOKIE_PROBE_COMPLETE_KEY = "_hm_h13c_restore_cookie_probe_complete"
LAST_DURABLE_TOUCH_KEY = "_hm_h13c_last_durable_touch"
DURABLE_CLEANUP_ATTEMPTED_KEY = "_hm_h13c_cleanup_attempted"
SECRET_SECTIONS = ("auth", "auth0", "authentication", "healthyme", "supabase")

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

HANDOFF_SESSION_KEYS = [
    "_hm_supabase_cookie_handoff_armed",
    "_hm_supabase_cookie_handoff_pending",
    "_hm_supabase_cookie_handoff_phase",
    "_hm_supabase_cookie_handoff_started_at",
]


def _get_secret(name: str, default: str = "") -> str:
    value = os.environ.get(name)
    if value:
        return str(value).strip()

    try:
        value = st.secrets.get(name)
        if value is not None:
            return str(value).strip()

        lower_name = name.lower()
        value = st.secrets.get(lower_name)
        if value is not None:
            return str(value).strip()

        for section in SECRET_SECTIONS:
            section_values = st.secrets.get(section)
            if not section_values:
                continue
            try:
                value = section_values.get(name)
                if value is None:
                    value = section_values.get(lower_name)
                if value is not None:
                    return str(value).strip()
            except Exception:
                continue
    except Exception:
        pass
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
    """H13C requires Auth configuration plus the server-only service-role key."""
    return bool(
        _get_secret("SUPABASE_URL")
        and _get_secret("SUPABASE_ANON_KEY")
        and durable_session_store_configured()
    )


def supabase_password_auth_configured() -> bool:
    return supabase_auth_configured()


def _auth_client():
    from supabase import create_client

    return create_client(
        _get_secret("SUPABASE_URL"),
        _get_secret("SUPABASE_ANON_KEY"),
    )


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
        email = str(_value(user, "email", "") or "").strip().lower()
        if email:
            return email

    session = _value(response, "session")
    session_user = _value(session, "user") if session is not None else None
    if session_user is not None:
        email = str(_value(session_user, "email", "") or "").strip().lower()
        if email:
            return email

    data = _model_dump(response)
    return str(
        ((data.get("user") or {}).get("email"))
        or (((data.get("session") or {}).get("user") or {}).get("email"))
        or ""
    ).strip().lower()


def _extract_user_id(response: Any) -> str:
    user = _value(response, "user")
    if user is not None:
        user_id = str(_value(user, "id", "") or "").strip()
        if user_id:
            return user_id

    session = _value(response, "session")
    session_user = _value(session, "user") if session is not None else None
    if session_user is not None:
        user_id = str(_value(session_user, "id", "") or "").strip()
        if user_id:
            return user_id

    data = _model_dump(response)
    return str(
        ((data.get("user") or {}).get("id"))
        or (((data.get("session") or {}).get("user") or {}).get("id"))
        or ""
    ).strip()


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


def _find_authorized_user(email: str, auth_user_id: str = ""):
    ok, app_user, _message = resolve_app_user(
        email=email,
        auth_user_id=auth_user_id,
    )
    return app_user if ok else None


def _apply_supabase_user_to_session(
    app_user: Dict[str, Any],
    email: str,
    auth_user_id: str = "",
    access_token: str = "",
) -> bool:
    resolved_auth_user_id = str(
        auth_user_id or app_user.get("auth_user_id") or ""
    ).strip()
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
    return bool(ok)


def _browser_cookie_is_secure() -> bool:
    try:
        return str(st.context.url or "").lower().startswith("https://")
    except Exception:
        return True


def _restore_cookie_manager():
    manager = st.session_state.get(RESTORE_COOKIE_MANAGER_KEY)
    if manager is not None:
        return manager

    import extra_streamlit_components as stx

    manager = stx.CookieManager(key="hm_h13c_restore_cookie_manager_v1")
    st.session_state[RESTORE_COOKIE_MANAGER_KEY] = manager
    return manager


def _context_cookie(cookie_name: str) -> str:
    try:
        return str(st.context.cookies.get(cookie_name) or "").strip()
    except Exception:
        return ""


def _component_cookie(cookie_name: str, *, allow_probe: bool) -> str:
    if not allow_probe:
        return ""
    if st.session_state.get(RESTORE_COOKIE_PROBE_COMPLETE_KEY):
        return ""

    first_probe = not st.session_state.get(RESTORE_COOKIE_PROBE_STARTED_KEY)
    if first_probe:
        st.session_state[RESTORE_COOKIE_PROBE_STARTED_KEY] = True

    try:
        cookies = (
            _restore_cookie_manager().get_all(
                key="hm_h13c_restore_cookie_read_v1"
            )
            or {}
        )
    except Exception:
        cookies = {}

    marker = str(cookies.get(cookie_name) or "").strip()
    if marker:
        st.session_state.pop(RESTORE_COOKIE_PROBE_STARTED_KEY, None)
        st.session_state[RESTORE_COOKIE_PROBE_COMPLETE_KEY] = True
        return marker

    if first_probe:
        # The browser component now mounts and sends its cookie dictionary back,
        # which triggers a Streamlit rerun. Stop this run before a guard redirects.
        st.info("Restoring your secure HealthyMe session…")
        st.stop()

    st.session_state.pop(RESTORE_COOKIE_PROBE_STARTED_KEY, None)
    st.session_state[RESTORE_COOKIE_PROBE_COMPLETE_KEY] = True
    return ""


def _browser_cookie_marker(
    cookie_name: str = SUPABASE_BROWSER_COOKIE_NAME,
    *,
    allow_component_probe: bool = True,
) -> str:
    marker = _context_cookie(cookie_name)
    if marker:
        st.session_state[RESTORE_COOKIE_PROBE_COMPLETE_KEY] = True
        return marker
    return _component_cookie(cookie_name, allow_probe=allow_component_probe)


def browser_has_legacy_supabase_marker() -> bool:
    return bool(
        _browser_cookie_marker(
            LEGACY_SUPABASE_BROWSER_COOKIE_NAME,
            allow_component_probe=False,
        )
    )


def _current_browser_session_id(*, allow_component_probe: bool = False) -> str:
    return (
        str(
            st.session_state.get(SUPABASE_BROWSER_SESSION_ID_KEY)
            or ""
        ).strip()
        or _browser_cookie_marker(
            SUPABASE_BROWSER_COOKIE_NAME,
            allow_component_probe=allow_component_probe,
        )
    )


def _write_browser_cookie(marker: str) -> bool:
    """Compatibility writer retained for callers outside the H13B handoff."""
    clean_marker = str(marker or "").strip()
    if not clean_marker:
        return False
    try:
        manager = _restore_cookie_manager()
        manager.set(
            SUPABASE_BROWSER_COOKIE_NAME,
            clean_marker,
            key=f"hm_h13c_cookie_set_{clean_marker[:12]}",
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
        manager = _restore_cookie_manager()
        expired_at = datetime.datetime.now() - datetime.timedelta(days=1)
        for cookie_name, suffix in (
            (SUPABASE_BROWSER_COOKIE_NAME, "v2"),
            (LEGACY_SUPABASE_BROWSER_COOKIE_NAME, "v1"),
        ):
            manager.set(
                cookie_name,
                "",
                key=f"hm_h13c_cookie_expire_{suffix}",
                path="/",
                expires_at=expired_at,
                secure=_browser_cookie_is_secure(),
                same_site="strict",
            )
    except Exception:
        pass

    for key in (
        SUPABASE_BROWSER_COOKIE_WRITE_KEY,
        RESTORE_COOKIE_PROBE_STARTED_KEY,
        RESTORE_COOKIE_PROBE_COMPLETE_KEY,
    ):
        st.session_state.pop(key, None)


def _token_needs_refresh(expires_at: Any, refresh_token: str) -> bool:
    if not refresh_token or expires_at in (None, ""):
        return False
    try:
        return float(expires_at) <= time.time() + TOKEN_REFRESH_SKEW_SECONDS
    except (TypeError, ValueError):
        return False


def _refresh_supabase_session(
    access_token: str,
    refresh_token: str,
) -> Tuple[bool, Dict[str, Any], Any]:
    if not refresh_token:
        return False, {}, None

    client = _auth_client()
    try:
        response = client.auth.refresh_session(refresh_token)
    except Exception:
        try:
            if access_token:
                client.auth.set_session(access_token, refresh_token)
            response = client.auth.refresh_session(refresh_token)
        except Exception:
            return False, {}, None

    payload = _extract_session_payload(response)
    if not payload.get("access_token") or not payload.get("refresh_token"):
        return False, {}, response
    return True, payload, response


def _parse_datetime(value: Any) -> Optional[datetime.datetime]:
    if isinstance(value, datetime.datetime):
        parsed = value
    else:
        text = str(value or "").strip()
        if not text:
            return None
        try:
            parsed = datetime.datetime.fromisoformat(
                text.replace("Z", "+00:00")
            )
        except ValueError:
            return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=datetime.timezone.utc)
    return parsed.astimezone(datetime.timezone.utc)


def _record_snapshot_is_fresh(record: Dict[str, Any]) -> bool:
    snapshot = record.get("app_user_snapshot")
    checked_at = _parse_datetime(record.get("role_checked_at"))
    if not isinstance(snapshot, dict) or not snapshot or not checked_at:
        return False
    age = (
        datetime.datetime.now(datetime.timezone.utc) - checked_at
    ).total_seconds()
    return age < _role_refresh_interval_seconds()


def _maybe_cleanup_expired_sessions() -> None:
    if st.session_state.get(DURABLE_CLEANUP_ATTEMPTED_KEY):
        return
    st.session_state[DURABLE_CLEANUP_ATTEMPTED_KEY] = True
    cleanup_expired_sessions(retention_days=7)


def _restore_from_durable_marker(marker: str) -> bool:
    try:
        record = load_session(marker)
    except DurableSessionStoreError as exc:
        st.session_state["auth_error"] = str(exc)
        return False

    if not record:
        _expire_browser_cookies()
        st.session_state["_hm_access_recovery_message"] = (
            "Your earlier browser session is no longer active. "
            "Please sign in once to create the durable Supabase session."
        )
        return False

    access_token = str(record.get("access_token") or "").strip()
    refresh_token = str(record.get("refresh_token") or "").strip()
    expires_at = record.get("token_expires_at")

    if _token_needs_refresh(expires_at, refresh_token):
        ok, payload, refresh_response = _refresh_supabase_session(
            access_token,
            refresh_token,
        )
        if not ok:
            revoke_session(marker)
            _expire_browser_cookies()
            st.session_state["auth_error"] = (
                "Your Supabase session expired and could not be refreshed. "
                "Please sign in again."
            )
            return False

        access_token = str(payload.get("access_token") or "").strip()
        refresh_token = str(payload.get("refresh_token") or "").strip()
        expires_at = payload.get("expires_at")
        record["access_token"] = access_token
        record["refresh_token"] = refresh_token
        record["token_expires_at"] = expires_at
        record["user_email"] = (
            _extract_email(refresh_response)
            or str(record.get("user_email") or "").strip().lower()
        )
        record["auth_user_id"] = (
            _extract_user_id(refresh_response)
            or str(record.get("auth_user_id") or "").strip()
        )
        try:
            update_tokens(
                marker=marker,
                access_token=access_token,
                refresh_token=refresh_token,
                token_expires_at=expires_at,
                ttl_seconds=_browser_session_ttl_seconds(),
            )
        except DurableSessionStoreError as exc:
            st.session_state["auth_error"] = str(exc)
            return False

    email = str(record.get("user_email") or "").strip().lower()
    auth_user_id = str(record.get("auth_user_id") or "").strip()

    if _record_snapshot_is_fresh(record):
        app_user = dict(record.get("app_user_snapshot") or {})
    else:
        app_user = _find_authorized_user(email, auth_user_id)
        if not app_user:
            revoke_session(marker)
            _expire_browser_cookies()
            st.session_state["auth_error"] = (
                f"{email or 'This Supabase user'} is no longer authorized in HealthyMe."
            )
            return False
        try:
            update_role_snapshot(
                marker=marker,
                app_role=str(
                    app_user.get("role")
                    or app_user.get("user_role")
                    or ""
                ),
                app_user_snapshot=dict(app_user),
            )
        except DurableSessionStoreError:
            # Role resolution succeeded; a failed audit snapshot update should not
            # discard an otherwise valid session.
            pass

    st.session_state[SUPABASE_SESSION_KEY] = True
    st.session_state[SUPABASE_BROWSER_SESSION_ID_KEY] = marker
    st.session_state["supabase_auth_email"] = email
    st.session_state[SUPABASE_BROWSER_COOKIE_WRITE_KEY] = True
    st.session_state.pop("signed_out", None)
    st.session_state.pop("logout_requested", None)
    _store_session_payload(
        {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "expires_at": expires_at,
        }
    )

    if not _apply_supabase_user_to_session(
        app_user,
        email,
        auth_user_id=auth_user_id,
        access_token=access_token,
    ):
        return False

    try:
        touch_session(marker, _browser_session_ttl_seconds())
        st.session_state[LAST_DURABLE_TOUCH_KEY] = time.time()
    except DurableSessionStoreError:
        pass

    _maybe_cleanup_expired_sessions()
    return True


def _refresh_active_session_if_needed(force: bool = False) -> bool:
    marker = str(
        st.session_state.get(SUPABASE_BROWSER_SESSION_ID_KEY)
        or ""
    ).strip()
    access_token = str(
        st.session_state.get("supabase_access_token")
        or ""
    ).strip()
    refresh_token = str(
        st.session_state.get(SUPABASE_REFRESH_TOKEN_KEY)
        or ""
    ).strip()
    expires_at = st.session_state.get(SUPABASE_EXPIRES_AT_KEY)

    if not marker or not refresh_token:
        return False

    if force or _token_needs_refresh(expires_at, refresh_token):
        ok, payload, _response = _refresh_supabase_session(
            access_token,
            refresh_token,
        )
        if not ok:
            revoke_session(marker)
            return False
        _store_session_payload(payload)
        try:
            update_tokens(
                marker=marker,
                access_token=str(payload.get("access_token") or ""),
                refresh_token=str(payload.get("refresh_token") or ""),
                token_expires_at=payload.get("expires_at"),
                ttl_seconds=_browser_session_ttl_seconds(),
            )
        except DurableSessionStoreError:
            return False

    now = time.time()
    role_refreshed_at = float(
        st.session_state.get(SUPABASE_ROLE_REFRESHED_AT_KEY)
        or 0
    )
    if now - role_refreshed_at >= _role_refresh_interval_seconds():
        try:
            record = load_session(marker)
        except DurableSessionStoreError:
            return False
        if not record:
            return False

        email = str(
            st.session_state.get("supabase_auth_email")
            or st.session_state.get("user_email")
            or record.get("user_email")
            or ""
        ).strip().lower()
        auth_user_id = str(
            st.session_state.get("supabase_auth_user_id")
            or record.get("auth_user_id")
            or ""
        ).strip()
        app_user = _find_authorized_user(email, auth_user_id)
        if not app_user:
            revoke_session(marker)
            return False

        if not _apply_supabase_user_to_session(
            app_user,
            email,
            auth_user_id=auth_user_id,
            access_token=str(
                st.session_state.get("supabase_access_token")
                or record.get("access_token")
                or ""
            ).strip(),
        ):
            return False
        try:
            update_role_snapshot(
                marker=marker,
                app_role=str(
                    app_user.get("role")
                    or app_user.get("user_role")
                    or ""
                ),
                app_user_snapshot=dict(app_user),
            )
        except DurableSessionStoreError:
            # The role was revalidated successfully. A transient snapshot-write
            # failure must not log out an otherwise valid active session.
            pass

    last_touch = float(
        st.session_state.get(LAST_DURABLE_TOUCH_KEY)
        or 0
    )
    if now - last_touch >= _role_refresh_interval_seconds():
        try:
            touch_session(marker, _browser_session_ttl_seconds())
            st.session_state[LAST_DURABLE_TOUCH_KEY] = now
        except DurableSessionStoreError:
            # Keep the active session; the durable expiry remains unchanged and a
            # later refresh will retry against the authoritative store.
            pass
    return True


def restore_supabase_login_from_session(force_refresh: bool = False) -> bool:
    """Restore Supabase auth from active state or a durable browser marker."""
    if st.session_state.get("signed_out") or st.session_state.get(
        "logout_requested"
    ):
        return False
    if not supabase_auth_configured():
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
                "Your durable Supabase session could not be refreshed. "
                "Please sign in again."
            )
            return False
        _clear_recovery_flags()
        st.session_state.pop(SUPABASE_LOGIN_JUST_COMPLETED_KEY, None)
        return True

    marker = _browser_cookie_marker(
        SUPABASE_BROWSER_COOKIE_NAME,
        allow_component_probe=True,
    )
    if not marker:
        return False
    return _restore_from_durable_marker(marker)


def sign_in_with_supabase(email: str, password: str) -> Tuple[bool, str]:
    clean_email = str(email or "").strip().lower()
    clean_password = password or ""

    if not supabase_auth_configured():
        return (
            False,
            "Supabase Auth durability is incomplete. Configure SUPABASE_URL, "
            "SUPABASE_ANON_KEY and the server-only SUPABASE_SERVICE_ROLE_KEY, "
            "then run the H13C SQL migration.",
        )
    if not clean_email or not clean_password:
        return False, "Please enter both email and password."

    try:
        previous_marker = _current_browser_session_id(
            allow_component_probe=False
        )
        clear_stale_app_identity_before_supabase_login()
        auth_response = _auth_client().auth.sign_in_with_password(
            {"email": clean_email, "password": clean_password}
        )
        clean_auth_email = _extract_email(auth_response) or clean_email
        auth_user_id = _extract_user_id(auth_response)
        payload = _extract_session_payload(auth_response)

        app_user = _find_authorized_user(
            clean_auth_email,
            auth_user_id,
        )
        if not app_user:
            return (
                False,
                f"{clean_auth_email or 'This email'} is authenticated but not "
                "authorized in HealthyMe. Confirm the active user and role mapping.",
            )

        marker = secrets.token_urlsafe(48)
        create_session(
            marker=marker,
            user_email=clean_auth_email,
            auth_user_id=auth_user_id,
            app_role=str(
                app_user.get("role")
                or app_user.get("user_role")
                or ""
            ),
            app_user_snapshot=dict(app_user),
            access_token=str(payload.get("access_token") or ""),
            refresh_token=str(payload.get("refresh_token") or ""),
            token_expires_at=payload.get("expires_at"),
            ttl_seconds=_browser_session_ttl_seconds(),
        )

        if previous_marker and previous_marker != marker:
            revoke_session(previous_marker)

        st.session_state[SUPABASE_SESSION_KEY] = True
        st.session_state[SUPABASE_LOGIN_JUST_COMPLETED_KEY] = True
        st.session_state[SUPABASE_BROWSER_SESSION_ID_KEY] = marker
        st.session_state[SUPABASE_BROWSER_COOKIE_WRITE_KEY] = False
        st.session_state["supabase_auth_user_id"] = auth_user_id
        st.session_state["supabase_auth_email"] = clean_auth_email
        st.session_state.pop("signed_out", None)
        st.session_state.pop("logout_requested", None)
        st.session_state.pop(RESTORE_COOKIE_PROBE_STARTED_KEY, None)
        st.session_state.pop(RESTORE_COOKIE_PROBE_COMPLETE_KEY, None)
        _store_session_payload(payload)

        if not _apply_supabase_user_to_session(
            app_user,
            clean_auth_email,
            auth_user_id=auth_user_id,
            access_token=str(payload.get("access_token") or ""),
        ):
            revoke_session(marker)
            return False, "HealthyMe could not apply the authorized user role."

        st.session_state.pop("auth_error", None)
        _maybe_cleanup_expired_sessions()
        return True, "Signed in with durable Supabase Auth."
    except DurableSessionStoreError as exc:
        return False, str(exc)
    except Exception as exc:
        return False, f"Supabase login failed: {exc}"


def sign_in_with_supabase_password(
    email: str,
    password: str,
) -> Tuple[bool, str, str]:
    ok, message = sign_in_with_supabase(email, password)
    if not ok:
        return False, "", message
    return True, st.session_state.get("supabase_auth_email", ""), message


def clear_supabase_auth_session() -> bool:
    """Revoke Supabase auth, durable row and browser markers."""
    remote_logout_ok = True
    durable_revoke_ok = True

    marker = _current_browser_session_id(allow_component_probe=False)
    access_token = str(
        st.session_state.get("supabase_access_token")
        or ""
    ).strip()
    refresh_token = str(
        st.session_state.get(SUPABASE_REFRESH_TOKEN_KEY)
        or ""
    ).strip()

    if marker and (not access_token or not refresh_token):
        try:
            record = load_session(marker) or {}
            access_token = access_token or str(
                record.get("access_token")
                or ""
            ).strip()
            refresh_token = refresh_token or str(
                record.get("refresh_token")
                or ""
            ).strip()
        except DurableSessionStoreError:
            pass

    if marker:
        durable_revoke_ok = revoke_session(marker)

    if access_token and refresh_token and _get_secret("SUPABASE_ANON_KEY"):
        try:
            client = _auth_client()
            client.auth.set_session(access_token, refresh_token)
            try:
                client.auth.sign_out({"scope": "local"})
            except TypeError:
                client.auth.sign_out()
        except Exception:
            remote_logout_ok = False

    _expire_browser_cookies()

    for key in [
        SUPABASE_SESSION_KEY,
        SUPABASE_LOGIN_JUST_COMPLETED_KEY,
        SUPABASE_REFRESH_TOKEN_KEY,
        SUPABASE_EXPIRES_AT_KEY,
        SUPABASE_BROWSER_SESSION_ID_KEY,
        SUPABASE_BROWSER_COOKIE_WRITE_KEY,
        SUPABASE_ROLE_REFRESHED_AT_KEY,
        LAST_DURABLE_TOUCH_KEY,
        DURABLE_CLEANUP_ATTEMPTED_KEY,
        RESTORE_COOKIE_MANAGER_KEY,
        "supabase_auth_email",
        "supabase_auth_user_id",
        "supabase_access_token",
        *HANDOFF_SESSION_KEYS,
    ]:
        st.session_state.pop(key, None)
    _clear_recovery_flags()
    return bool(remote_logout_ok and durable_revoke_ok)
