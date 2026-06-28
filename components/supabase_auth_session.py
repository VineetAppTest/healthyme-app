import json
import os
import secrets
import time
from typing import Dict, Optional, Tuple

import streamlit as st
import streamlit.components.v1 as components

from components.db import find_user_by_email
from components.normalized_store import find_user_by_email_fast


SUPABASE_SESSION_KEY = "_hm_supabase_auth_session"
SUPABASE_BROWSER_SESSION_ID_KEY = "_hm_supabase_auth_browser_session_id"
SUPABASE_BROWSER_STORAGE_KEY = "hm_supabase_auth_session_id"
SUPABASE_BROWSER_QUERY_PARAM = "hm_supabase_auth_sid"
SUPABASE_BROWSER_MISSING_MARKER = "__missing__"


def _get_secret(name: str, default: str = "") -> str:
    value = os.environ.get(name)
    if value:
        return value
    try:
        value = st.secrets.get(name, default)
        return str(value) if value is not None else default
    except Exception:
        return default


def supabase_auth_configured() -> bool:
    return bool(_get_secret("SUPABASE_URL") and _get_secret("SUPABASE_ANON_KEY"))


def supabase_password_auth_configured() -> bool:
    """Compatibility alias retained for the PR #7 scaffold."""
    return supabase_auth_configured()


def _client():
    from supabase import create_client

    return create_client(_get_secret("SUPABASE_URL"), _get_secret("SUPABASE_ANON_KEY"))


@st.cache_resource
def _browser_session_registry() -> Dict[str, dict]:
    return {}


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
        session = (_model_dump(response).get("session") or {})

    payload = {
        "access_token": str(_value(session, "access_token", "") or ""),
        "refresh_token": str(_value(session, "refresh_token", "") or ""),
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
    st.session_state["auth_login_method"] = "supabase"
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


def _get_browser_query_marker(include_missing: bool = False) -> str:
    try:
        marker = st.query_params.get(SUPABASE_BROWSER_QUERY_PARAM, "")
    except Exception:
        return ""

    if isinstance(marker, list):
        marker = marker[0] if marker else ""

    marker = str(marker or "").strip()
    if marker == SUPABASE_BROWSER_MISSING_MARKER and not include_missing:
        return ""
    return marker


def _current_browser_session_id() -> str:
    return (
        str(st.session_state.get(SUPABASE_BROWSER_SESSION_ID_KEY) or "").strip()
        or _get_browser_query_marker()
    )


def _store_browser_session(auth_response, email: str) -> str:
    payload = _extract_session_payload(auth_response)
    if not payload.get("access_token") or not payload.get("refresh_token"):
        return ""

    session_id = _current_browser_session_id() or secrets.token_urlsafe(32)
    _browser_session_registry()[session_id] = {
        **payload,
        "email": (email or "").strip().lower(),
        "updated_at": time.time(),
    }
    st.session_state[SUPABASE_SESSION_KEY] = True
    st.session_state[SUPABASE_BROWSER_SESSION_ID_KEY] = session_id
    return session_id


def _update_browser_session_record(session_id: str, response, email: str) -> None:
    if not session_id:
        return

    record = _browser_session_registry().get(session_id, {})
    payload = _extract_session_payload(response)
    if payload:
        record.update(payload)
    record["email"] = (email or record.get("email") or "").strip().lower()
    record["updated_at"] = time.time()
    _browser_session_registry()[session_id] = record
    st.session_state[SUPABASE_SESSION_KEY] = True
    st.session_state[SUPABASE_BROWSER_SESSION_ID_KEY] = session_id


def render_supabase_browser_session_bridge(clear: bool = False, stop_for_sync: bool = False) -> None:
    """Synchronize the opaque Supabase pilot marker between browser and Streamlit.

    The browser stores only a random marker. Supabase access and refresh tokens stay in
    the server-side registry for the current Streamlit process.
    """

    current_marker = str(st.session_state.get(SUPABASE_BROWSER_SESSION_ID_KEY) or "")
    script = f"""
<script>
(() => {{
  const storageKey = {json.dumps(SUPABASE_BROWSER_STORAGE_KEY)};
  const queryKey = {json.dumps(SUPABASE_BROWSER_QUERY_PARAM)};
  const missingMarker = {json.dumps(SUPABASE_BROWSER_MISSING_MARKER)};
  const currentMarker = {json.dumps(current_marker)};
  const shouldClear = {json.dumps(bool(clear))};

  try {{
    const url = new URL(window.parent.location.href);
    const params = url.searchParams;
    const replaceUrl = () => {{
      const next = url.pathname + (params.toString() ? `?${{params.toString()}}` : '') + url.hash;
      window.parent.history.replaceState(null, '', next);
    }};
    const navigateWithParams = () => {{
      const next = url.pathname + (params.toString() ? `?${{params.toString()}}` : '') + url.hash;
      window.parent.location.href = next;
    }};

    if (shouldClear) {{
      window.parent.localStorage.removeItem(storageKey);
      if (params.has(queryKey)) {{
        params.delete(queryKey);
        replaceUrl();
      }}
      return;
    }}

    if (currentMarker) {{
      window.parent.localStorage.setItem(storageKey, currentMarker);
      if (params.has(queryKey)) {{
        params.delete(queryKey);
        replaceUrl();
      }}
      return;
    }}

    const queryMarker = params.get(queryKey);
    if (queryMarker) {{
      if (queryMarker === missingMarker) {{
        params.delete(queryKey);
        replaceUrl();
      }}
      return;
    }}

    const storedMarker = window.parent.localStorage.getItem(storageKey);
    params.set(queryKey, storedMarker || missingMarker);
    navigateWithParams();
  }} catch (error) {{
    // Browser storage access can fail in unusual embedded contexts. In that case,
    // keep normal Streamlit/Auth0 behavior rather than blocking the app.
  }}
}})();
</script>
"""
    components.html(script, height=0, width=0)

    if (
        stop_for_sync
        and not current_marker
        and not _get_browser_query_marker(include_missing=True)
        and not st.session_state.get("signed_out")
        and not st.session_state.get("logout_requested")
    ):
        st.caption("Restoring secure session...")
        st.stop()


def _restore_from_browser_marker() -> bool:
    session_id = _get_browser_query_marker()
    if not session_id:
        return False

    record = _browser_session_registry().get(session_id)
    if not record:
        render_supabase_browser_session_bridge(clear=True)
        return False

    access_token = str(record.get("access_token") or "")
    refresh_token = str(record.get("refresh_token") or "")
    if not access_token or not refresh_token:
        _browser_session_registry().pop(session_id, None)
        render_supabase_browser_session_bridge(clear=True)
        return False

    try:
        client = _client()
        try:
            auth_response = client.auth.set_session(access_token, refresh_token)
        except Exception:
            auth_response = client.auth.refresh_session(refresh_token)
    except Exception:
        _browser_session_registry().pop(session_id, None)
        render_supabase_browser_session_bridge(clear=True)
        st.session_state["logged_in"] = False
        st.session_state["auth_error"] = "Supabase session expired. Please sign in again."
        return False

    email = _extract_email(auth_response) or str(record.get("email") or "").strip().lower()
    app_user = _find_authorized_user(email)
    if not app_user:
        st.session_state["logged_in"] = False
        st.session_state["auth_error"] = f"{email or 'This email'} is authenticated but not authorized in HealthyMe."
        return False

    _update_browser_session_record(session_id, auth_response, email)
    return _apply_supabase_user_to_session(app_user, email)


def restore_supabase_login_from_session() -> bool:
    if st.session_state.get("signed_out") or st.session_state.get("logout_requested"):
        return False

    if _restore_from_browser_marker():
        return True

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
        clean_auth_email = _extract_email(auth_response) or clean_email

        app_user = _find_authorized_user(clean_auth_email)
        if not app_user:
            st.session_state["auth_error"] = f"{clean_auth_email or 'This email'} is authenticated but not authorized in HealthyMe."
            return False, st.session_state["auth_error"]

        _store_browser_session(auth_response, clean_auth_email)
        _apply_supabase_user_to_session(app_user, clean_auth_email)
        return True, "Signed in with Supabase Auth."
    except Exception as exc:
        return False, f"Supabase login failed: {exc}"


def sign_in_with_supabase_password(email: str, password: str) -> Tuple[bool, str, str]:
    """Compatibility helper retained for the PR #7 scaffold."""
    ok, message = sign_in_with_supabase(email, password)
    if not ok:
        return False, "", message
    return True, st.session_state.get("supabase_auth_email", ""), message


def clear_supabase_auth_session() -> bool:
    session_id = _current_browser_session_id()
    record = _browser_session_registry().pop(session_id, None) if session_id else None
    cleared = True

    if record and record.get("access_token") and record.get("refresh_token"):
        try:
            client = _client()
            try:
                client.auth.set_session(record["access_token"], record["refresh_token"])
            except Exception:
                pass
            client.auth.sign_out()
        except Exception:
            cleared = False

    for key in [SUPABASE_SESSION_KEY, SUPABASE_BROWSER_SESSION_ID_KEY, "supabase_auth_email"]:
        st.session_state.pop(key, None)

    return cleared
