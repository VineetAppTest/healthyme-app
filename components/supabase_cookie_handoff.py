"""Confirmed browser-cookie handoff for Streamlit Supabase login.

The extra-streamlit-components cookie API is asynchronous. A successful Supabase
login must therefore remain on the Login page until the browser confirms that the
opaque HealthyMe session marker was actually written. Only the marker is stored in
the browser; Supabase access and refresh tokens remain in the server-side registry.
"""

from __future__ import annotations

import datetime
import time
from typing import Literal, Tuple

import streamlit as st

from components.supabase_auth_session import (
    SUPABASE_BROWSER_COOKIE_NAME,
    SUPABASE_BROWSER_COOKIE_WRITE_KEY,
    SUPABASE_BROWSER_SESSION_ID_KEY,
    _browser_cookie_is_secure,
    _browser_session_ttl_seconds,
)

HANDOFF_PENDING_KEY = "_hm_supabase_cookie_handoff_pending"
HANDOFF_PHASE_KEY = "_hm_supabase_cookie_handoff_phase"
HANDOFF_STARTED_AT_KEY = "_hm_supabase_cookie_handoff_started_at"
HANDOFF_MANAGER_KEY = "_hm_supabase_cookie_manager_v3"
HANDOFF_TIMEOUT_SECONDS = 20

HandoffStatus = Literal["not_pending", "waiting", "confirmed", "failed"]


def _manager():
    """Create the browser component only once for the current Streamlit session."""
    manager = st.session_state.get(HANDOFF_MANAGER_KEY)
    if manager is not None:
        return manager

    import extra_streamlit_components as stx

    manager = stx.CookieManager(key="hm_supabase_cookie_manager_v3")
    st.session_state[HANDOFF_MANAGER_KEY] = manager
    return manager


def clear_cookie_handoff_state() -> None:
    for key in (
        HANDOFF_PENDING_KEY,
        HANDOFF_PHASE_KEY,
        HANDOFF_STARTED_AT_KEY,
    ):
        st.session_state.pop(key, None)


def begin_cookie_handoff() -> bool:
    """Start the two-phase cookie write and confirmation process."""
    marker = str(
        st.session_state.get(SUPABASE_BROWSER_SESSION_ID_KEY) or ""
    ).strip()
    if not marker:
        return False

    st.session_state[HANDOFF_PENDING_KEY] = marker
    st.session_state[HANDOFF_PHASE_KEY] = "write"
    st.session_state[HANDOFF_STARTED_AT_KEY] = time.time()
    st.session_state[SUPABASE_BROWSER_COOKIE_WRITE_KEY] = False
    return True


def cookie_handoff_pending() -> bool:
    return bool(str(st.session_state.get(HANDOFF_PENDING_KEY) or "").strip())


def process_cookie_handoff() -> Tuple[HandoffStatus, str]:
    """Write the opaque marker, then confirm it from the browser component.

    Component calls may trigger Streamlit reruns. The phase is persisted before a
    component invocation so the next run continues safely instead of repeating the
    login or routing before the browser has committed the cookie.
    """
    marker = str(st.session_state.get(HANDOFF_PENDING_KEY) or "").strip()
    if not marker:
        return "not_pending", ""

    try:
        started_at = float(st.session_state.get(HANDOFF_STARTED_AT_KEY) or 0)
    except (TypeError, ValueError):
        started_at = 0
    if not started_at:
        started_at = time.time()
        st.session_state[HANDOFF_STARTED_AT_KEY] = started_at

    if time.time() - started_at > HANDOFF_TIMEOUT_SECONDS:
        clear_cookie_handoff_state()
        return (
            "failed",
            "HealthyMe could not confirm the secure browser session. Please sign in again.",
        )

    manager = _manager()
    phase = str(st.session_state.get(HANDOFF_PHASE_KEY) or "write")
    key_suffix = marker[:12]

    if phase == "write":
        # Persist the next phase before invoking the browser component because the
        # component can itself trigger a Streamlit rerun.
        st.session_state[HANDOFF_PHASE_KEY] = "confirm"
        manager.set(
            SUPABASE_BROWSER_COOKIE_NAME,
            marker,
            key=f"hm_supabase_handoff_set_{key_suffix}",
            path="/",
            expires_at=datetime.datetime.now() + datetime.timedelta(
                seconds=_browser_session_ttl_seconds()
            ),
            secure=_browser_cookie_is_secure(),
            same_site="strict",
        )
        return "waiting", "Securing your HealthyMe session…"

    cookies = manager.get_all(key=f"hm_supabase_handoff_confirm_{key_suffix}") or {}
    confirmed_marker = str(cookies.get(SUPABASE_BROWSER_COOKIE_NAME) or "").strip()
    if confirmed_marker == marker:
        clear_cookie_handoff_state()
        st.session_state[SUPABASE_BROWSER_COOKIE_WRITE_KEY] = True
        return "confirmed", "Secure session confirmed."

    return "waiting", "Securing your HealthyMe session…"
