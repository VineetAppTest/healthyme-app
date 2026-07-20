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

restored = False
if supabase_auth_enabled():
    restored = restore_supabase_login_from_session()

# In Supabase-only mode, never inspect or restore a stale Auth0/OIDC browser identity.
if not restored and auth0_enabled():
    restored = restore_login_from_token()

if restored:
    is_admin = is_admin_role(st.session_state.get("user_role"))
    restored_role = "admin" if is_admin else "member"
    requested_page = str(
        st.session_state.pop("_hm_requested_page_after_login", "") or ""
    )
    requested_role = str(
        st.session_state.pop("_hm_requested_role_after_bootstrap", "") or ""
    ).strip().lower()
    st.session_state.pop("_hm_expected_login_role", None)
    st.session_state.pop("_hm_oidc_entrypoint_bootstrap_attempted", None)

    # A hard refresh of a legacy Streamlit multipage URL can start the page script
    # without the HealthyMe role session even though the native OIDC cookie is still
    # valid. Protected pages route here once so the entrypoint can rebuild the role
    # session, then return the user to the exact page only when the role matches.
    if (
        requested_page.startswith("pages/")
        and requested_page != "pages/01_Login.py"
        and requested_role == restored_role
    ):
        st.switch_page(requested_page)

    if is_admin:
        st.switch_page("pages/10_Admin_Dashboard.py")
    else:
        st.switch_page("pages/02_Member_Home.py")

# Honor a completed logout only after all configured providers have had a chance
# to restore. This avoids stale per-tab flags overriding a valid Streamlit OIDC
# identity cookie after refresh.
if st.session_state.get("signed_out") or st.session_state.get("logout_requested"):
    st.switch_page("pages/01_Login.py")

st.switch_page("pages/01_Login.py")
