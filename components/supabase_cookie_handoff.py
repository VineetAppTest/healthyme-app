from __future__ import annotations

import json
import os
from typing import Iterable

import streamlit as st


DEFAULT_COOKIE_TTL_SECONDS = 12 * 60 * 60


def _positive_int_secret(name: str, default: int, minimum: int) -> int:
    raw_value = os.environ.get(name)
    if raw_value is None:
        try:
            raw_value = st.secrets.get(name)
        except Exception:
            raw_value = None
    try:
        parsed = int(float(str(raw_value or default)))
    except (TypeError, ValueError):
        parsed = default
    return max(parsed, minimum)


def _cookie_ttl_seconds() -> int:
    return _positive_int_secret(
        "SUPABASE_BROWSER_SESSION_TTL_SECONDS",
        DEFAULT_COOKIE_TTL_SECONDS,
        5 * 60,
    )


def render_cookie_commit_handoff(
    *,
    marker: str,
    cookie_name: str,
    destination: str = "/",
) -> None:
    """Write one opaque first-party marker and open a fresh browser session.

    The caller must pass only a random opaque marker. Supabase access and refresh
    tokens must remain in the restricted server-side durable-session store.
    """
    clean_marker = str(marker or "").strip()
    clean_cookie_name = str(cookie_name or "").strip()
    clean_destination = str(destination or "/").strip() or "/"
    if not clean_marker or not clean_cookie_name:
        st.error("HealthyMe could not prepare the secure browser-session handoff.")
        return

    script = f"""
    <div id="hm-h13p1-cookie-status" style="font:600 0.9rem sans-serif;">
      Securing your browser session…
    </div>
    <script>
    (() => {{
      const cookieName = {json.dumps(clean_cookie_name)};
      const marker = {json.dumps(clean_marker)};
      const destination = {json.dumps(clean_destination)};
      const maxAge = {int(_cookie_ttl_seconds())};
      const attributes = [
        "Path=/",
        `Max-Age=${{maxAge}}`,
        "SameSite=Strict"
      ];
      if (window.location.protocol === "https:") {{
        attributes.push("Secure");
      }}
      document.cookie =
        `${{cookieName}}=${{encodeURIComponent(marker)}}; ${{attributes.join("; ")}}`;

      const written = document.cookie
        .split("; ")
        .some((entry) => entry.startsWith(`${{cookieName}}=`));

      const status = document.getElementById("hm-h13p1-cookie-status");
      if (!written) {{
        if (status) {{
          status.textContent =
            "HealthyMe could not confirm the browser marker. Please retry the login once.";
        }}
        return;
      }}

      if (status) {{
        status.textContent = "Secure browser marker confirmed. Continuing…";
      }}
      setTimeout(() => window.location.replace(destination), 180);
    }})();
    </script>
    """
    st.html(script, unsafe_allow_javascript=True)


def render_cookie_clear_handoff(
    *,
    cookie_names: Iterable[str],
    destination: str = "/Login",
) -> None:
    """Expire opaque HealthyMe browser markers and continue to Login."""
    clean_names = [
        str(name or "").strip()
        for name in cookie_names
        if str(name or "").strip()
    ]
    clean_destination = str(destination or "/Login").strip() or "/Login"

    script = f"""
    <div id="hm-h13p1-logout-status" style="font:600 0.9rem sans-serif;">
      Clearing the browser marker…
    </div>
    <script>
    (() => {{
      const cookieNames = {json.dumps(clean_names)};
      const destination = {json.dumps(clean_destination)};
      const attributes = [
        "Path=/",
        "Max-Age=0",
        "Expires=Thu, 01 Jan 1970 00:00:00 GMT",
        "SameSite=Strict"
      ];
      if (window.location.protocol === "https:") {{
        attributes.push("Secure");
      }}
      for (const cookieName of cookieNames) {{
        document.cookie = `${{cookieName}}=; ${{attributes.join("; ")}}`;
      }}
      const status = document.getElementById("hm-h13p1-logout-status");
      if (status) {{
        status.textContent = "Browser marker cleared. Returning to Login…";
      }}
      setTimeout(() => window.location.replace(destination), 180);
    }})();
    </script>
    """
    st.html(script, unsafe_allow_javascript=True)
