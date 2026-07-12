from datetime import date

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


def _apply_member_daily_log_defaults() -> None:
    """Keep Daily Log saved-day filters on today unless the member changes them."""
    today = date.today()
    st.session_state.setdefault("hm_h9a4c_saved_from", today)
    st.session_state.setdefault("hm_h9a4c_saved_to", today)

    # Daily Log renders View Saved Days as the second bordered block in the
    # Food Journal tab. Reorder only that page's tab panel by scoping to the
    # existing Daily Log marker class, leaving all other member tabs untouched.
    st.markdown(
        """
        <style>
        div[data-testid="stTabs"]:has(.hm-h9a4c-note)
        div[role="tabpanel"] > div[data-testid="stVerticalBlock"]{
          display:flex!important;
          flex-direction:column!important;
        }
        div[data-testid="stTabs"]:has(.hm-h9a4c-note)
        div[role="tabpanel"] > div[data-testid="stVerticalBlock"]
        > div[data-testid="stVerticalBlockBorderWrapper"]:nth-of-type(2){
          order:90!important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _hide_member_reference_library() -> None:
    """Temporarily hide the Member Home Reference Library without deleting routes."""
    st.markdown(
        """
        <style>
        div[data-testid="stVerticalBlock"] > div:has(.hm-home-reference-title),
        div[data-testid="stVerticalBlock"] > div:has(.hm-home-reference-title) ~ div{
          display:none!important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


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

    _apply_member_daily_log_defaults()
    _hide_member_reference_library()
