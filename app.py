import json
import time

import streamlit as st

from components.admin_role_model import is_admin_role
from components.auth_mode import get_auth_mode, supabase_auth_enabled
from components.auth_session import clear_app_session_for_logout
from components.supabase_auth_session import (
    SUPABASE_BROWSER_COOKIE_NAME,
    SUPABASE_BROWSER_SESSION_ID_KEY,
    clear_supabase_auth_session,
    restore_supabase_login_from_session,
    sign_in_with_supabase,
    supabase_auth_configured,
)
from components.supabase_cookie_handoff import (
    render_cookie_clear_handoff,
    render_cookie_commit_handoff,
)
from components.ui_common import apply_luxe_theme, inject_global_styles


ROUTER_BUILD = "H13P1-direct-supabase-cookie-handoff-v2-inline"


st.set_page_config(
    page_title="HealthyMe",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="collapsed",
)
inject_global_styles()
apply_luxe_theme()


def _native_cookie_value(name: str) -> str:
    try:
        return str(st.context.cookies.get(name) or "").strip()
    except Exception:
        return ""


def _resolved_supabase_session() -> bool:
    return bool(
        st.session_state.get("logged_in")
        and st.session_state.get("_hm_auth_role_resolved")
        and (
            st.session_state.get("auth_provider") == "supabase"
            or st.session_state.get("auth_login_method") == "supabase"
        )
    )


def _role_destination():
    return admin_page if is_admin_role(st.session_state.get("user_role")) else member_page


def _render_login_handoff() -> None:
    marker = str(
        st.session_state.get(SUPABASE_BROWSER_SESSION_ID_KEY) or ""
    ).strip()
    if not marker or not _resolved_supabase_session():
        st.error("HealthyMe created no usable secure session after Supabase sign-in.")
        st.stop()

    st.title("Securing your HealthyMe session")
    st.info(
        "HealthyMe is committing the opaque browser marker and opening a fresh "
        "session to prove that refresh restoration works."
    )
    st.caption("No password or Supabase token is written to the browser.")
    render_cookie_commit_handoff(
        marker=marker,
        cookie_name=SUPABASE_BROWSER_COOKIE_NAME,
        destination="/",
    )
    st.stop()


def _perform_logout() -> None:
    st.title("Signing out securely")
    st.info(
        "HealthyMe is revoking the server-side session and clearing the browser marker."
    )

    clear_ok = False
    try:
        clear_ok = bool(clear_supabase_auth_session())
    except Exception:
        clear_ok = False

    clear_app_session_for_logout(
        feedback_level="success" if clear_ok else "warning",
        feedback_message=(
            "You have been signed out securely."
            if clear_ok
            else "The local session was cleared. Close this tab before switching users."
        ),
    )
    render_cookie_clear_handoff(
        cookie_names=(
            SUPABASE_BROWSER_COOKIE_NAME,
            "hm_supabase_sid_v1",
        ),
        destination="/Login",
    )
    st.stop()


def _login_page() -> None:
    st.title("HealthyMe secure login")
    st.caption(
        "H13P1 proof of concept: direct Supabase sign-in with a first-party "
        "opaque session marker. No access or refresh token is stored in the browser."
    )
    st.code(ROUTER_BUILD)

    if get_auth_mode() != "supabase":
        st.error(
            "This isolated proof of concept requires AUTH_MODE='supabase' "
            "in the temporary Streamlit app."
        )
        st.stop()

    if not supabase_auth_configured():
        st.error(
            "Supabase session durability is not configured for this temporary app. "
            "Add the Supabase URL, anon key and server-only service-role key."
        )
        st.stop()

    existing_error = str(st.session_state.pop("auth_error", "") or "").strip()
    if existing_error:
        st.error(existing_error)

    with st.form("h13p1_login_form", clear_on_submit=False):
        email = st.text_input("Email", key="h13p1_login_email")
        password = st.text_input(
            "Password",
            type="password",
            key="h13p1_login_password",
        )
        submitted = st.form_submit_button(
            "Continue with Supabase",
            type="primary",
            use_container_width=True,
        )

    if submitted:
        ok, message = sign_in_with_supabase(email, password)
        if not ok:
            st.error(message)
            st.stop()
        st.session_state["_hm_h13p1_login_started_at"] = time.time()

        # Do not navigate to another Streamlit page before the browser cookie is
        # committed. The earlier v1 navigation could update the URL while leaving
        # the previous callable page rendered. Commit the first-party marker in the
        # same successful login execution, then open a fresh root session.
        _render_login_handoff()


def _admin_page() -> None:
    st.title("Admin Dashboard — H13P1 router test")
    st.success(
        "The direct Supabase session and HealthyMe Admin role were restored "
        "before this page ran."
    )
    col1, col2, col3 = st.columns(3)
    col1.metric("Opaque browser marker", "Present")
    col2.metric("HealthyMe role", "Admin")
    col3.metric(
        "Restore",
        f"{st.session_state.get('_hm_h13p1_restore_ms', '—')} ms",
    )
    st.code(ROUTER_BUILD)
    if st.button("Logout", key="h13p1_admin_logout"):
        _perform_logout()


def _member_page() -> None:
    st.title("Member Home — H13P1 router test")
    st.success(
        "The direct Supabase session and HealthyMe Member role were restored "
        "before this page ran."
    )
    col1, col2, col3 = st.columns(3)
    col1.metric("Opaque browser marker", "Present")
    col2.metric("HealthyMe role", "Member")
    col3.metric(
        "Restore",
        f"{st.session_state.get('_hm_h13p1_restore_ms', '—')} ms",
    )
    st.code(ROUTER_BUILD)
    if st.button("Logout", key="h13p1_member_logout"):
        _perform_logout()


def _diagnostics_page() -> None:
    cookie_value = _native_cookie_value(SUPABASE_BROWSER_COOKIE_NAME)
    role = str(
        st.session_state.get("user_role")
        or st.session_state.get("role")
        or "none"
    ).strip().lower()
    safe_snapshot = {
        "router_build": ROUTER_BUILD,
        "auth_mode": get_auth_mode(),
        "opaque_cookie_present": bool(cookie_value),
        "opaque_cookie_length": len(cookie_value),
        "healthyme_logged_in": bool(st.session_state.get("logged_in")),
        "healthyme_role_resolved": bool(
            st.session_state.get("_hm_auth_role_resolved")
        ),
        "healthyme_role": role,
        "restore_ms": st.session_state.get("_hm_h13p1_restore_ms"),
        "tokens_in_url": False,
        "local_storage_used": False,
    }

    st.title("HealthyMe H13P1 authentication diagnostics")
    st.caption(
        "Safe indicators only. This page does not display cookie values, passwords, "
        "access tokens, refresh tokens, email addresses or user IDs."
    )
    col1, col2, col3 = st.columns(3)
    col1.metric("Opaque cookie", "Present" if cookie_value else "Absent")
    col2.metric(
        "HealthyMe session",
        "Present" if safe_snapshot["healthyme_logged_in"] else "Absent",
    )
    col3.metric("HealthyMe role", role.title())
    st.code(json.dumps(safe_snapshot, indent=2, sort_keys=True), language="json")


def _root_page() -> None:
    st.empty()


root_page = st.Page(
    _root_page,
    title="HealthyMe",
    icon="🌿",
    default=True,
)
login_page = st.Page(
    _login_page,
    title="Login",
    url_path="Login",
)
admin_page = st.Page(
    _admin_page,
    title="Admin Dashboard",
    url_path="Admin_Dashboard",
)
member_page = st.Page(
    _member_page,
    title="Member Home",
    url_path="Member_Home",
)
diagnostics_page = st.Page(
    _diagnostics_page,
    title="Auth Diagnostics",
    url_path="Auth_Diagnostics",
)

selected_page = st.navigation(
    [
        root_page,
        login_page,
        admin_page,
        member_page,
        diagnostics_page,
    ],
    position="hidden",
)

restore_started = time.perf_counter()
restored = _resolved_supabase_session()
cookie_present = bool(_native_cookie_value(SUPABASE_BROWSER_COOKIE_NAME))

if (
    not restored
    and cookie_present
    and supabase_auth_enabled()
):
    try:
        restored = bool(restore_supabase_login_from_session())
    except Exception:
        restored = False

st.session_state["_hm_h13p1_restore_ms"] = round(
    (time.perf_counter() - restore_started) * 1000,
    1,
)

if selected_page is not diagnostics_page:
    if restored:
        destination = _role_destination()
        if selected_page in (root_page, login_page):
            st.switch_page(destination)
        if destination is admin_page and selected_page is member_page:
            st.switch_page(admin_page)
        if destination is member_page and selected_page is admin_page:
            st.switch_page(member_page)
    else:
        if selected_page in (admin_page, member_page) and cookie_present:
            st.session_state["auth_error"] = (
                "The opaque browser marker reached HealthyMe, but the server-side "
                "Supabase session could not be restored."
            )
            st.switch_page(diagnostics_page)
        if selected_page is not login_page:
            st.switch_page(login_page)

selected_page.run()
