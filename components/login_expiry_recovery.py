from __future__ import annotations

from typing import Any

import streamlit as st


_RECOVERY_MESSAGE_OLD = (
    'showMessage("This secure login request has expired. Please start again.", "error");'
)
_RECOVERY_MESSAGE_NEW = (
    'showMessage("Your secure sign-in request has expired. HealthyMe is starting a fresh login.", "info");\n'
    '            window.setTimeout(() => redirectTop(clientLoginUrl), 900);'
)


def install_login_expiry_recovery() -> None:
    """Recover stale Supabase authorization pages without changing the login flow.

    The accepted authorizer remains the source of truth. This installer changes only
    the expired-request presentation: stale requests automatically return to the
    clean HealthyMe Login URL instead of leaving the user on a dead-end error.
    """

    from native_bridge import root_authorization_ui_h13r7e as authorization_ui

    current = authorization_ui.render_root_authorization_ui
    if getattr(current, "_hm_login_expiry_recovery", False):
        authorization_ui._hm_h13r9_base_render_root_authorization_ui = current
        return

    base = getattr(
        authorization_ui,
        "_hm_login_expiry_recovery_base",
        current,
    )
    authorization_ui._hm_login_expiry_recovery_base = base

    def render_with_expiry_recovery(authorization_id: str) -> None:
        client_login_url = authorization_ui._secret(
            "AUTH_CLIENT_LOGIN_URL",
            authorization_ui.DEFAULT_CLIENT_LOGIN_URL,
        )

        if not str(authorization_id or "").strip():
            st.info(
                "Your secure sign-in request has expired. HealthyMe is starting a fresh login."
            )
            st.html(
                f"""
                <script>
                (() => {{
                  const destination = {client_login_url!r};
                  const redirect = () => {{
                    try {{ window.top.location.replace(destination); }}
                    catch (_error) {{ window.location.replace(destination); }}
                  }};
                  window.setTimeout(redirect, 900);
                }})();
                </script>
                """,
                unsafe_allow_javascript=True,
            )
            st.link_button(
                "Start fresh HealthyMe login",
                client_login_url,
                use_container_width=True,
            )
            st.stop()

        original_html = st.html

        def html_with_stale_recovery(body: Any, *args: Any, **kwargs: Any):
            if isinstance(body, str) and _RECOVERY_MESSAGE_OLD in body:
                body = body.replace(
                    _RECOVERY_MESSAGE_OLD,
                    _RECOVERY_MESSAGE_NEW,
                    1,
                )
            return original_html(body, *args, **kwargs)

        st.html = html_with_stale_recovery
        try:
            base(authorization_id)
        finally:
            st.html = original_html

    render_with_expiry_recovery._hm_login_expiry_recovery = True
    authorization_ui.render_root_authorization_ui = render_with_expiry_recovery
    # app.py intentionally caches this exact callable across Streamlit reruns.
    authorization_ui._hm_h13r9_base_render_root_authorization_ui = (
        render_with_expiry_recovery
    )
