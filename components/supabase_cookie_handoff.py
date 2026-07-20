"""Reliable browser-cookie handoff for HealthyMe Streamlit Supabase login.

H13E keeps the durable Supabase session introduced in H13C, but replaces H13D's
plain iframe cookie write. The component iframe can reload the parent page, but it
cannot reliably create an application-domain cookie. H13E therefore uses the
CookieManager component only to commit the opaque marker, then performs one full
browser reload. No CookieManager read-back loop is used.
"""

from __future__ import annotations

import datetime
import time
from typing import Literal, Tuple

import streamlit as st
import streamlit.components.v1 as components

from components.supabase_auth_session import (
    SUPABASE_BROWSER_COOKIE_NAME,
    SUPABASE_BROWSER_COOKIE_WRITE_KEY,
    SUPABASE_BROWSER_SESSION_ID_KEY,
    _browser_cookie_is_secure,
    _browser_session_ttl_seconds,
)

HANDOFF_ARMED_KEY = "_hm_supabase_cookie_handoff_armed"
HANDOFF_PENDING_KEY = "_hm_supabase_cookie_handoff_pending"
HANDOFF_PHASE_KEY = "_hm_supabase_cookie_handoff_phase"
HANDOFF_STARTED_AT_KEY = "_hm_supabase_cookie_handoff_started_at"
HANDOFF_MANAGER_KEY = "_hm_supabase_cookie_manager_v4"
HANDOFF_TIMEOUT_SECONDS = 30

HandoffStatus = Literal["not_pending", "waiting", "confirmed", "failed"]


def _manager():
    """Create one CookieManager instance for the active Streamlit session."""
    manager = st.session_state.get(HANDOFF_MANAGER_KEY)
    if manager is not None:
        return manager

    import extra_streamlit_components as stx

    manager = stx.CookieManager(key="hm_supabase_cookie_manager_v4")
    st.session_state[HANDOFF_MANAGER_KEY] = manager
    return manager


def clear_cookie_handoff_state() -> None:
    for key in (
        HANDOFF_ARMED_KEY,
        HANDOFF_PENDING_KEY,
        HANDOFF_PHASE_KEY,
        HANDOFF_STARTED_AT_KEY,
    ):
        st.session_state.pop(key, None)


def arm_cookie_handoff() -> None:
    """Arm before Supabase login so a component rerun cannot lose the handoff."""
    clear_cookie_handoff_state()
    st.session_state[HANDOFF_ARMED_KEY] = True


def cancel_cookie_handoff() -> None:
    clear_cookie_handoff_state()


def begin_cookie_handoff() -> bool:
    """Prepare the opaque marker for CookieManager commit and browser reload."""
    marker = str(
        st.session_state.get(SUPABASE_BROWSER_SESSION_ID_KEY) or ""
    ).strip()
    if not marker:
        return False

    st.session_state.pop(HANDOFF_ARMED_KEY, None)
    st.session_state[HANDOFF_PENDING_KEY] = marker
    st.session_state[HANDOFF_PHASE_KEY] = "commit"
    st.session_state[HANDOFF_STARTED_AT_KEY] = time.time()
    st.session_state[SUPABASE_BROWSER_COOKIE_WRITE_KEY] = False
    return True


def cookie_handoff_pending() -> bool:
    pending_marker = str(st.session_state.get(HANDOFF_PENDING_KEY) or "").strip()
    if pending_marker:
        return True

    # CookieManager may rerun the script from inside the login call. Recover the
    # newly created durable marker instead of returning to the credential form.
    if st.session_state.get(HANDOFF_ARMED_KEY):
        marker = str(
            st.session_state.get(SUPABASE_BROWSER_SESSION_ID_KEY) or ""
        ).strip()
        if marker:
            return begin_cookie_handoff()
    return False


def _render_parent_reload(delay_ms: int) -> None:
    """Reload the top-level browser so ``st.context.cookies`` sees the marker."""
    safe_delay = max(int(delay_ms), 500)
    components.html(
        f"""
        <script>
        window.setTimeout(() => {{
          try {{
            window.parent.location.reload();
          }} catch (error) {{
            window.location.reload();
          }}
        }}, {safe_delay});
        </script>
        """,
        height=0,
        width=0,
    )


def process_cookie_handoff() -> Tuple[HandoffStatus, str]:
    """Commit through CookieManager, then force one initial browser request.

    The phase is saved before the CookieManager call because that component may
    trigger a Streamlit rerun. Both the same run and the component-rerun path render
    a browser reload, so the flow cannot depend on synchronous component return.
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
            "HealthyMe could not commit the secure browser session. Please sign in again.",
        )

    phase = str(st.session_state.get(HANDOFF_PHASE_KEY) or "commit")

    if phase == "commit":
        # Save the next phase first. CookieManager.set can initiate a Streamlit rerun
        # before this function reaches its next Python statement.
        st.session_state[HANDOFF_PHASE_KEY] = "reload"
        try:
            _manager().set(
                SUPABASE_BROWSER_COOKIE_NAME,
                marker,
                key=f"hm_supabase_h13e_set_{marker[:12]}",
                path="/",
                expires_at=datetime.datetime.now() + datetime.timedelta(
                    seconds=_browser_session_ttl_seconds()
                ),
                secure=_browser_cookie_is_secure(),
                same_site="strict",
            )
        except Exception:
            clear_cookie_handoff_state()
            return (
                "failed",
                "HealthyMe could not write the secure browser marker. Please sign in again.",
            )

        st.session_state[SUPABASE_BROWSER_COOKIE_WRITE_KEY] = True
        # This covers the case where CookieManager.set returns without triggering a
        # rerun. The delay gives the browser component time to commit the cookie.
        _render_parent_reload(2200)
        return "waiting", "Securing your HealthyMe session…"

    # This is the expected path when CookieManager.set triggered a component rerun.
    # At this point the browser has already processed the set request; reload shortly.
    st.session_state[SUPABASE_BROWSER_COOKIE_WRITE_KEY] = True
    _render_parent_reload(900)
    return "waiting", "Securing your HealthyMe session…"
