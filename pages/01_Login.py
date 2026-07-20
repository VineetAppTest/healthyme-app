import html

import streamlit as st

from components.admin_role_model import is_admin_role
from components.auth_mode import (
    auth_mode_label,
    oidc_button_label,
    oidc_provider_name,
    supabase_oidc_poc_enabled,
)
from components.auth_session import restore_login_from_token
from components.ui_common import apply_luxe_theme, inject_global_styles


st.set_page_config(
    page_title="HealthyMe OIDC PoC",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="collapsed",
)
inject_global_styles()
apply_luxe_theme()


def _route_authenticated_user() -> None:
    requested_page = str(
        st.session_state.pop("_hm_requested_page_after_login", "") or ""
    )
    expected_role = str(
        st.session_state.pop("_hm_expected_login_role", "") or ""
    ).strip().lower()
    requested_role = str(
        st.session_state.pop("_hm_requested_role_after_bootstrap", "")
        or expected_role
        or ""
    ).strip().lower()
    st.session_state.pop("_hm_oidc_entrypoint_bootstrap_attempted", None)

    is_admin = is_admin_role(st.session_state.get("user_role"))
    restored_role = "admin" if is_admin else "member"

    if (
        requested_page.startswith("pages/")
        and requested_page != "pages/01_Login.py"
        and requested_role == restored_role
    ):
        try:
            st.switch_page(requested_page)
            return
        except Exception:
            pass

    if is_admin:
        st.switch_page("pages/10_Admin_Dashboard.py")
    else:
        st.switch_page("pages/02_Member_Home.py")


def _logout_was_requested() -> bool:
    if st.session_state.get("logout_requested") or st.session_state.get("signed_out"):
        return True
    try:
        return str(st.query_params.get("logout") or "").strip() == "1"
    except Exception:
        return False


def _clear_local_logout_state() -> None:
    for key in list(st.session_state.keys()):
        try:
            del st.session_state[key]
        except Exception:
            pass
    try:
        st.query_params.clear()
    except Exception:
        pass


def _bootstrap_entrypoint_for_protected_refresh() -> None:
    """Let app.py rebuild the role session from the retained OIDC cookie once."""
    requested_page = str(
        st.session_state.get("_hm_requested_page_after_login") or ""
    )
    if not requested_page.startswith("pages/"):
        return
    if st.session_state.get("_hm_oidc_entrypoint_bootstrap_attempted"):
        return

    requested_role = str(
        st.session_state.get("_hm_expected_login_role") or ""
    ).strip().lower()
    st.session_state["_hm_requested_role_after_bootstrap"] = requested_role
    st.session_state["_hm_oidc_entrypoint_bootstrap_attempted"] = True
    st.switch_page("app.py")


if not supabase_oidc_poc_enabled():
    st.error(
        "This branch is the isolated Supabase OIDC proof of concept. "
        "Set AUTH_MODE='supabase_oidc_poc' in the temporary Streamlit app secrets."
    )
    st.stop()

# Logout must be handled before any identity restoration. The dashboard sets a
# session flag before navigating here; otherwise the valid Streamlit identity
# cookie would immediately rebuild the HealthyMe session and route back.
if _logout_was_requested():
    try:
        st.query_params.clear()
    except Exception:
        pass
    if st.user.is_logged_in:
        st.logout()
    _clear_local_logout_state()

# A hard refresh of a protected legacy multipage URL can reach Login before that
# page can see the native OIDC identity. The entrypoint is able to see and restore
# the cookie, as confirmed when opening the temporary app root directly. Bootstrap
# through app.py once, then return to the requested page when the role matches.
_bootstrap_entrypoint_for_protected_refresh()

if restore_login_from_token():
    _route_authenticated_user()

st.markdown(
    f"""
    <div class="login-brand-row">
      <div>
        <div class="login-brand-name">HealthyMe</div>
        <div class="login-brand-sub">Same-app Supabase OIDC proof of concept</div>
      </div>
      <div class="login-secure-pill">{html.escape(auth_mode_label())}</div>
    </div>
    """,
    unsafe_allow_html=True,
)

left, right = st.columns([0.96, 1.04], gap="large")

with left:
    try:
        box = st.container(border=True)
    except TypeError:
        box = st.container()

    with box:
        st.markdown("## Secure test login")
        st.caption(
            "This temporary branch tests whether Streamlit can retain a Supabase "
            "identity across browser refreshes through its native OIDC cookie."
        )

        if st.button(
            oidc_button_label(),
            type="primary",
            use_container_width=True,
        ):
            st.session_state.pop("signed_out", None)
            st.session_state.pop("logout_requested", None)
            st.session_state.pop("_hm_oidc_entrypoint_bootstrap_attempted", None)
            st.login(oidc_provider_name())

        st.info(
            "This test does not replace the working H13R1 production login. "
            "No Supabase password, access token, or refresh token is stored by Streamlit."
        )

with right:
    st.markdown(
        """
        <div class="journey-card">
          <h3>PoC acceptance</h3>
          <p>The test succeeds only when both HealthyMe roles remain signed in after refresh.</p>
          <div class="journey-grid">
            <div class="journey-item">✓ Admin role mapping</div>
            <div class="journey-item">✓ Member role mapping</div>
            <div class="journey-item">✓ Protected-page refresh</div>
            <div class="journey-item">✓ Native OIDC logout</div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

if st.user.is_logged_in:
    if st.button("Clear test identity", use_container_width=True):
        st.logout()
