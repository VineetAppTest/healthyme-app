import streamlit as st
from components.admin_role_model import is_admin_role
from components.ui_common import inject_global_styles, apply_luxe_theme, render_build_text_v12, render_back_to_top
from components.auth_mode import auth0_enabled, supabase_auth_enabled, auth_mode_label, get_auth_mode
from components.auth_session import restore_login_from_token, logout_current_user, login_with_supabase_password, pop_secure_logout_feedback
from components.supabase_auth_session import restore_supabase_login_from_session, supabase_auth_configured

st.set_page_config(page_title="HealthyMe Login", page_icon="🌿", layout="wide", initial_sidebar_state="collapsed")
inject_global_styles()
apply_luxe_theme()


def _route_authenticated_user():
    if is_admin_role(st.session_state.get("user_role")):
        st.switch_page("pages/10_Admin_Dashboard.py")
    else:
        st.switch_page("pages/02_Member_Home.py")


def _render_secure_logout_feedback(feedback):
    if not feedback:
        return
    message = feedback.get("message") or "Complete secure logout finished. Please open a fresh login session before switching users."
    level = feedback.get("level") or "success"
    if level == "success":
        st.success(message)
    else:
        st.warning(message)


logout_param = False
try:
    logout_param = st.query_params.get("logout") == "1"
except Exception:
    logout_param = False

if logout_param:
    st.session_state["signed_out"] = True
    st.session_state["logout_requested"] = True

if not st.session_state.get("signed_out") and not st.session_state.get("logout_requested"):
    restored = False
    if supabase_auth_enabled():
        restored = restore_supabase_login_from_session()
    if not restored and auth0_enabled():
        restored = restore_login_from_token()
    if restored:
        _route_authenticated_user()

mode = get_auth_mode()
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
        if mode == "supabase":
            st.caption("Sign in through Supabase Auth. HealthyMe will allow access only if your email is authorized by the admin.")
        elif mode == "dual":
            st.caption("Auth0 remains available. Supabase Auth is enabled only for controlled pilot testing.")
        else:
            st.caption("Sign in through Auth0. HealthyMe will allow access only if your email is authorized by the admin. Auth0 may take a few seconds during secure redirect.")

        auth_error = st.session_state.get("auth_error")
        if auth_error:
            st.error(auth_error)
            if st.button("Logout authenticated identity", use_container_width=True):
                logout_current_user()
                st.rerun()

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
                st.caption("Pilot only: Supabase Auth login")
            else:
                st.caption("Supabase Auth login")

            if not supabase_auth_configured():
                st.warning("Supabase Auth login is enabled by AUTH_MODE, but SUPABASE_URL and SUPABASE_ANON_KEY are not configured for Streamlit.")
            else:
                with st.form("supabase_auth_login_form"):
                    email = st.text_input("Email", key="supabase_auth_email_input")
                    password = st.text_input("Password", type="password", key="supabase_auth_password_input")
                    submitted = st.form_submit_button("Continue with Supabase", type="primary", use_container_width=True)

                if submitted:
                    st.session_state.pop("signed_out", None)
                    st.session_state.pop("logout_requested", None)
                    try:
                        st.query_params.clear()
                    except Exception:
                        pass
                    if login_with_supabase_password(email, password):
                        st.session_state.pop("signed_out", None)
                        st.session_state.pop("logout_requested", None)
                        try:
                            st.query_params.clear()
                        except Exception:
                            pass
                        st.success("Signed in with Supabase Auth.")
                        _route_authenticated_user()
                    else:
                        st.error(st.session_state.get("auth_error") or "Supabase login failed.")

        if mode == "supabase":
            provider_copy = "Supabase confirms who you are. HealthyMe then checks whether your email exists in the app as Admin or Member."
        elif mode == "dual":
            provider_copy = "Auth0 remains the default path. Supabase login is available only for controlled migration testing. HealthyMe still checks whether your email exists in the app as Admin or Member."
        else:
            provider_copy = "Auth0 confirms who you are. HealthyMe then checks whether your email exists in the app as Admin or Member."

        st.markdown(f"""
        <div class='info-banner'>
          <b>No public sign-up:</b><br>
          {provider_copy}
        </div>
        """, unsafe_allow_html=True)

    if st.session_state.get("signed_out") or st.session_state.get("logout_requested"):
        st.markdown("<div class='hm-logout-bottom-shell'>", unsafe_allow_html=True)
        secure_logout_feedback = pop_secure_logout_feedback()
        if secure_logout_feedback:
            _render_secure_logout_feedback(secure_logout_feedback)
        else:
            st.success("You have been signed out.")
        if mode == "supabase":
            logout_copy = "Your HealthyMe app session has been cleared."
            logout_button_label = "Clear session"
        elif mode == "dual":
            logout_copy = "Your HealthyMe app session has been cleared. Dual mode may keep your Auth0 browser identity active. Use Complete secure logout before switching from Auth0 admin to Supabase member testing."
            logout_button_label = "Complete secure logout"
        else:
            logout_copy = "For a full secure logout, complete the Auth0/OIDC logout below. If your browser still signs in automatically, close the browser tab or use a fresh browser profile."
            logout_button_label = "Complete secure logout"
        st.markdown(
            f"<div class='hm-logout-bottom-copy'>{logout_copy}</div>",
            unsafe_allow_html=True,
        )
        st.caption("Use Complete Secure Logout before switching between admin and member accounts during Supabase pilot testing.")
        if st.button(logout_button_label, key="complete_secure_logout_bottom", use_container_width=True):
            logout_current_user()
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

with journey_col:
    provider_journey = "Supabase Secure Login" if mode == "supabase" else ("Auth0 / Supabase Login" if mode == "dual" else "Auth0 Secure Login")
    st.markdown(f"""
    <div class="journey-card">
      <h3>Your wellness journey</h3>
      <p>A premium, expert-led flow from assessment to actionable wellness guidance.</p>
      <div class="journey-grid">
        <div class="journey-item">✓ {provider_journey}</div>
        <div class="journey-item">✓ Lifestyle Assessment</div>
        <div class="journey-item">✓ NSP Assessment</div>
        <div class="journey-item">🔒 Expert Review</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

feature_auth_label = "Supabase Auth" if mode == "supabase" else ("OIDC + Supabase" if mode == "dual" else "OIDC login")
st.markdown(f"""
<div class="login-feature-strip">
  <div class="login-feature"><b>Secure</b><span>{feature_auth_label}</span></div>
  <div class="login-feature"><b>Role-based</b><span>Admin / Member</span></div>
  <div class="login-feature"><b>Private</b><span>No URL token</span></div>
</div>
""", unsafe_allow_html=True)
