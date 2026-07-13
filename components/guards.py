from datetime import date
import inspect

import streamlit as st

from components.admin_role_model import current_user_is_admin, current_user_is_member
from components.auth_mode import auth0_enabled, supabase_auth_enabled
from components.auth_session import restore_login_from_token
from components.supabase_auth_session import (
    browser_has_legacy_supabase_marker,
    restore_supabase_login_from_session,
)


MEMBER_REFERENCE_LIBRARY_ENABLED = False
MEMBER_REFERENCE_LIBRARY_PAGES = {
    "08_Recipe_Repository.py",
    "09_Exercise_Repository.py",
    "40_Member_Supplements.py",
}


def restore_any_login(required_role: str = ""):
    """Restore only authentication providers appropriate for the requested role."""
    normalized_role = str(required_role or "").strip().lower()

    if st.session_state.get("logged_in") and st.session_state.get("_hm_auth_role_resolved"):
        if (
            st.session_state.get("auth_login_method") == "supabase"
            or st.session_state.get("auth_provider") == "supabase"
        ):
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

    # A member route must never inherit an existing Auth0 admin browser identity.
    if not restored and normalized_role == "member":
        st.session_state["_hm_expected_login_role"] = "member"
        if browser_has_legacy_supabase_marker():
            st.session_state["_hm_legacy_supabase_marker_detected"] = True
        return False

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
    """Recover a missing session through the normal Login page."""
    current_page = _current_page_filename()
    if current_page and current_page != "01_Login.py":
        st.session_state["_hm_requested_page_after_login"] = f"pages/{current_page}"

    normalized_role = str(required_role or "").strip().lower()
    if normalized_role:
        st.session_state["_hm_expected_login_role"] = normalized_role

    if normalized_role == "member":
        st.session_state["_hm_access_recovery_message"] = (
            "Your member session could not be restored after the app restart. "
            "Please sign in again with the member account."
        )
    else:
        st.session_state["_hm_access_recovery_message"] = (
            "Your secure app session needs to be refreshed. Please sign in again."
        )

    try:
        st.switch_page("pages/01_Login.py")
    except Exception:
        st.warning(f"{required_role} access required")
        st.caption(
            "Your secure session could not be restored on this page. "
            "Please return to Login and sign in again."
        )
        if st.button("Go to Login", key=f"hm_go_to_login_{normalized_role or 'user'}"):
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
    """Apply Member Home spacing and hide only the disabled library widgets."""
    if current_page != "02_Member_Home.py":
        return

    st.markdown(
        """
        <style>
        header[data-testid="stHeader"],
        [data-testid="stToolbar"],
        [data-testid="stDecoration"],
        [data-testid="stStatusWidget"]{
          display:none!important;
          visibility:hidden!important;
          height:0!important;
          min-height:0!important;
          margin:0!important;
          padding:0!important;
        }
        html body [data-testid="stAppViewContainer"],
        html body [data-testid="stMain"],
        html body section.main{
          padding-top:0!important;
          margin-top:0!important;
        }
        html body [data-testid="stMainBlockContainer"],
        html body [data-testid="stAppViewBlockContainer"],
        html body section.main > div.block-container,
        html body .main .block-container,
        html body .stMainBlockContainer,
        html body .block-container{
          padding-top:0!important;
          margin-top:0!important;
        }

        /* Collapse style-only Streamlit blocks that otherwise leave a blank band. */
        div[data-testid="stElementContainer"]:has(> div[data-testid="stMarkdownContainer"] > style),
        div[data-testid="stElementContainer"]:has(> div > div[data-testid="stMarkdownContainer"] > style){
          height:0!important;
          min-height:0!important;
          margin:0!important;
          padding:0!important;
          overflow:hidden!important;
        }

        /* Exact widget-key selectors first; these cannot hide the surrounding columns. */
        .st-key-hm_home_recipe_repo,
        .st-key-hm_home_exercise_repo,
        .st-key-hm_home_supplements{
          display:none!important;
          height:0!important;
          min-height:0!important;
          margin:0!important;
          padding:0!important;
          overflow:hidden!important;
        }

        /* Fallback selectors target only the marker's own element and next button. */
        div[data-testid="stElementContainer"]:has(> div[data-testid="stMarkdownContainer"] .hm-home-reference-title),
        div[data-testid="stElementContainer"]:has(> div > div[data-testid="stMarkdownContainer"] .hm-home-reference-title),
        div[data-testid="stElementContainer"]:has(> div[data-testid="stMarkdownContainer"] .hm-home-muted-anchor),
        div[data-testid="stElementContainer"]:has(> div > div[data-testid="stMarkdownContainer"] .hm-home-muted-anchor),
        div[data-testid="stElementContainer"]:has(> div[data-testid="stMarkdownContainer"] .hm-home-muted-anchor) + div[data-testid="stElementContainer"],
        div[data-testid="stElementContainer"]:has(> div > div[data-testid="stMarkdownContainer"] .hm-home-muted-anchor) + div[data-testid="stElementContainer"]{
          display:none!important;
          height:0!important;
          min-height:0!important;
          margin:0!important;
          padding:0!important;
          overflow:hidden!important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _redirect_disabled_reference_page(current_page: str) -> None:
    """Keep hidden member-library URLs away from admin and back to member flow."""
    if MEMBER_REFERENCE_LIBRARY_ENABLED or current_page not in MEMBER_REFERENCE_LIBRARY_PAGES:
        return

    st.session_state["_hm_reference_library_unavailable"] = True
    st.session_state["_hm_expected_login_role"] = "member"

    if (
        st.session_state.get("logged_in")
        and st.session_state.get("_hm_auth_role_resolved")
        and current_user_is_member()
    ):
        st.switch_page("pages/02_Member_Home.py")
        st.stop()

    st.session_state["_hm_requested_page_after_login"] = "pages/02_Member_Home.py"
    st.session_state["_hm_access_recovery_message"] = (
        "The Member Reference Library is currently unavailable. "
        "Please sign in with the member account to return to Member Home."
    )
    st.switch_page("pages/01_Login.py")
    st.stop()


def require_admin():
    restore_any_login("admin")
    if not st.session_state.get("logged_in"):
        _show_access_required("Admin")

    if (
        st.session_state.get("auth_login_method") == "supabase"
        or st.session_state.get("auth_provider") == "supabase"
    ):
        try:
            restore_supabase_login_from_session(force_refresh=True)
        except Exception:
            pass

    if not current_user_is_admin():
        _show_access_required("Admin")
    st.session_state["is_admin"] = True
    st.session_state["admin_logged_in"] = True


def require_member():
    current_page = _current_page_filename()
    _redirect_disabled_reference_page(current_page)

    restore_any_login("member")
    if not st.session_state.get("logged_in"):
        _show_access_required("Member")

    if (
        st.session_state.get("auth_login_method") == "supabase"
        or st.session_state.get("auth_provider") == "supabase"
    ):
        try:
            restore_supabase_login_from_session(force_refresh=True)
        except Exception:
            pass

    if not current_user_is_member():
        _show_access_required("Member")

    _apply_member_page_defaults(current_page)
    _apply_member_feature_visibility(current_page)
