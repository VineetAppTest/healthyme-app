from __future__ import annotations

import runpy
from pathlib import Path
from typing import Any

import streamlit as st


# Streamlit reruns reuse the same Python process. Always restore the process-level
# routing primitives before installing the current production wrapper.
_ROUTING_PRIMITIVES = {
    "Page": "_hm_h13r2_base_page",
    "navigation": "_hm_h13r2_base_navigation",
    "switch_page": "_hm_h13r2_base_switch_page",
}
for public_name, cache_name in _ROUTING_PRIMITIVES.items():
    current_callable = getattr(st, public_name)
    base_callable = getattr(st, cache_name, None)
    if base_callable is None:
        setattr(st, cache_name, current_callable)
    else:
        setattr(st, public_name, base_callable)


from native_bridge import root_authorization_ui as _router_authorization_ui  # noqa: E402
from native_bridge import root_authorization_ui_h13r7e as _root_authorization_ui  # noqa: E402


BUILD = "H13R8-login-timing-url-cleanup-v1"
ROLLBACK_BUILD = "H13R7E-meaningful-wellness-authorizer-v1"


def _native_identity_present() -> bool:
    try:
        return bool(st.user and st.user.is_logged_in)
    except Exception:
        return False


def _instrument_authorizer_html(document: str) -> str:
    """Add visible stage timing without changing Supabase/OIDC operations."""
    if not isinstance(document, str) or "id=\"hm-form\"" not in document:
        return document

    document = document.replace(
        ".hm-progress-copy { margin-top:7px;color:var(--hm-muted);font-size:13px; }",
        ".hm-progress-copy { margin-top:7px;color:var(--hm-muted);font-size:13px; }\n"
        "      .hm-progress-elapsed { margin-top:10px;color:#6f7a74;font-size:11px;font-weight:700; }",
        1,
    )
    document = document.replace(
        '<div class="hm-progress-title">Signing you in securely…</div>\n'
        '            <div class="hm-progress-copy">HealthyMe is confirming your identity and access.</div>',
        '<div id="hm-progress-title" class="hm-progress-title">Checking your credentials…</div>\n'
        '            <div id="hm-progress-copy" class="hm-progress-copy">Supabase is confirming your account.</div>\n'
        '            <div id="hm-progress-elapsed" class="hm-progress-elapsed">Elapsed: 0 seconds</div>',
        1,
    )
    document = document.replace(
        "      let busy = false;",
        "      let busy = false;\n"
        "      let loginStartedAt = 0;\n"
        "      let elapsedTimer = null;\n"
        "      const progressTitle = document.getElementById(\"hm-progress-title\");\n"
        "      const progressCopy = document.getElementById(\"hm-progress-copy\");\n"
        "      const progressElapsed = document.getElementById(\"hm-progress-elapsed\");\n\n"
        "      function setProgressStage(title, copy) {\n"
        "        if (progressTitle) progressTitle.textContent = title;\n"
        "        if (progressCopy) progressCopy.textContent = copy;\n"
        "      }\n\n"
        "      function updateElapsed() {\n"
        "        if (!loginStartedAt || !progressElapsed) return;\n"
        "        const seconds = Math.max(0, Math.round((performance.now() - loginStartedAt) / 1000));\n"
        "        progressElapsed.textContent = `Elapsed: ${seconds} second${seconds === 1 ? \"\" : \"s\"}`;\n"
        "      }\n\n"
        "      function startElapsedTimer() {\n"
        "        loginStartedAt = performance.now();\n"
        "        updateElapsed();\n"
        "        if (elapsedTimer) clearInterval(elapsedTimer);\n"
        "        elapsedTimer = setInterval(updateElapsed, 1000);\n"
        "      }\n\n"
        "      function stopElapsedTimer() {\n"
        "        updateElapsed();\n"
        "        if (elapsedTimer) clearInterval(elapsedTimer);\n"
        "        elapsedTimer = null;\n"
        "      }\n\n"
        "      function cleanVisibleAuthorizationUrl() {\n"
        "        try {\n"
        "          const cleanUrl = new URL(clientLoginUrl, window.top.location.origin);\n"
        "          window.top.history.replaceState({}, \"\", cleanUrl.pathname + cleanUrl.search + cleanUrl.hash);\n"
        "        } catch (_error) {\n"
        "          // The server-side post-auth cleanup remains the fallback.\n"
        "        }\n"
        "      }",
        1,
    )
    document = document.replace(
        "      async function approveAndContinue() {\n"
        "        const {data:details,error:detailsError} =",
        "      async function approveAndContinue() {\n"
        "        setProgressStage(\"Validating secure access…\", \"HealthyMe is checking the authorization request.\");\n"
        "        const {data:details,error:detailsError} =",
        1,
    )
    document = document.replace(
        "        if (details?.redirect_url && !(\"authorization_id\" in details)) {\n"
        "          redirectTop(details.redirect_url);",
        "        if (details?.redirect_url && !(\"authorization_id\" in details)) {\n"
        "          setProgressStage(\"Opening your dashboard…\", \"Your identity and access have been confirmed.\");\n"
        "          stopElapsedTimer();\n"
        "          redirectTop(details.redirect_url);",
        1,
    )
    document = document.replace(
        "        const {data,error} = await supabase.auth.oauth.approveAuthorization(authorizationId);",
        "        setProgressStage(\"Authorizing HealthyMe access…\", \"Applying your approved Member or Admin access.\");\n"
        "        const {data,error} = await supabase.auth.oauth.approveAuthorization(authorizationId);",
        1,
    )
    document = document.replace(
        "        if (error) throw error;\n"
        "        redirectTop(data.redirect_url);\n"
        "      }",
        "        if (error) throw error;\n"
        "        setProgressStage(\"Opening your dashboard…\", \"Your identity and access have been confirmed.\");\n"
        "        stopElapsedTimer();\n"
        "        redirectTop(data.redirect_url);\n"
        "      }",
        1,
    )
    document = document.replace(
        "        busy = true;\n"
        "        signInButton.disabled = true;\n"
        "        showMessage(\"Confirming your identity…\", \"info\");",
        "        busy = true;\n"
        "        signInButton.disabled = true;\n"
        "        startElapsedTimer();\n"
        "        setProgressStage(\"Checking your credentials…\", \"Supabase is confirming your account.\");\n"
        "        showMessage(\"Confirming your identity…\", \"info\");",
        1,
    )
    document = document.replace(
        "          showMessage(error.message || \"Unable to sign in. Please check your details.\", \"error\");\n"
        "          busy = false;",
        "          stopElapsedTimer();\n"
        "          showMessage(error.message || \"Unable to sign in. Please check your details.\", \"error\");\n"
        "          busy = false;",
        1,
    )
    document = document.replace(
        "        showProgress();\n"
        "        try {",
        "        cleanVisibleAuthorizationUrl();\n"
        "        setProgressStage(\"Completing secure authorization…\", \"HealthyMe is preparing your protected application access.\");\n"
        "        showProgress();\n"
        "        try {",
        1,
    )
    document = document.replace(
        "          loginPanel.style.display = \"block\";\n"
        "          progressPanel.style.display = \"none\";",
        "          stopElapsedTimer();\n"
        "          loginPanel.style.display = \"block\";\n"
        "          progressPanel.style.display = \"none\";",
        1,
    )
    return document


# Cache the accepted H13R7E authorizer once, then reinstall the production wrapper
# on every rerun.
_BASE_AUTHORIZER = getattr(
    _root_authorization_ui,
    "_hm_h13r8_base_render_root_authorization_ui",
    None,
)
if _BASE_AUTHORIZER is None:
    _BASE_AUTHORIZER = _root_authorization_ui.render_root_authorization_ui
    _root_authorization_ui._hm_h13r8_base_render_root_authorization_ui = (
        _BASE_AUTHORIZER
    )
else:
    _root_authorization_ui.render_root_authorization_ui = _BASE_AUTHORIZER


def _render_root_authorization_ui_for_native_router(authorization_id: str) -> None:
    if _native_identity_present():
        # The authorization_id is one-time OAuth state. Clear it without an explicit
        # st.rerun, then let the accepted role router select Member/Admin normally.
        if authorization_id:
            st.query_params.clear()
        return

    original_html = st.html

    def _timed_html(body: Any, *args: Any, **kwargs: Any) -> Any:
        if isinstance(body, str):
            body = _instrument_authorizer_html(body)
        return original_html(body, *args, **kwargs)

    st.html = _timed_html
    try:
        _BASE_AUTHORIZER(authorization_id)
    finally:
        st.html = original_html


_root_authorization_ui.render_root_authorization_ui = (
    _render_root_authorization_ui_for_native_router
)

# The accepted Gate 4/full-member runtime imports the legacy authorizer module
# directly. Point it at the H13R8 wrapper before the production runtime is compiled.
_router_authorization_ui.render_root_authorization_ui = (
    _render_root_authorization_ui_for_native_router
)

# Do not wrap st.navigation for callback cleanup. Earlier navigation wrapping touched
# page registration and caused duplicate URL-path failures. The accepted role router
# remains responsible for selecting the canonical Member/Admin page.

CUTOVER_ENTRY = (
    Path(__file__).resolve().parent
    / "production_cutover"
    / "production_live_cutover_app.py"
)

runpy.run_path(
    str(CUTOVER_ENTRY),
    run_name="__hm_h13r8_login_timing_url_cleanup__",
)
