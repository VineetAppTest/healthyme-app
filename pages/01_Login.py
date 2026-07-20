import html

import streamlit as st

from components.admin_role_model import is_admin_role
from components.auth_mode import (
    auth0_enabled,
    auth_mode_label,
    get_auth_mode,
    supabase_auth_enabled,
)
from components.auth_session import (
    login_with_supabase_password,
    logout_current_user,
    pop_secure_logout_feedback,
    restore_login_from_token,
)
from components.supabase_auth_session import (
    restore_supabase_login_from_session,
    supabase_auth_configured,
)
from components.ui_common import apply_luxe_theme, inject_global_styles


st.set_page_config(
    page_title="HealthyMe Login",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="collapsed",
)
inject_global_styles()
apply_luxe_theme()

st.markdown(
    """
    <style>
    .hm-login-page-notice-slot{min-height:3.15rem;margin:.1rem 0 .45rem 0;}
    .hm-login-inline-status-slot{min-height:3.15rem;margin:.35rem 0 .15rem 0;}
    .hm-login-notice{display:flex;align-items:center;min-height:2.75rem;padding:.62rem .8rem;border-radius:12px;font-size:.86rem;font-weight:700;line-height:1.35;}
    .hm-login-notice-info{background:#EAF5F8;border:1px solid #CFE4EA;color:#0F4C5C;}
    .hm-login-notice-success{background:#E7F7EF;border:1px solid #C9EAD7;color:#166534;}
    .hm-login-notice-warning{background:#FFF4DE;border:1px solid #E8D39E;color:#8A5F10;}
    .hm-login-notice-error{background:#FDECEC;border:1px solid #F2C8C8;color:#9B1C1C;}
    .hm-login-notice-empty{visibility:hidden;border:1px solid transparent;}
    div[data-testid="stHorizontalBlock"]:has(.hm-login-column-anchor){align-items:flex-start!important;}
    div[data-testid="stHorizontalBlock"]:has(.hm-login-column-anchor)>div[data-testid="column"]{align-self:flex-start!important;}
    </style>
    """,
    unsafe_allow_html=True,
)


def _route_authenticated_user() -> None:
    requested_page = str(
        st.session_state.pop("_hm_requested_page_after_login", "") or ""
    )
    expected_role = str(
        st.session_state.pop("_hm_expected_login_role", "") or ""
    ).strip().lower()
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

    if expected_role == "member" and is_admin:
        st.session_state["auth_error"] = (
            "An admin account was detected while a member page was being recovered. "
            "Please sign out and use the member account."
        )
        return

    if is_admin:
        st.switch_page("pages/10_Admin_Dashboard.py")
    else:
        st.switch_page("pages/02_Member_Home.py")


def _notice_html(message: str = "", level: str = "info", *, inline: bool = False) -> str:
    slot_class = "hm-login-inline-status-slot" if inline else "hm-login-page-notice-slot"
    clean_message = html.escape(str(message or "").strip())
    if not clean_message:
        return (
            f"<div class='{slot_class}'><div class='hm-login-notice "
            "hm-login-notice-empty'>Status</div></div>"
        )
    safe_level = level if level in {"info", "success", "warning", "error"} else "info"
    return (
        f"<div class='{slot_class}'><div class='hm-login-notice "
        f"hm-login-notice-{safe_level}'>{clean_message}</div></div>"
    )


def _clear_login_request_flags() -> None:
    st.session_state.pop("signed_out", None)
    st.session_state.pop("logout_requested", None)
    try:
        st.query_params.clear()
    except Exception:
        pass


mode = get_auth_mode()
expected_login_role = str(
    st.session_state.get("_hm_expected_login_role", "") or ""
).strip().lower()

logout_param = False
try:
    logout_param = st.query_params.get("logout") == "1"
except Exception:
    pass

if logout_param:
    if st.session_state.get("logged_in"):
        logout_current_user()
    else:
        st.session_state["signed_out"] = True
        st.session_state["logout_requested"] = True
    try:
        st.query_params.clear()
    except Exception:
        pass

if not st.session_state.get("signed_out") and not st.session_state.get("logout_requested"):
    restored = False
    if supabase_auth_enabled():
        restored = restore_supabase_login_from_session()
    if not restored and auth0_enabled() and expected_login_role != "member":
        restored = restore_login_from_token()
    if restored:
        _route_authenticated_user()

page_notice_message = ""
page_notice_level = "info"

secure_logout_feedback = pop_secure_logout_feedback()
if secure_logout_feedback:
    page_notice_message = secure_logout_feedback.get("message") or "You have been signed out."
    page_notice_level = (
        "success" if secure_logout_feedback.get("level") == "success" else "warning"
    )
elif st.session_state.get("signed_out") or st.session_state.get("logout_requested"):
    page_notice_message = "You have been signed out securely."
    page_notice_level = "success"
else:
    recovery_message = st.session_state.pop("_hm_access_recovery_message", None)
    if recovery_message:
        page_notice_message = str(recovery_message)
        page_notice_level = "info"

# Retired cookie markers are informational only and never trigger authentication.
st.session_state.pop("_hm_legacy_supabase_marker_detected", None)

st.markdown(
    f"""
    <div class="login-brand-row">
      <div>
        <div class="login-brand-name">HealthyMe</div>
        <div class="login-brand-sub">Guided wellness assessment platform</div>
      </div>
      <div class="login-secure-pill">{html.escape(auth_mode_label())}</div>
    </div>
    """,
    unsafe_allow_html=True,
)
st.markdown(
    _notice_html(page_notice_message, page_notice_level),
    unsafe_allow_html=True,
)

login_col, journey_col = st.columns([0.96, 1.04], gap="large")

with login_col:
    st.markdown("<div class='hm-login-column-anchor'></div>", unsafe_allow_html=True)
    try:
        box = st.container(border=True)
    except TypeError:
        box = st.container()

    with box:
        st.markdown("## Secure Login")
        if mode == "supabase":
            st.caption(
                "Sign in through Supabase Auth. HealthyMe grants access only to "
                "authorized Admin or Member accounts."
            )
        elif mode == "dual":
            if expected_login_role == "member":
                st.caption(
                    "Member recovery mode: sign in with the Supabase member account."
                )
            else:
                st.caption("Select the configured authentication route.")
        else:
            st.caption("Sign in through Auth0 with an authorized HealthyMe account.")

        login_status_message = str(st.session_state.pop("auth_error", "") or "")
        login_status_level = "error" if login_status_message else "info"

        if auth0_enabled():
            if st.button(
                "Continue with Auth0",
                type="primary",
                use_container_width=True,
            ):
                st.session_state.pop("_hm_expected_login_role", None)
                st.session_state.pop("_hm_requested_page_after_login", None)
                _clear_login_request_flags()
                st.login("auth0")

        if supabase_auth_enabled():
            if auth0_enabled():
                st.markdown("---")
            if not supabase_auth_configured():
                login_status_message = (
                    "Supabase Auth is enabled, but its Streamlit configuration is incomplete."
                )
                login_status_level = "warning"
            else:
                with st.form("supabase_auth_login_form"):
                    email = st.text_input("Email", key="supabase_auth_email_input")
                    password = st.text_input(
                        "Password",
                        type="password",
                        key="supabase_auth_password_input",
                    )
                    submitted = st.form_submit_button(
                        "Continue with Supabase",
                        type="primary",
                        use_container_width=True,
                    )

                if submitted:
                    _clear_login_request_flags()
                    st.session_state.pop("auth_error", None)
                    if login_with_supabase_password(email, password):
                        _route_authenticated_user()
                    login_status_message = str(
                        st.session_state.pop("auth_error", "Supabase login failed.")
                    )
                    login_status_level = "error"

        st.markdown(
            _notice_html(login_status_message, login_status_level, inline=True),
            unsafe_allow_html=True,
        )

        if mode == "supabase":
            provider_copy = (
                "Supabase confirms your identity. HealthyMe then checks your active "
                "Admin or Member authorization."
            )
        elif mode == "dual":
            provider_copy = (
                "HealthyMe checks the selected provider and then verifies your active app role."
            )
        else:
            provider_copy = (
                "Auth0 confirms your identity. HealthyMe then checks your active app role."
            )

        st.markdown(
            f"""
            <div class='info-banner'>
              <b>No public sign-up:</b><br>
              {html.escape(provider_copy)}
            </div>
            """,
            unsafe_allow_html=True,
        )

with journey_col:
    provider_journey = (
        "Supabase Secure Login"
        if mode == "supabase"
        else ("Auth0 / Supabase Login" if mode == "dual" else "Auth0 Secure Login")
    )
    st.markdown(
        f"""
        <div class="journey-card">
          <h3>Your wellness journey</h3>
          <p>A premium, expert-led flow from assessment to actionable wellness guidance.</p>
          <div class="journey-grid">
            <div class="journey-item">✓ {html.escape(provider_journey)}</div>
            <div class="journey-item">✓ Lifestyle Assessment</div>
            <div class="journey-item">✓ NSP Assessment</div>
            <div class="journey-item">🔒 Expert Review</div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

feature_auth_label = (
    "Supabase Auth"
    if mode == "supabase"
    else ("OIDC + Supabase" if mode == "dual" else "OIDC login")
)
st.markdown(
    f"""
    <div class="login-feature-strip">
      <div class="login-feature"><b>Secure</b><span>{html.escape(feature_auth_label)}</span></div>
      <div class="login-feature"><b>Role-based</b><span>Admin / Member</span></div>
      <div class="login-feature"><b>Private</b><span>No URL token</span></div>
    </div>
    """,
    unsafe_allow_html=True,
)
