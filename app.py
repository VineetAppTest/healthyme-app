import streamlit as st
from components.admin_role_model import is_admin_role
from components.ui_common import inject_global_styles, apply_luxe_theme, render_build_text_v12
from components.auth_session import restore_login_from_token
from components.auth_mode import supabase_auth_enabled
from components.supabase_auth_session import restore_supabase_login_from_session

st.set_page_config(page_title="HealthyMe", page_icon="🌿", layout="wide", initial_sidebar_state="collapsed")
inject_global_styles()
apply_luxe_theme()

# Auth0 redirects back to the root/home page after login.
# Stage 3 also supports a Supabase Auth pilot session when AUTH_MODE allows it.
# In dual mode, prefer an existing Supabase pilot session before falling back to Auth0.
restored = False
if supabase_auth_enabled():
    restored = restore_supabase_login_from_session()
if not restored:
    restored = restore_login_from_token()

if restored:
    if is_admin_role(st.session_state.get("user_role")):
        st.switch_page("pages/10_Admin_Dashboard.py")
    else:
        st.switch_page("pages/02_Member_Home.py")

st.switch_page("pages/01_Login.py")
