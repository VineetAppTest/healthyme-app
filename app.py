import time

import streamlit as st

from components.admin_role_model import is_admin_role
from components.auth_mode import auth0_enabled, supabase_auth_enabled
from components.auth_session import restore_login_from_token
from components.supabase_auth_session import restore_supabase_login_from_session
from components.ui_common import apply_luxe_theme, inject_global_styles


ROUTER_BUILD = "H13O2-st-navigation-poc-v2-diagnostics"


st.set_page_config(
    page_title="HealthyMe",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="collapsed",
)
inject_global_styles()
apply_luxe_theme()


def _logout_was_requested() -> bool:
    if st.session_state.get("logout_requested") or st.session_state.get("signed_out"):
        return True
    try:
        return str(st.query_params.get("logout") or "").strip() == "1"
    except Exception:
        return False


def _clear_local_session() -> None:
    for key in list(st.session_state.keys()):
        try:
            del st.session_state[key]
        except Exception:
            pass
    try:
        st.query_params.clear()
    except Exception:
        pass


def _root_route() -> None:
    if (
        st.session_state.get("logged_in")
        and st.session_state.get("_hm_auth_role_resolved")
    ):
        if is_admin_role(st.session_state.get("user_role")):
            st.switch_page("pages/10_Admin_Dashboard.py")
        st.switch_page("pages/02_Member_Home.py")
    st.switch_page("pages/01_Login.py")


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
    "pages/10_Admin_Dashboard.py",
    title="Admin Dashboard",
    url_path="Admin_Dashboard",
)
member_page = st.Page(
    "pages/02_Member_Home.py",
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

# Logout is handled centrally before any retained OIDC identity can rebuild the
# HealthyMe role session.
if _logout_was_requested():
    try:
        st.query_params.clear()
    except Exception:
        pass
    if st.user.is_logged_in:
        st.logout()
    _clear_local_session()

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

technical_pages = (
    consent_page,
    native_logout_page,
    auth_diagnostics_page,
)

if selected_page not in technical_pages:
    if restored:
        is_admin = is_admin_role(st.session_state.get("user_role"))
        if is_admin and selected_page in (login_page, member_page):
            st.switch_page(admin_page)
        if not is_admin and selected_page in (login_page, admin_page):
            st.switch_page(member_page)
    elif selected_page in (admin_page, member_page):
        st.switch_page(login_page)

selected_page.run()
