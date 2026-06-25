import streamlit as st
from components.ui_common import inject_global_styles, apply_luxe_theme, render_build_text_v12, render_back_to_top
from components.auth_mode import auth0_enabled, supabase_auth_enabled, auth_mode_label, get_auth_mode
from components.auth_session import restore_login_from_token, logout_current_user, login_with_supabase_password
from components.supabase_auth_session import supabase_password_auth_configured

st.set_page_config(page_title="HealthyMe Login", page_icon="🌿", layout="wide", initial_sidebar_state="collapsed")
inject_global_styles()
apply_luxe_theme()

logout_param = False
try:
    logout_param = st.query_params.get("logout") == "1"
except Exception:
    logout_param = False

if logout_param:
    st.session_state["signed_out"] = True
    st.session_state["logout_requested"] = True

if not st.session_state.get("signed_out") and not st.session_state.get("logout_requested") and restore_login_from_token():
    if st.session_state.get("user_role") == "admin":
        st.switch_page("pages/10_Admin_Dashboard.py")
    else:
        st.switch_page("pages/02_Member_Home.py")

st.markdown(f"""
<div class="login-brand-row">
  <div>
    <div class="login-brand-name">HealthyMe</div>
    <div class="login-brand-sub">Guided wellness assessment platform</div>
  </div>
  <div class="login-secure-pill">{auth_mode_label()}</div>
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
        auth_mode = get_auth_mode()
        if auth_mode == "supabase":
            st.caption("Sign in through Supabase. HealthyMe will allow access only if your email is authorized by the admin.")
        elif auth_mode == "dual":
            st.caption("Sign in through Auth0 or Supabase pilot login. HealthyMe will allow access only if your email is authorized by the admin.")
        else:
            st.caption("Sign in through Auth0. HealthyMe will allow access only if your email is authorized by the admin. Auth0 may take a few seconds during secure redirect.")

        auth_error = st.session_state.get("auth_error")
        if auth_error:
            st.error(auth_error)
            if st.button("Logout authenticated identity", use_container_width=True):
                logout_current_user()

        if auth0_enabled():
            if st.button("Continue with Auth0", type="primary", use_container_width=True):
                st.session_state.pop("signed_out", None)
                st.session_state.pop("logout_requested", None)
                try:
                    st.query_params.clear()
                except Exception:
                    pass
                st.login("auth0")

        if supabase_auth_enabled():
            if auth0_enabled():
                st.markdown("---")
            st.markdown("### Supabase pilot login")
            if not supabase_password_auth_configured():
                st.warning("Supabase pilot login is not configured yet. Use Auth0 login until the pilot settings are added.")
            with st.form("supabase_login_form"):
                supabase_email = st.text_input("Email", key="supabase_login_email")
                supabase_secret = st.text_input("Password", type="password", key="supabase_login_secret")
                supabase_submit = st.form_submit_button("Continue with Supabase", type="primary", use_container_width=True)
            if supabase_submit:
                if login_with_supabase_password(supabase_email, supabase_secret):
                    if st.session_state.get("user_role") == "admin":
                        st.switch_page("pages/10_Admin_Dashboard.py")
                    else:
                        st.switch_page("pages/02_Member_Home.py")

        if auth0_enabled() and supabase_auth_enabled():
            provider_text = "Auth0 or Supabase confirms who you are."
        elif supabase_auth_enabled():
            provider_text = "Supabase confirms who you are."
        else:
            provider_text = "Auth0 confirms who you are."

        st.markdown(f"""
        <div class='info-banner'>
          <b>No public sign-up:</b><br>
          {provider_text} HealthyMe then checks whether your email exists in the app as Admin or Member.
        </div>
        """, unsafe_allow_html=True)

    if st.session_state.get("signed_out") or st.session_state.get("logout_requested"):
        st.markdown("<div class='hm-logout-bottom-shell'>", unsafe_allow_html=True)
        st.success("You have been signed out.")
        logout_copy = "For a full secure logout, complete the Auth0/OIDC logout below. If your browser still signs in automatically, close the browser tab or use a fresh browser profile."
        if get_auth_mode() == "supabase":
            logout_copy = "You have been signed out of the HealthyMe app session. Close the browser tab if you want to fully clear local form entries."
        st.markdown(
            f"<div class='hm-logout-bottom-copy'>{logout_copy}</div>",
            unsafe_allow_html=True,
        )
        if auth0_enabled():
            if st.button("Complete secure logout", key="complete_secure_logout_bottom", use_container_width=True):
                logout_current_user()
        st.markdown("</div>", unsafe_allow_html=True)

with journey_col:
    st.markdown(f"""
    <div class="journey-card">
      <h3>Your wellness journey</h3>
      <p>A premium, expert-led flow from assessment to actionable wellness guidance.</p>
      <div class="journey-grid">
        <div class="journey-item">✓ {auth_mode_label()}</div>
        <div class="journey-item">✓ Lifestyle Assessment</div>
        <div class="journey-item">✓ NSP Assessment</div>
        <div class="journey-item">🔒 Expert Review</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("""
<div class="login-feature-strip">
  <div class="login-feature"><b>Secure</b><span>Role-checked login</span></div>
  <div class="login-feature"><b>Role-based</b><span>Admin / Member</span></div>
  <div class="login-feature"><b>Private</b><span>No URL token</span></div>
</div>
""", unsafe_allow_html=True)
