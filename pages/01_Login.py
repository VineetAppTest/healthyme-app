import streamlit as st

from components.ui_common import inject_global_styles, apply_luxe_theme
from components.db import authenticate
from components.auth_session import start_persistent_session, restore_persistent_session, route_authenticated_user, maybe_wait_for_cookie_restore

st.set_page_config(page_title="HealthyMe Login", page_icon="🌿", layout="wide")
inject_global_styles()
apply_luxe_theme()

if restore_persistent_session():
    route_authenticated_user()
else:
    maybe_wait_for_cookie_restore()


st.markdown("""
<div class="login-brand-row">
  <div>
    <div class="login-brand-name">HealthyMe</div>
    <div class="login-brand-sub">Guided wellness assessment platform</div>
  </div>
  <div class="login-secure-pill">Secure access</div>
</div>
""", unsafe_allow_html=True)

login_col, journey_col = st.columns([.96, 1.04], gap="large")

with login_col:
    try:
        box = st.container(border=True)
    except TypeError:
        box = st.container()

    with box:
        st.markdown("## Login Credentials")
        st.caption("Sign in using the access created by your administrator.")

        with st.form("healthyme_login_form", clear_on_submit=False):
            email = st.text_input("Email", placeholder="name@example.com")
            password = st.text_input("Password", type="password", placeholder="Enter password")
            submitted = st.form_submit_button("Login", type="primary", use_container_width=True)

        if submitted:
            with st.spinner("Signing you in securely..."):
                user = authenticate(email, password)
                if not user:
                    st.error("Invalid email or password.")
                else:
                    start_persistent_session(user)
                    route_authenticated_user()

with journey_col:
    st.markdown("""
    <div class="journey-card">
      <h3>Your wellness journey</h3>
      <p>A premium, expert-led flow from assessment to actionable wellness guidance.</p>
      <div class="journey-grid">
        <div class="journey-item">✓ Lifestyle Assessment</div>
        <div class="journey-item">✓ NSP Assessment</div>
        <div class="journey-item">⏳ Expert Review</div>
        <div class="journey-item">🔒 Personalized Plan</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("""
<div class="login-feature-strip">
  <div class="login-feature"><b>Assess</b><p>Complete guided LAF and NSP sections.</p></div>
  <div class="login-feature"><b>Review</b><p>Admin evaluates responses and scoring.</p></div>
  <div class="login-feature"><b>Guide</b><p>Recipes and exercises unlock after review.</p></div>
  <div class="login-feature"><b>Private</b><p>Access is administrator controlled.</p></div>
</div>
""", unsafe_allow_html=True)
