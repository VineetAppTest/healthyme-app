import json
import time

import streamlit as st

from components.admin_role_model import is_admin_role
from components.auth_mode import auth0_enabled, supabase_auth_enabled
from components.auth_session import restore_login_from_token
from components.supabase_auth_session import restore_supabase_login_from_session
from components.ui_common import apply_luxe_theme, inject_global_styles


ROUTER_BUILD = "H13O2-st-navigation-poc-v10-stable-switch"
BOOTSTRAP_QUERY_KEY = "hm_bootstrap"
BOOTSTRAP_ATTEMPT_QUERY_KEY = "hm_bootstrap_try"
BOOTSTRAP_MAX_ATTEMPTS = 3
BOOTSTRAP_DELAYS_MS = (200, 600, 1200)


st.set_page_config(
    page_title="HealthyMe",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="collapsed",
)
inject_global_styles()
apply_luxe_theme()


def _query_value(name: str) -> str:
    try:
        return str(st.query_params.get(name) or "").strip()
    except Exception:
        return ""


def _query_int(name: str, default: int = 0) -> int:
    try:
        return max(0, int(_query_value(name) or default))
    except (TypeError, ValueError):
        return default


def _native_identity_present() -> bool:
    try:
        return bool(st.user.is_logged_in)
    except Exception:
        return False


def _auth_cookie_present() -> bool:
    try:
        return "_streamlit_user" in dict(st.context.cookies)
    except Exception:
        return False


def _root_route() -> None:
    """The central router redirects root before this placeholder normally runs."""
    st.empty()


def _router_logout_button(key: str) -> None:
    """Run Streamlit's native logout directly in the button event."""
    if st.button("Logout", key=key, use_container_width=False):
        st.logout()
        st.stop()


def _admin_router_test_page() -> None:
    """Minimal protected Admin page with no legacy page guard or UI side effects."""
    role = st.session_state.get("user_role")
    if not (
        st.session_state.get("logged_in")
        and st.session_state.get("_hm_auth_role_resolved")
        and is_admin_role(role)
    ):
        st.error("The central router did not restore an Admin session.")
        st.stop()

    st.title("Admin Dashboard — H13O2 router test")
    st.success("Admin OIDC identity and HealthyMe role were restored before this page ran.")
    st.caption(
        "This deliberately lightweight page excludes the legacy Admin Dashboard guard, "
        "logout bar and navigation code so the central router can be tested independently."
    )
    col1, col2, col3 = st.columns(3)
    col1.metric("Native OIDC identity", "Present")
    col2.metric("HealthyMe role", "Admin")
    col3.metric(
        "Router restore",
        f"{st.session_state.get('_hm_router_restore_ms', '—')} ms",
    )
    st.code(ROUTER_BUILD)
    _router_logout_button("h13o2_admin_logout")


def _member_router_test_page() -> None:
    """Minimal protected Member page with no legacy page guard or UI side effects."""
    role = st.session_state.get("user_role")
    if not (
        st.session_state.get("logged_in")
        and st.session_state.get("_hm_auth_role_resolved")
        and not is_admin_role(role)
    ):
        st.error("The central router did not restore a Member session.")
        st.stop()

    st.title("Member Home — H13O2 router test")
    st.success("Member OIDC identity and HealthyMe role were restored before this page ran.")
    st.caption(
        "This deliberately lightweight page excludes the legacy Member Home guard, "
        "page defaults and UI code so the central router can be tested independently."
    )
    col1, col2, col3 = st.columns(3)
    col1.metric("Native OIDC identity", "Present")
    col2.metric("HealthyMe role", "Member")
    col3.metric(
        "Router restore",
        f"{st.session_state.get('_hm_router_restore_ms', '—')} ms",
    )
    st.code(ROUTER_BUILD)
    _router_logout_button("h13o2_member_logout")


def _show_role_restore_recovery() -> None:
    """Keep an authenticated user out of Login when only role restoration is delayed."""
    st.title("HealthyMe is restoring your access")
    st.warning(
        "Your secure sign-in is still active, but HealthyMe could not finish restoring "
        "your access profile. This is a temporary restoration issue, not a logout."
    )
    st.caption(
        "Use Retry access once. Do not sign in again while this message is displayed."
    )
    attempts = st.session_state.get("_hm_role_restore_attempts", "—")
    st.metric("Automatic role-lookup attempts", attempts)
    if st.button("Retry access", type="primary"):
        st.rerun()
    if st.button("Open safe diagnostics"):
        st.switch_page(auth_diagnostics_page)
    st.stop()


def _restart_as_new_browser_session(
    target_role: str,
    *,
    attempt: int,
    message: str = "HealthyMe is restoring your secure session…",
) -> None:
    """Start a fresh browser session so Streamlit rereads the identity cookie.

    The attempt number is carried in the URL, so bounded retries survive the new
    WebSocket session without relying on Session State.
    """
    safe_attempt = max(1, min(int(attempt), BOOTSTRAP_MAX_ATTEMPTS))
    delay_ms = BOOTSTRAP_DELAYS_MS[safe_attempt - 1]
    destination = (
        f"/?{BOOTSTRAP_QUERY_KEY}={target_role}"
        f"&{BOOTSTRAP_ATTEMPT_QUERY_KEY}={safe_attempt}"
    )
    st.info(message)
    st.html(
        (
            "<script>"
            f"setTimeout(() => window.location.replace({json.dumps(destination)}), "
            f"{delay_ms});"
            "</script>"
        ),
        unsafe_allow_javascript=True,
    )
    st.caption("The page will continue automatically.")
    st.stop()


root_page = st.Page(
    _root_route,
    title="HealthyMe",
    icon="🌿",
    default=True,
)
login_page = st.Page(
    "pages/01_Login.py",
    title="Login",
    url_path="Login",
)
admin_page = st.Page(
    _admin_router_test_page,
    title="Admin Dashboard",
    url_path="Admin_Dashboard",
)
member_page = st.Page(
    _member_router_test_page,
    title="Member Home",
    url_path="Member_Home",
)
consent_page = st.Page(
    "pages/00_OAuth_Consent.py",
    title="OAuth Consent",
    url_path="OAuth_Consent",
)
native_logout_page = st.Page(
    "pages/00_Native_Logout.py",
    title="Native Logout",
    url_path="Native_Logout",
)
auth_diagnostics_page = st.Page(
    "pages/00_Auth_Diagnostics.py",
    title="Auth Diagnostics",
    url_path="Auth_Diagnostics",
)

selected_page = st.navigation(
    [
        root_page,
        login_page,
        admin_page,
        member_page,
        consent_page,
        native_logout_page,
        auth_diagnostics_page,
    ],
    position="hidden",
)

restore_started = time.perf_counter()
restored = False

if supabase_auth_enabled():
    try:
        restored = restore_supabase_login_from_session()
    except Exception:
        restored = False

if not restored and auth0_enabled():
    try:
        restored = restore_login_from_token()
    except Exception:
        restored = False

bootstrap_target = _query_value(BOOTSTRAP_QUERY_KEY).lower()
bootstrap_attempt = _query_int(BOOTSTRAP_ATTEMPT_QUERY_KEY)

st.session_state["_hm_router_build"] = ROUTER_BUILD
st.session_state["_hm_router_restore_ms"] = round(
    (time.perf_counter() - restore_started) * 1000,
    1,
)
st.session_state["_hm_router_native_identity"] = _native_identity_present()
st.session_state["_hm_router_auth_cookie_present"] = _auth_cookie_present()
st.session_state["_hm_router_bootstrap_target"] = bootstrap_target
st.session_state["_hm_router_bootstrap_attempt"] = bootstrap_attempt

technical_pages = (
    consent_page,
    native_logout_page,
    auth_diagnostics_page,
)

if selected_page not in technical_pages:
    if restored:
        is_admin = is_admin_role(st.session_state.get("user_role"))
        restored_role = "admin" if is_admin else "member"

        # After OIDC returns to the root, perform one browser-level stabilization
        # before showing a protected page. This proves the newly written identity
        # cookie can be read by a separate Streamlit session before the user refreshes.
        if selected_page is root_page and not bootstrap_target:
            _restart_as_new_browser_session(
                restored_role,
                attempt=1,
                message="HealthyMe is securing your new sign-in…",
            )

        if is_admin and selected_page in (root_page, login_page, member_page):
            st.switch_page(admin_page)
        if not is_admin and selected_page in (root_page, login_page, admin_page):
            st.switch_page(member_page)

    elif selected_page is admin_page:
        _restart_as_new_browser_session("admin", attempt=1)

    elif selected_page is member_page:
        _restart_as_new_browser_session("member", attempt=1)

    elif selected_page is root_page:
        if bootstrap_target in {"admin", "member"}:
            if bootstrap_attempt < BOOTSTRAP_MAX_ATTEMPTS:
                _restart_as_new_browser_session(
                    bootstrap_target,
                    attempt=bootstrap_attempt + 1,
                )
            if _native_identity_present() or _auth_cookie_present():
                _show_role_restore_recovery()
        st.switch_page(login_page)

    elif selected_page is login_page and (
        _native_identity_present() or _auth_cookie_present()
    ):
        # Never present a second login form while a native identity is already active.
        _show_role_restore_recovery()

selected_page.run()
