import streamlit as st
from components.ui_common import inject_global_styles, apply_luxe_theme
from components.auth_session import restore_login_from_token

st.set_page_config(page_title="HealthyMe", page_icon="🌿", layout="wide", initial_sidebar_state="collapsed")
inject_global_styles()
apply_luxe_theme()

# Auth0 redirects back to the root/home page after login.
# Route from here directly to the correct role page to avoid the extra Login page bounce.
if restore_login_from_token():
    if st.session_state.get("user_role") == "admin":
        st.switch_page("pages/10_Admin_Dashboard.py")
    else:
        st.switch_page("pages/02_Member_Home.py")

st.switch_page("pages/01_Login.py")