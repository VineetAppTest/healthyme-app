import html

import streamlit as st

from components.admin_role_model import is_admin_role
from components.auth_mode import (
    auth_mode_label,
    oidc_button_label,
    oidc_provider_name,
    supabase_oidc_poc_enabled,
)
from components.auth_session import (
    logout_current_user,
    restore_login_from_token,
)
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
    st.session_state.pop("_hm_expected_login_role", None)
    is_admin = is_admin_role(st.session_state.get("user_role"))

    if requested_page.startswith("pages/") and requested_page != "pages/01_Login.py":
        requested_is_admin_page = "Admin" in requested_page
        role_matches_page = (
            (is_admin and requested_is_admin_page)
            or (not is_admin and not requested_is_admin_page)
        )
        if role_matches_page:
            try:
                st.switch_page(requested_page)
                return
            except Exception:
                pass

    if is_admin:
        st.switch_page("pages/10_Admin_Dashboard.py")
    else:
        st.switch_page("pages/02_Member_Home.py")


if not supabase_oidc_poc_enabled():
    st.error(
        "This branch is the isolated Supabase OIDC proof of concept. "
        "Set AUTH_MODE='supabase_oidc_poc' in the temporary Streamlit app secrets."
    )
    st.stop()

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
            st.session_state.pop("_hm_expected_login_role", None)
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
        logout_current_user()
