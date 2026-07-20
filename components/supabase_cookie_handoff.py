"""Browser-cookie handoff for HealthyMe Streamlit Supabase login.

H13D removes the asynchronous CookieManager read-back loop that could leave the
Login page permanently stuck on “Securing your HealthyMe session…”. A successful
login now commits the opaque marker in the browser and performs one full browser
reload. The new Streamlit session then reads the marker from ``st.context.cookies``
and restores the durable Supabase session.
"""

from __future__ import annotations

import json
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
HANDOFF_STARTED_AT_KEY = "_hm_supabase_cookie_handoff_started_at"
HANDOFF_RENDERED_KEY = "_hm_supabase_cookie_handoff_rendered"
HANDOFF_TIMEOUT_SECONDS = 20

HandoffStatus = Literal["not_pending", "waiting", "confirmed", "failed"]


def clear_cookie_handoff_state() -> None:
    for key in (
        HANDOFF_ARMED_KEY,
        HANDOFF_PENDING_KEY,
        HANDOFF_STARTED_AT_KEY,
        HANDOFF_RENDERED_KEY,
    ):
        st.session_state.pop(key, None)


def arm_cookie_handoff() -> None:
    """Arm before Supabase login so component-triggered reruns cannot lose state."""
    clear_cookie_handoff_state()
    st.session_state[HANDOFF_ARMED_KEY] = True


def cancel_cookie_handoff() -> None:
    clear_cookie_handoff_state()


def begin_cookie_handoff() -> bool:
    """Prepare the opaque browser marker for one browser-level commit/reload."""
    marker = str(
        st.session_state.get(SUPABASE_BROWSER_SESSION_ID_KEY) or ""
    ).strip()
    if not marker:
        return False

    st.session_state.pop(HANDOFF_ARMED_KEY, None)
    st.session_state[HANDOFF_PENDING_KEY] = marker
    st.session_state[HANDOFF_STARTED_AT_KEY] = time.time()
    st.session_state[HANDOFF_RENDERED_KEY] = False
    st.session_state[SUPABASE_BROWSER_COOKIE_WRITE_KEY] = False
    return True


def cookie_handoff_pending() -> bool:
    pending_marker = str(st.session_state.get(HANDOFF_PENDING_KEY) or "").strip()
    if pending_marker:
        return True

    # Recover when the login call itself was interrupted by a Streamlit rerun.
    if st.session_state.get(HANDOFF_ARMED_KEY):
        marker = str(
            st.session_state.get(SUPABASE_BROWSER_SESSION_ID_KEY) or ""
        ).strip()
        if marker:
            return begin_cookie_handoff()
    return False


def _render_cookie_commit_and_reload(marker: str) -> None:
    """Set the opaque marker and reload the parent browser after it commits.

    ``st.context.cookies`` is populated only from the initial browser request. A
    normal Streamlit script rerun is therefore insufficient. The full browser reload
    is intentional and occurs once immediately after a successful login.
    """
    cookie_name = json.dumps(SUPABASE_BROWSER_COOKIE_NAME)
    cookie_value = json.dumps(marker)
    ttl_seconds = int(_browser_session_ttl_seconds())
    secure_attribute = "; Secure" if _browser_cookie_is_secure() else ""

    components.html(
        f"""
        <script>
        (() => {{
          const cookieName = {cookie_name};
          const cookieValue = {cookie_value};
          const attributes = "Path=/; Max-Age={ttl_seconds}; SameSite=Strict{secure_attribute}";
          const cookieText = `${{cookieName}}=${{encodeURIComponent(cookieValue)}}; ${{attributes}}`;

          document.cookie = cookieText;
          try {{
            window.parent.document.cookie = cookieText;
          }} catch (error) {{
            // The component document is normally same-origin. Its cookie write
            // remains the fallback when parent-document access is restricted.
          }}

          let committed = document.cookie
            .split("; ")
            .some((row) => row.startsWith(`${{cookieName}}=`));
          try {{
            committed = committed || window.parent.document.cookie
              .split("; ")
              .some((row) => row.startsWith(`${{cookieName}}=`));
          }} catch (error) {{
            // Keep the component-document result.
          }}

          window.setTimeout(() => {{
            try {{
              window.parent.location.reload();
            }} catch (error) {{
              window.location.reload();
            }}
          }}, committed ? 700 : 1300);
        }})();
        </script>
        """,
        height=0,
        width=0,
    )


def process_cookie_handoff() -> Tuple[HandoffStatus, str]:
    """Commit the marker and wait for a full browser reload.

    This function deliberately does not use CookieManager ``get_all`` confirmation.
    That custom-component read-back was the source of the deployed H13C wait loop.
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
            "HealthyMe could not complete the secure browser handoff. Please sign in again.",
        )

    st.session_state[HANDOFF_RENDERED_KEY] = True
    st.session_state[SUPABASE_BROWSER_COOKIE_WRITE_KEY] = True
    _render_cookie_commit_and_reload(marker)
    return "waiting", "Securing your HealthyMe session…"
