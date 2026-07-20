"""Durable Supabase session repository for HealthyMe Streamlit authentication.

This module is server-only. It uses SUPABASE_SERVICE_ROLE_KEY to access a table
that has no anon/authenticated privileges or RLS policies.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
import hashlib
import json
import os
from typing import Any, Dict, Optional

import streamlit as st

SESSION_TABLE = "hm_streamlit_auth_sessions"
SECRET_SECTIONS = ("auth", "auth0", "authentication", "healthyme", "supabase")


class DurableSessionStoreError(RuntimeError):
    """Raised when the durable Streamlit session store cannot be used."""


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


def durable_session_store_configured() -> bool:
    return bool(
        _get_secret("SUPABASE_URL")
        and _get_secret("SUPABASE_SERVICE_ROLE_KEY")
    )


@st.cache_resource(show_spinner=False)
def _service_client():
    if not durable_session_store_configured():
        raise DurableSessionStoreError(
            "SUPABASE_SERVICE_ROLE_KEY is not configured for the Streamlit service."
        )

    from supabase import create_client

    return create_client(
        _get_secret("SUPABASE_URL"),
        _get_secret("SUPABASE_SERVICE_ROLE_KEY"),
    )


def _response_data(response: Any):
    if response is None:
        return None
    if isinstance(response, dict):
        return response.get("data")
    return getattr(response, "data", None)


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _iso(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat()


def _parse_timestamp(value: Any) -> Optional[datetime]:
    if isinstance(value, datetime):
        parsed = value
    else:
        text = str(value or "").strip()
        if not text:
            return None
        try:
            parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
        except ValueError:
            return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def marker_hash(marker: str) -> str:
    clean_marker = str(marker or "").strip()
    if len(clean_marker) < 32:
        raise DurableSessionStoreError("The browser session marker is invalid.")
    return hashlib.sha256(clean_marker.encode("utf-8")).hexdigest()


def _normalise_snapshot(value: Any) -> Dict[str, Any]:
    if not isinstance(value, dict):
        return {}
    try:
        return json.loads(json.dumps(value, default=str))
    except Exception:
        return {str(key): str(item) for key, item in value.items()}


def create_session(
    *,
    marker: str,
    user_email: str,
    auth_user_id: str,
    app_role: str,
    app_user_snapshot: Dict[str, Any],
    access_token: str,
    refresh_token: str,
    token_expires_at: Any,
    ttl_seconds: int,
) -> Dict[str, Any]:
    """Create one durable session row and preserve other device sessions."""
    clean_email = str(user_email or "").strip().lower()
    clean_access_token = str(access_token or "").strip()
    clean_refresh_token = str(refresh_token or "").strip()
    if not clean_email:
        raise DurableSessionStoreError("A user email is required.")
    if not clean_access_token or not clean_refresh_token:
        raise DurableSessionStoreError("Supabase did not return a refreshable session.")

    now = _utc_now()
    expiry = now + timedelta(seconds=max(int(ttl_seconds), 300))
    row = {
        "marker_hash": marker_hash(marker),
        "user_email": clean_email,
        "auth_user_id": str(auth_user_id or "").strip() or None,
        "app_role": str(app_role or "").strip() or None,
        "app_user_snapshot": _normalise_snapshot(app_user_snapshot),
        "access_token": clean_access_token,
        "refresh_token": clean_refresh_token,
        "token_expires_at": (
            int(float(token_expires_at))
            if token_expires_at not in (None, "")
            else None
        ),
        "expires_at": _iso(expiry),
        "role_checked_at": _iso(now),
        "last_seen_at": _iso(now),
        "metadata": {"source": "healthyme_streamlit_h13c"},
    }

    client = _service_client()
    try:
        # Marker rotation for the same browser is handled by the auth layer. Do not
        # revoke sessions on other devices merely because the email is the same.
        response = client.table(SESSION_TABLE).insert(row).execute()
        data = _response_data(response) or []
        if isinstance(data, list) and data:
            return dict(data[0])
        return dict(row)
    except Exception as exc:
        raise DurableSessionStoreError(
            "HealthyMe could not create the durable Supabase session. "
            "Confirm that the H13C SQL migration has been run."
        ) from exc


def load_session(marker: str) -> Optional[Dict[str, Any]]:
    """Load one active, unexpired session by hashed opaque marker."""
    digest = marker_hash(marker)
    try:
        response = (
            _service_client()
            .table(SESSION_TABLE)
            .select("*")
            .eq("marker_hash", digest)
            .limit(1)
            .execute()
        )
    except Exception as exc:
        raise DurableSessionStoreError(
            "HealthyMe could not read the durable Supabase session store."
        ) from exc

    data = _response_data(response) or []
    if not isinstance(data, list) or not data:
        return None

    record = dict(data[0])
    if record.get("revoked_at"):
        return None

    expires_at = _parse_timestamp(record.get("expires_at"))
    if not expires_at or expires_at <= _utc_now():
        revoke_session(marker)
        return None
    return record


def update_tokens(
    *,
    marker: str,
    access_token: str,
    refresh_token: str,
    token_expires_at: Any,
    ttl_seconds: int,
) -> None:
    now = _utc_now()
    expiry = now + timedelta(seconds=max(int(ttl_seconds), 300))
    payload = {
        "access_token": str(access_token or "").strip(),
        "refresh_token": str(refresh_token or "").strip(),
        "token_expires_at": (
            int(float(token_expires_at))
            if token_expires_at not in (None, "")
            else None
        ),
        "expires_at": _iso(expiry),
        "last_seen_at": _iso(now),
    }
    if not payload["access_token"] or not payload["refresh_token"]:
        raise DurableSessionStoreError("The refreshed Supabase session is incomplete.")

    try:
        (
            _service_client()
            .table(SESSION_TABLE)
            .update(payload)
            .eq("marker_hash", marker_hash(marker))
            .is_("revoked_at", "null")
            .execute()
        )
    except Exception as exc:
        raise DurableSessionStoreError(
            "HealthyMe could not update the refreshed Supabase session."
        ) from exc


def update_role_snapshot(
    *,
    marker: str,
    app_role: str,
    app_user_snapshot: Dict[str, Any],
) -> None:
    now = _utc_now()
    try:
        (
            _service_client()
            .table(SESSION_TABLE)
            .update(
                {
                    "app_role": str(app_role or "").strip() or None,
                    "app_user_snapshot": _normalise_snapshot(app_user_snapshot),
                    "role_checked_at": _iso(now),
                    "last_seen_at": _iso(now),
                }
            )
            .eq("marker_hash", marker_hash(marker))
            .is_("revoked_at", "null")
            .execute()
        )
    except Exception as exc:
        raise DurableSessionStoreError(
            "HealthyMe could not update the durable role snapshot."
        ) from exc


def touch_session(marker: str, ttl_seconds: int) -> None:
    now = _utc_now()
    expiry = now + timedelta(seconds=max(int(ttl_seconds), 300))
    try:
        (
            _service_client()
            .table(SESSION_TABLE)
            .update(
                {
                    "last_seen_at": _iso(now),
                    "expires_at": _iso(expiry),
                }
            )
            .eq("marker_hash", marker_hash(marker))
            .is_("revoked_at", "null")
            .execute()
        )
    except Exception as exc:
        raise DurableSessionStoreError(
            "HealthyMe could not extend the durable browser session."
        ) from exc


def revoke_session(marker: str) -> bool:
    clean_marker = str(marker or "").strip()
    if not clean_marker:
        return True

    now = _utc_now()
    try:
        (
            _service_client()
            .table(SESSION_TABLE)
            .update(
                {
                    "revoked_at": _iso(now),
                    "last_seen_at": _iso(now),
                    "access_token": None,
                    "refresh_token": None,
                }
            )
            .eq("marker_hash", marker_hash(clean_marker))
            .execute()
        )
        return True
    except Exception:
        return False


def cleanup_expired_sessions(retention_days: int = 7) -> None:
    """Best-effort maintenance; never block login if cleanup fails."""
    try:
        (
            _service_client()
            .rpc(
                "hm_cleanup_streamlit_auth_sessions",
                {"p_retention_days": max(int(retention_days), 1)},
            )
            .execute()
        )
    except Exception:
        pass
