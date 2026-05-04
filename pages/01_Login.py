import streamlit as st
from components.ui_common import inject_global_styles, apply_luxe_theme
from components.db import authenticate, create_login_session
from components.auth_session import persist_token_in_url, restore_login_from_token

st.set_page_config(page_title="HealthyMe Login", page_icon="🌿", layout="wide")
inject_global_styles()
apply_luxe_theme()

# If browser was refreshed and token is present, restore login.
if restore_login_from_token():
    if st.session_state.get('must_reset_password'):
        st.switch_page('pages/00_Reset_Password.py')
    elif st.session_state.get('user_role') == 'admin':
        st.switch_page('pages/10_Admin_Dashboard.py')
    else:
        st.switch_page('pages/02_Member_Home.py')

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

        email = st.text_input("Email", placeholder="name@example.com")
        password = st.text_input("Password", type="password", placeholder="Enter password")

        if st.button("Login", type="primary", use_container_width=True):
            user = authenticate(email, password)
            if not user:
                st.error("Invalid email or password.")
            else:
                st.session_state["logged_in"] = True
                st.session_state["user_id"] = user["id"]
                st.session_state["user_role"] = user["role"]
                st.session_state["user_name"] = user["name"]
                st.session_state["must_reset_password"] = user.get("must_reset_password", False)
                token = create_login_session(user["id"])
                st.session_state["hm_token"] = token
                persist_token_in_url(token)
                if st.session_state["must_reset_password"]:
                    st.switch_page("pages/00_Reset_Password.py")
                elif user["role"] == "admin":
                    st.switch_page("pages/10_Admin_Dashboard.py")
                else:
                    st.switch_page("pages/02_Member_Home.py")

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