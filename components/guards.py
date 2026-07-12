from datetime import date
import inspect

import streamlit as st

from components.admin_role_model import current_user_is_admin, current_user_is_member
from components.auth_mode import auth0_enabled, supabase_auth_enabled
from components.auth_session import restore_login_from_token
from components.supabase_auth_session import restore_supabase_login_from_session


def restore_any_login():
    # Prefer an already-resolved HealthyMe app session, but do not let a
    # Supabase pilot member/admin role silently fall back to a stale Auth0 role.
    if st.session_state.get("logged_in") and st.session_state.get("_hm_auth_role_resolved"):
        if st.session_state.get("auth_login_method") == "supabase" or st.session_state.get("auth_provider") == "supabase":
            # A protected page should never behave like a logout just because a
            # direct URL was opened or a transient role refresh failed. Keep the
            # already-resolved Supabase role for this request, then the final
            # admin/member check below decides access.
            try:
                restore_supabase_login_from_session(force_refresh=True)
            except Exception:
                pass
            return True
        return True

    restored = False
    if supabase_auth_enabled():
        try:
            restored = restore_supabase_login_from_session()
        except Exception:
            restored = False
    if not restored and auth0_enabled():
        try:
            restored = restore_login_from_token()
        except Exception:
            restored = False
    return bool(restored)


def _show_access_required(required_role: str = "Admin") -> None:
    st.warning(f"{required_role} access required")
    st.caption(
        "Protected pages do not start a login/logout flow. Please sign in from the Login page "
        "with the correct role, then use the in-app navigation to open this page. A full browser "
        "reload or pasted direct URL can start a fresh Streamlit session during Supabase testing."
    )
    if st.button("Go to Login", key=f"hm_go_to_login_{required_role.lower()}"):
        try:
            st.switch_page("pages/01_Login.py")
        except Exception:
            st.info("Open the Login page from the app menu or app root.")
    st.stop()


def _current_page_filename() -> str:
    """Return the active Streamlit page filename without relying on URL parsing."""
    for frame in inspect.stack():
        filename = str(frame.filename or "").replace("\\", "/")
        if "/pages/" in filename:
            return filename.rsplit("/", 1)[-1]
    return ""


def _apply_member_page_defaults() -> None:
    """Apply page-specific defaults only when the member enters that page."""
    current_page = _current_page_filename()
    previous_page = st.session_state.get("_hm_previous_member_page")

    if current_page == "18_Daily_Log.py":
        if previous_page != current_page:
            today = date.today()
            st.session_state["hm_h9a4c_saved_from"] = today
            st.session_state["hm_h9a4c_saved_to"] = today

        # Scope the reorder to the Daily Log Food Journal by requiring the
        # page-specific marker inside the same direct-child container. The prior
        # selector depended on an unstable Streamlit wrapper hierarchy and did
        # not move the block reliably.
        st.markdown(
            """
            <style>
            div[data-testid="stVerticalBlock"]:has(> div[data-testid="stVerticalBlockBorderWrapper"] .hm-h9a4c-note){
              display:flex!important;
              flex-direction:column!important;
            }
            div[data-testid="stVerticalBlock"]:has(> div[data-testid="stVerticalBlockBorderWrapper"] .hm-h9a4c-note)
            > div[data-testid="stVerticalBlockBorderWrapper"]:nth-of-type(2){
              order:100!important;
            }
            </style>
            """,
            unsafe_allow_html=True,
        )

    st.session_state["_hm_previous_member_page"] = current_page


def require_admin():
    restore_any_login()
    if not st.session_state.get("logged_in"):
        _show_access_required("Admin")

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
        _show_access_required("Admin")
    st.session_state["is_admin"] = True
    st.session_state["admin_logged_in"] = True


def require_member():
    restore_any_login()
    if not st.session_state.get("logged_in"):
        _show_access_required("Member")

    if st.session_state.get("auth_login_method") == "supabase" or st.session_state.get("auth_provider") == "supabase":
        try:
            restore_supabase_login_from_session(force_refresh=True)
        except Exception:
            pass

    if not current_user_is_member():
        _show_access_required("Member")

    _apply_member_page_defaults()
