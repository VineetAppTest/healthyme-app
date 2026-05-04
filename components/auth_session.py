"""
HealthyMe production-safe auth session helper
--------------------------------------------

Production decision:
- Do NOT put login tokens in the URL.
- A shared app link must never act like a login link.
- Browser-refresh persistence uses a browser cookie only.
- Server-side state stores only SHA-256 token hashes.
- If the cookie component is unavailable, the app safely falls back to normal login.

For enterprise-grade SSO later, replace custom password login with Streamlit OIDC/Auth0/Google.
"""

from __future__ import annotations

import datetime as _dt
import hashlib
import secrets
import time
import uuid
from typing import Any, Dict, Optional, Tuple

import streamlit as st

from components.storage_backend import load_state, save_state, normalize_state

AUTH_COOKIE_NAME = "hm_auth_v2"
LEGACY_URL_KEYS = ["hm_sid", "hm_token"]
SESSION_HOURS = 8
RESTORE_WAIT_CYCLES = 2
RESTORE_WAIT_SECONDS = 0.25


def _utc_now() -> _dt.datetime:
    return _dt.datetime.now(_dt.timezone.utc)


def _iso(dt: _dt.datetime) -> str:
    return dt.astimezone(_dt.timezone.utc).isoformat()


def _parse_iso(value: str) -> Optional[_dt.datetime]:
    try:
        value = str(value or "")
        if value.endswith("Z"):
            value = value[:-1] + "+00:00"
        dt = _dt.datetime.fromisoformat(value)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=_dt.timezone.utc)
        return dt.astimezone(_dt.timezone.utc)
    except Exception:
        return None


def _hash_token(token: str) -> str:
    return hashlib.sha256(str(token).encode("utf-8")).hexdigest()


def _make_cookie_value(session_id: str, token: str) -> str:
    return f"{session_id}:{token}"


def _split_cookie_value(value: str) -> Tuple[str, str]:
    value = str(value or "").strip()
    if not value or ":" not in value:
        return "", ""
    session_id, token = value.split(":", 1)
    return session_id.strip(), token.strip()


def clear_legacy_url_tokens() -> None:
    """Remove old hm_sid/hm_token query params from earlier test builds."""
    try:
        for key in LEGACY_URL_KEYS:
            if key in st.query_params:
                st.query_params.pop(key, None)
    except Exception:
        pass


def _get_cookie_manager() -> Any:
    try:
        import extra_streamlit_components as stx  # type: ignore
    except Exception:
        return None

    try:
        if "_hm_cookie_manager_v2" not in st.session_state:
            st.session_state["_hm_cookie_manager_v2"] = stx.CookieManager()
        return st.session_state["_hm_cookie_manager_v2"]
    except Exception:
        try:
            return stx.CookieManager()
        except Exception:
            return None


def _cookie_get() -> str:
    # Try Streamlit context cookies first where available.
    try:
        context_obj = getattr(st, "context", None)
        if context_obj is not None:
            cookies = getattr(st.context, "cookies", {}) or {}
            raw = cookies.get(AUTH_COOKIE_NAME, "")
            if raw:
                return str(raw)
    except Exception:
        pass

    manager = _get_cookie_manager()
    if manager is None:
        return ""

    for method_name in ["get", "get_cookie"]:
        try:
            method = getattr(manager, method_name, None)
            if method:
                raw = method(AUTH_COOKIE_NAME)
                if isinstance(raw, list):
                    raw = raw[0] if raw else ""
                if raw:
                    return str(raw)
        except Exception:
            pass

    for method_name in ["get_all", "getAll"]:
        try:
            method = getattr(manager, method_name, None)
            if method:
                all_cookies = method()
                if isinstance(all_cookies, dict) and all_cookies.get(AUTH_COOKIE_NAME):
                    return str(all_cookies.get(AUTH_COOKIE_NAME))
        except Exception:
            pass

    return ""


def _cookie_set(session_id: str, token: str) -> None:
    manager = _get_cookie_manager()
    if manager is None:
        return

    value = _make_cookie_value(session_id, token)
    expires_at = _utc_now() + _dt.timedelta(hours=SESSION_HOURS)

    try:
        manager.set(cookie=AUTH_COOKIE_NAME, val=value, expires_at=expires_at)
        return
    except TypeError:
        pass
    except Exception:
        return

    try:
        manager.set(AUTH_COOKIE_NAME, value, max_age=SESSION_HOURS * 60 * 60)
        return
    except TypeError:
        pass
    except Exception:
        return

    try:
        manager.set(AUTH_COOKIE_NAME, value)
    except Exception:
        pass


def _cookie_clear() -> None:
    manager = _get_cookie_manager()
    if manager is None:
        return

    for method_name in ["delete", "remove"]:
        try:
            method = getattr(manager, method_name, None)
            if method:
                try:
                    method(cookie=AUTH_COOKIE_NAME)
                except TypeError:
                    method(AUTH_COOKIE_NAME)
                return
        except Exception:
            pass

    try:
        manager.set(cookie=AUTH_COOKIE_NAME, val="", expires_at=_utc_now() - _dt.timedelta(days=1))
    except Exception:
        try:
            manager.set(AUTH_COOKIE_NAME, "", max_age=0)
        except Exception:
            pass


def _find_user(db: Dict[str, Any], user_id: str) -> Optional[Dict[str, Any]]:
    for user in db.get("users", []) or []:
        if str(user.get("id")) == str(user_id) and user.get("is_active", True):
            return user
    return None


def _apply_user_to_session(user: Dict[str, Any], session_id: Optional[str] = None, token: Optional[str] = None) -> None:
    st.session_state["logged_in"] = True
    st.session_state["user_id"] = user["id"]
    st.session_state["user_role"] = user["role"]
    st.session_state["user_name"] = user.get("name", "User")
    st.session_state["must_reset_password"] = bool(user.get("must_reset_password", False))

    if session_id:
        st.session_state["auth_session_id"] = str(session_id)
    if token:
        st.session_state["auth_session_token"] = str(token)


def _cleanup_expired_sessions(db: Dict[str, Any]) -> bool:
    sessions = db.setdefault("auth_sessions", {})
    now = _utc_now()
    changed = False

    for session_id, record in list(sessions.items()):
        expires_at = _parse_iso(str(record.get("expires_at", "")))
        if not expires_at or expires_at <= now:
            sessions.pop(session_id, None)
            changed = True

    return changed


def _get_login_db_snapshot() -> Optional[Dict[str, Any]]:
    try:
        db = st.session_state.pop("_hm_login_db_snapshot", None)
        if isinstance(db, dict):
            return normalize_state(db)
    except Exception:
        pass
    return None


def _validate_session(session_id: str, token: str) -> bool:
    if not session_id or not token:
        return False

    try:
        db = normalize_state(load_state())
        sessions = db.setdefault("auth_sessions", {})
        record = sessions.get(session_id)

        if not record:
            return False

        expires_at = _parse_iso(str(record.get("expires_at", "")))
        if not expires_at or expires_at <= _utc_now():
            sessions.pop(session_id, None)
            save_state(db)
            return False

        if not secrets.compare_digest(str(record.get("token_hash", "")), _hash_token(token)):
            return False

        user = _find_user(db, str(record.get("user_id", "")))
        if not user:
            sessions.pop(session_id, None)
            save_state(db)
            return False

        _apply_user_to_session(user, session_id=session_id, token=token)
        return True

    except Exception:
        return False


def start_persistent_session(user: Dict[str, Any]) -> None:
    db = _get_login_db_snapshot() or normalize_state(load_state())
    _cleanup_expired_sessions(db)

    session_id = str(uuid.uuid4())
    token = secrets.token_urlsafe(32)
    now = _utc_now()
    expires_at = now + _dt.timedelta(hours=SESSION_HOURS)

    db.setdefault("auth_sessions", {})[session_id] = {
        "user_id": user["id"],
        "token_hash": _hash_token(token),
        "created_at": _iso(now),
        "last_seen_at": _iso(now),
        "expires_at": _iso(expires_at),
    }

    save_state(db)
    _apply_user_to_session(user, session_id=session_id, token=token)
    _cookie_set(session_id, token)
    clear_legacy_url_tokens()


def restore_persistent_session() -> bool:
    clear_legacy_url_tokens()

    if st.session_state.get("logged_in"):
        return True

    cookie_value = _cookie_get()
    session_id, token = _split_cookie_value(cookie_value)

    if session_id and token and _validate_session(session_id, token):
        return True

    return False


def restore_session_from_query_params() -> bool:
    return restore_persistent_session()


def restore_session_immediately() -> bool:
    return restore_persistent_session()


def maybe_wait_for_cookie_restore() -> None:
    if st.session_state.get("logged_in"):
        return

    if restore_persistent_session():
        return

    manager_available = _get_cookie_manager() is not None
    cycles = int(st.session_state.get("_hm_cookie_restore_cycles", 0))

    if manager_available and cycles < RESTORE_WAIT_CYCLES:
        st.session_state["_hm_cookie_restore_cycles"] = cycles + 1
        st.info("Restoring secure session...")
        time.sleep(RESTORE_WAIT_SECONDS)
        st.rerun()


def logout_current_session() -> None:
    session_id = str(st.session_state.get("auth_session_id", "") or "").strip()

    if not session_id:
        try:
            session_id, _token = _split_cookie_value(_cookie_get())
        except Exception:
            session_id = ""

    if session_id:
        try:
            db = normalize_state(load_state())
            db.setdefault("auth_sessions", {}).pop(str(session_id), None)
            save_state(db)
        except Exception:
            pass

    _cookie_clear()
    clear_legacy_url_tokens()

    for key in list(st.session_state.keys()):
        del st.session_state[key]

    st.switch_page("pages/01_Login.py")


def safe_switch_page(page: str) -> None:
    clear_legacy_url_tokens()
    st.switch_page(page)


def publish_active_session_to_url() -> None:
    # Legacy compatibility no-op. Tokens are intentionally never placed in URLs.
    clear_legacy_url_tokens()


def install_switch_page_patch() -> None:
    # Legacy compatibility no-op.
    clear_legacy_url_tokens()


def route_authenticated_user() -> None:
    if not st.session_state.get("logged_in"):
        return

    clear_legacy_url_tokens()

    if st.session_state.get("must_reset_password"):
        safe_switch_page("pages/00_Reset_Password.py")
    elif st.session_state.get("user_role") == "admin":
        safe_switch_page("pages/10_Admin_Dashboard.py")
    else:
        safe_switch_page("pages/02_Member_Home.py")
