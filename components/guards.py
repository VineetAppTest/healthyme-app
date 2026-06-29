import streamlit as st

from components.admin_role_model import current_user_is_admin, current_user_is_member
from components.auth_mode import supabase_auth_enabled
from components.auth_session import restore_login_from_token
from components.supabase_auth_session import restore_supabase_login_from_session


def restore_any_login():
    # Prefer an already-resolved HealthyMe app session, but do not let a
    # Supabase pilot member/admin role silently fall back to a stale Auth0 role.
    if st.session_state.get("logged_in") and st.session_state.get("_hm_auth_role_resolved"):
        if st.session_state.get("auth_login_method") == "supabase" or st.session_state.get("auth_provider") == "supabase":
            try:
                return bool(restore_supabase_login_from_session(force_refresh=True))
            except Exception:
                return False
        return True

    restored = False
    if supabase_auth_enabled():
        try:
            restored = restore_supabase_login_from_session()
        except Exception:
            restored = False
    if not restored:
        try:
            restored = restore_login_from_token()
        except Exception:
            restored = False
    return bool(restored)


def require_admin():
    restore_any_login()
    if not st.session_state.get("logged_in"):
        st.switch_page("pages/01_Login.py")

    # Strict direct-link guard: when the current session is Supabase, refresh
    # the role from hm_users by auth_user_id/email before allowing admin pages.
    if st.session_state.get("auth_login_method") == "supabase" or st.session_state.get("auth_provider") == "supabase":
        try:
            restore_supabase_login_from_session(force_refresh=True)
        except Exception:
            # Do not convert a transient refresh problem into logout.
            # The final role check below remains the source of truth.
            pass

    if not current_user_is_admin():
        st.warning("Admin access required")
        st.stop()
    st.session_state["is_admin"] = True
    st.session_state["admin_logged_in"] = True


def require_member():
    restore_any_login()
    if not st.session_state.get("logged_in"):
        st.switch_page("pages/01_Login.py")

    if st.session_state.get("auth_login_method") == "supabase" or st.session_state.get("auth_provider") == "supabase":
        try:
            restore_supabase_login_from_session(force_refresh=True)
        except Exception:
            pass

    if not current_user_is_member():
        st.warning("Member access required")
        st.stop()
