import html

import streamlit as st

from components.auth_mode import (
    auth_mode_label,
    oidc_button_label,
    oidc_provider_name,
    supabase_oidc_poc_enabled,
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


if not supabase_oidc_poc_enabled():
    st.error(
        "This branch is the isolated Supabase OIDC proof of concept. "
        "Set AUTH_MODE='supabase_oidc_poc' in the temporary Streamlit app secrets."
    )
    st.stop()

st.markdown(
    f"""
    <div class="login-brand-row">
      <div>
        <div class="login-brand-name">HealthyMe</div>
        <div class="login-brand-sub">Central st.navigation + Supabase OIDC proof of concept</div>
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
            "This temporary branch tests whether the central Streamlit router can "
            "restore the Supabase OIDC identity and HealthyMe role before a protected "
            "page runs after browser refresh."
        )

        if st.button(
            oidc_button_label(),
            type="primary",
            use_container_width=True,
        ):
            st.session_state.pop("signed_out", None)
            st.session_state.pop("logout_requested", None)
            st.session_state.pop("_hm_expected_login_role", None)
            st.session_state.pop("_hm_requested_page_after_login", None)
            st.login(oidc_provider_name())

        st.info(
            "This test does not replace the working H13R1 production login. "
            "No Supabase password, access token, or refresh token is stored by Streamlit."
        )

with right:
    st.markdown(
        """
        <div class="journey-card">
          <h3>H13O2 acceptance</h3>
          <p>The test succeeds only when both HealthyMe roles remain signed in after an immediate protected-page refresh.</p>
          <div class="journey-grid">
            <div class="journey-item">✓ Central router executes first</div>
            <div class="journey-item">✓ Admin role restoration</div>
            <div class="journey-item">✓ Member role restoration</div>
            <div class="journey-item">✓ Native OIDC logout</div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

if st.user.is_logged_in:
    if st.button("Clear test identity", use_container_width=True):
        st.logout()
