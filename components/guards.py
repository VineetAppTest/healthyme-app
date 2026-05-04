import streamlit as st
from components.auth_session import restore_login_from_token

def require_admin():
    restore_login_from_token()
    if not st.session_state.get("logged_in") or st.session_state.get("user_role")!="admin":
        st.switch_page("pages/01_Login.py")

def require_member():
    restore_login_from_token()
    if not st.session_state.get("logged_in") or st.session_state.get("user_role")!="member":
        st.switch_page("pages/01_Login.py")