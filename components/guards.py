import streamlit as st
from components.auth_mode import supabase_auth_enabled
from components.auth_session import restore_login_from_token
from components.supabase_auth_session import restore_supabase_login_from_session, render_supabase_browser_session_bridge


def _restore_allowed_session():
    if supabase_auth_enabled():
        render_supabase_browser_session_bridge(stop_for_sync=True)
        if restore_supabase_login_from_session():
            return True
    return restore_login_from_token()


def require_admin():
    _restore_allowed_session()
    if not st.session_state.get("logged_in") or st.session_state.get("user_role") != "admin":
        st.switch_page("pages/01_Login.py")
    st.session_state["is_admin"] = True
    st.session_state["admin_logged_in"] = True


def require_member():
    _restore_allowed_session()
    if not st.session_state.get("logged_in") or st.session_state.get("user_role") != "member":
        st.switch_page("pages/01_Login.py")
