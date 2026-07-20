import streamlit as st

from components.admin_role_model import is_admin_role
from components.auth_mode import auth0_enabled, supabase_auth_enabled
from components.auth_session import restore_login_from_token
from components.supabase_auth_session import restore_supabase_login_from_session
from components.ui_common import apply_luxe_theme, inject_global_styles


st.set_page_config(
    page_title="HealthyMe",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="collapsed",
)
inject_global_styles()
apply_luxe_theme()

# A completed logout must always land on Login without attempting any provider restore.
if st.session_state.get("signed_out") or st.session_state.get("logout_requested"):
    st.switch_page("pages/01_Login.py")

restored = False
if supabase_auth_enabled():
    restored = restore_supabase_login_from_session()

# In Supabase-only mode, never inspect or restore a stale Auth0/OIDC browser identity.
if not restored and auth0_enabled():
    restored = restore_login_from_token()

if restored:
    if is_admin_role(st.session_state.get("user_role")):
        st.switch_page("pages/10_Admin_Dashboard.py")
    else:
        st.switch_page("pages/02_Member_Home.py")

st.switch_page("pages/01_Login.py")
