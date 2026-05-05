import streamlit as st
from components.ui_common import inject_global_styles, apply_luxe_theme
from components.auth_session import restore_login_from_token, get_oidc_email, get_oidc_name

st.set_page_config(page_title="HealthyMe Login", page_icon="🌿", layout="wide", initial_sidebar_state="collapsed")
inject_global_styles()
apply_luxe_theme()

# If already authenticated and authorized, route user.
if restore_login_from_token():
    if st.session_state.get("user_role") == "admin":
        st.switch_page("pages/10_Admin_Dashboard.py")
    else:
        st.switch_page("pages/02_Member_Home.py")

st.markdown("""
<div class="login-brand-row">
  <div>
    <div class="login-brand-name">HealthyMe</div>
    <div class="login-brand-sub">Guided wellness assessment platform</div>
  </div>
  <div class="login-secure-pill">Auth0 / OIDC secure access</div>
</div>
""", unsafe_allow_html=True)

login_col, journey_col = st.columns([.96, 1.04], gap="large")

with login_col:
    try:
        box = st.container(border=True)
    except TypeError:
        box = st.container()

    with box:
        st.markdown("## Secure Login")
        st.caption("Sign in through Auth0. HealthyMe will allow access only if your email is authorized by the admin. Auth0 may take a few seconds during secure redirect.")

        auth_error = st.session_state.get("auth_error")
        if auth_error:
            st.error(auth_error)
            if st.button("Logout authenticated identity", use_container_width=True):
                for k in list(st.session_state.keys()):
                    del st.session_state[k]
                st.logout()

        if st.button("Continue with Auth0", type="primary", use_container_width=True):
            st.login("auth0")

        st.markdown("""
        <div class='info-banner'>
          <b>No public sign-up:</b><br>
          Auth0 confirms who you are. HealthyMe then checks whether your email exists in the app as Admin or Member.
        </div>
        """, unsafe_allow_html=True)

with journey_col:
    st.markdown("""
    <div class="journey-card">
      <h3>Your wellness journey</h3>
      <p>A premium, expert-led flow from assessment to actionable wellness guidance.</p>
      <div class="journey-grid">
        <div class="journey-item">✓ Auth0 Secure Login</div>
        <div class="journey-item">✓ Lifestyle Assessment</div>
        <div class="journey-item">✓ NSP Assessment</div>
        <div class="journey-item">🔒 Expert Review</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("""
<div class="login-feature-strip">
  <div class="login-feature"><b>Secure</b><span>OIDC login</span></div>
  <div class="login-feature"><b>Role-based</b><span>Admin / Member</span></div>
  <div class="login-feature"><b>Private</b><span>No URL token</span></div>
</div>
""", unsafe_allow_html=True)