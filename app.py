import time
from urllib.parse import urlsplit

import streamlit as st

from components.admin_role_model import is_admin_role
from components.auth_mode import auth0_enabled, supabase_auth_enabled
from components.auth_session import restore_login_from_token
from components.supabase_auth_session import restore_supabase_login_from_session
from components.ui_common import apply_luxe_theme, inject_global_styles


ROUTER_BUILD = "H13O2-st-navigation-poc-v5-session-bootstrap"
LOGOUT_QUERY_KEY = "logout"
PROTECTED_BOOTSTRAP_DELAYS = (0.15, 0.35, 0.75)


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


def _logout_marker_present() -> bool:
    return _query_value(LOGOUT_QUERY_KEY) == "1"


def _logout_was_requested() -> bool:
    return bool(
        _logout_marker_present()
        or st.session_state.get("logout_requested")
        or st.session_state.get("signed_out")
    )


def _clear_local_session(*, preserve_query_params: bool = False) -> None:
    for key in list(st.session_state.keys()):
        try:
            del st.session_state[key]
        except Exception:
            pass
    if not preserve_query_params:
        try:
            st.query_params.clear()
        except Exception:
            pass


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


def _app_origin() -> str:
    try:
        parsed = urlsplit(str(st.context.url or ""))
        if parsed.scheme and parsed.netloc:
            return f"{parsed.scheme}://{parsed.netloc}"
    except Exception:
        pass
    return ""


def _absolute_app_url(path: str) -> str:
    normalized = "/" + str(path or "").lstrip("/")
    origin = _app_origin()
    return f"{origin}{normalized}" if origin else normalized


def _root_route() -> None:
    """The central router redirects root before this placeholder normally runs."""
    st.empty()


def _router_logout_button() -> None:
    # A URL marker survives the new browser session created by st.logout(). It keeps
    # Login stable while the browser finishes deleting the identity cookie.
    st.link_button(
        "Logout",
        _absolute_app_url("/Native_Logout?logout=1"),
        use_container_width=False,
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
    _router_logout_button()


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
    _router_logout_button()


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
        st.session_state.pop("_hm_router_final_retry_done", None)
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

logout_marker = _logout_marker_present()

# A durable URL marker is intentionally preserved across the new session created by
# st.logout(). While it is present, stale identity state is never allowed to rebuild a
# HealthyMe session or redirect Login back to a protected page.
if _logout_was_requested():
    if _native_identity_present():
        st.logout()
    _clear_local_session(preserve_query_params=logout_marker)

restore_started = time.perf_counter()
restored = False

if not logout_marker:
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
st.session_state["_hm_router_logout_marker"] = logout_marker

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
    if logout_marker:
        st.session_state.pop("_hm_protected_bootstrap_attempt", None)
        if selected_page is not login_page:
            st.switch_page(login_page)
    elif restored:
        st.session_state.pop("_hm_protected_bootstrap_attempt", None)
        st.session_state.pop("_hm_router_final_retry_done", None)
        is_admin = is_admin_role(st.session_state.get("user_role"))
        if is_admin and selected_page in (root_page, login_page, member_page):
            st.switch_page(admin_page)
        if not is_admin and selected_page in (root_page, login_page, admin_page):
            st.switch_page(member_page)
    elif selected_page in protected_pages:
        # On a hard refresh, the first script run can occur before Streamlit has exposed
        # the persisted identity cookie through st.user/st.context. Retry the whole router
        # across bounded reruns even when the first run sees neither signal.
        attempt = int(st.session_state.get("_hm_protected_bootstrap_attempt") or 0)
        if attempt < len(PROTECTED_BOOTSTRAP_DELAYS):
            st.session_state["_hm_protected_bootstrap_attempt"] = attempt + 1
            time.sleep(PROTECTED_BOOTSTRAP_DELAYS[attempt])
            st.rerun()

        native_identity = _native_identity_present()
        auth_cookie = _auth_cookie_present()
        if native_identity or auth_cookie:
            _show_role_restore_recovery()

        st.session_state.pop("_hm_protected_bootstrap_attempt", None)
        st.switch_page(login_page)
    else:
        st.session_state.pop("_hm_protected_bootstrap_attempt", None)

selected_page.run()
