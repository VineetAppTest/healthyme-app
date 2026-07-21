import time

import streamlit as st

from components.admin_role_model import is_admin_role
from components.auth_mode import auth0_enabled, supabase_auth_enabled
from components.auth_session import restore_login_from_token
from components.supabase_auth_session import restore_supabase_login_from_session
from components.ui_common import apply_luxe_theme, inject_global_styles


ROUTER_BUILD = "H13O2-st-navigation-poc-v7-native-session-flow"
PROTECTED_BOOTSTRAP_DELAYS = (0.15, 0.35, 0.75)


st.set_page_config(
    page_title="HealthyMe",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="collapsed",
)
inject_global_styles()
apply_luxe_theme()


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
    """Use Streamlit's native logout lifecycle without page or query-param redirects."""
    st.button(
        "Logout",
        key=key,
        use_container_width=False,
        on_click=st.logout,
    )


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
    """Keep an authenticated user out of Login when only restoration is delayed."""
    st.title("HealthyMe is restoring your access")
    st.warning(
        "Your secure sign-in is still active, but HealthyMe could not finish restoring "
        "your access profile. This is a temporary restoration issue, not a logout."
    )
    st.caption(
        "The app has already retried automatically. Use Retry access once; do not sign in again."
    )
    attempts = st.session_state.get("_hm_role_restore_attempts", "—")
    st.metric("Automatic role-lookup attempts", attempts)
    if st.button("Retry access", type="primary"):
        st.session_state.pop("_hm_protected_bootstrap_attempt", None)
        st.rerun()
    if st.button("Open safe diagnostics"):
        st.switch_page(auth_diagnostics_page)
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

st.session_state["_hm_router_build"] = ROUTER_BUILD
st.session_state["_hm_router_restore_ms"] = round(
    (time.perf_counter() - restore_started) * 1000,
    1,
)
st.session_state["_hm_router_native_identity"] = _native_identity_present()
st.session_state["_hm_router_auth_cookie_present"] = _auth_cookie_present()

technical_pages = (
    consent_page,
    native_logout_page,
    auth_diagnostics_page,
)
protected_pages = (
    root_page,
    admin_page,
    member_page,
)

if selected_page not in technical_pages:
    if restored:
        st.session_state.pop("_hm_protected_bootstrap_attempt", None)
        is_admin = is_admin_role(st.session_state.get("user_role"))
        if is_admin and selected_page in (root_page, login_page, member_page):
            st.switch_page(admin_page)
        if not is_admin and selected_page in (root_page, login_page, admin_page):
            st.switch_page(member_page)
    elif selected_page in protected_pages:
        # A hard refresh can begin before Streamlit exposes the persisted identity to
        # the first Python run. Retry the complete router for a short bounded period.
        attempt = int(st.session_state.get("_hm_protected_bootstrap_attempt") or 0)
        if attempt < len(PROTECTED_BOOTSTRAP_DELAYS):
            st.session_state["_hm_protected_bootstrap_attempt"] = attempt + 1
            time.sleep(PROTECTED_BOOTSTRAP_DELAYS[attempt])
            st.rerun()

        if _native_identity_present() or _auth_cookie_present():
            _show_role_restore_recovery()

        st.session_state.pop("_hm_protected_bootstrap_attempt", None)
        st.switch_page(login_page)
    elif selected_page is login_page and (
        _native_identity_present() or _auth_cookie_present()
    ):
        # Never present a second login form while a native identity is already active.
        _show_role_restore_recovery()
    else:
        st.session_state.pop("_hm_protected_bootstrap_attempt", None)

selected_page.run()
