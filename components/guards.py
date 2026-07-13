from datetime import date
import inspect

import streamlit as st

from components.admin_role_model import current_user_is_admin, current_user_is_member
from components.auth_mode import auth0_enabled, supabase_auth_enabled
from components.auth_session import restore_login_from_token
from components.supabase_auth_session import restore_supabase_login_from_session


MEMBER_REFERENCE_LIBRARY_ENABLED = False
MEMBER_REFERENCE_LIBRARY_PAGES = {
    "08_Recipe_Repository.py",
    "09_Exercise_Repository.py",
    "40_Member_Supplements.py",
}


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


def _current_page_filename() -> str:
    """Return the active Streamlit page filename without relying on URL parsing."""
    for frame in inspect.stack():
        filename = str(frame.filename or "").replace("\\", "/")
        if "/pages/" in filename:
            return filename.rsplit("/", 1)[-1]
    return ""


def _show_access_required(required_role: str = "Admin") -> None:
    """Recover a fresh/expired Streamlit session through the normal login page."""
    current_page = _current_page_filename()
    if current_page and current_page != "01_Login.py":
        st.session_state["_hm_requested_page_after_login"] = f"pages/{current_page}"

    st.session_state["_hm_access_recovery_message"] = (
        "Your secure app session needs to be refreshed. Please sign in again."
    )
    try:
        st.switch_page("pages/01_Login.py")
    except Exception:
        st.warning(f"{required_role} access required")
        st.caption(
            "Your secure session could not be restored on this page. Please return to Login and sign in again."
        )
        if st.button("Go to Login", key=f"hm_go_to_login_{required_role.lower()}"):
            st.switch_page("pages/01_Login.py")
    st.stop()


def _apply_member_page_defaults(current_page: str) -> None:
    """Apply page-specific defaults only when the member enters that page."""
    previous_page = st.session_state.get("_hm_previous_member_page")

    if current_page == "18_Daily_Log.py" and previous_page != current_page:
        today = date.today()
        st.session_state["hm_h9a4c_saved_from"] = today
        st.session_state["hm_h9a4c_saved_to"] = today

    st.session_state["_hm_previous_member_page"] = current_page


def _apply_member_feature_visibility(current_page: str) -> None:
    """Hide and block the Member Reference Library until it is re-enabled."""
    if MEMBER_REFERENCE_LIBRARY_ENABLED:
        return

    if current_page == "02_Member_Home.py":
        st.markdown(
            """
            <style>
            /* Hide only the Reference Library heading and its three muted actions. */
            .hm-home-reference-title{display:none!important;}
            .hm-home-muted-anchor + div{display:none!important;}
            div[data-testid="stElementContainer"]:has(.hm-home-reference-title),
            div[data-testid="stElementContainer"]:has(.hm-home-muted-anchor){display:none!important;}
            </style>
            """,
            unsafe_allow_html=True,
        )

    if current_page in MEMBER_REFERENCE_LIBRARY_PAGES:
        st.session_state["_hm_reference_library_unavailable"] = True
        st.switch_page("pages/02_Member_Home.py")
        st.stop()


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

    current_page = _current_page_filename()
    _apply_member_page_defaults(current_page)
    _apply_member_feature_visibility(current_page)
