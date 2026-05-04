import streamlit as st

from components.auth_session import (
    maybe_wait_for_cookie_restore,
    restore_session_immediately,
    safe_switch_page,
)


def _ensure_login_restored():
    if not st.session_state.get("logged_in"):
        if not restore_session_immediately():
            maybe_wait_for_cookie_restore()


def _enforce_password_reset():
    if st.session_state.get("logged_in") and st.session_state.get("must_reset_password"):
        safe_switch_page("pages/00_Reset_Password.py")


def require_admin():
    _ensure_login_restored()
    if not st.session_state.get("logged_in") or st.session_state.get("user_role") != "admin":
        safe_switch_page("pages/01_Login.py")
    _enforce_password_reset()


def require_member():
    _ensure_login_restored()
    if not st.session_state.get("logged_in") or st.session_state.get("user_role") != "member":
        safe_switch_page("pages/01_Login.py")
    _enforce_password_reset()
