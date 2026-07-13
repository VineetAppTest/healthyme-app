from datetime import date, datetime, time
import inspect
import time as time_module

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
    """Restore only the authentication provider appropriate for the requested role."""
    normalized_role = str(required_role or "").strip().lower()

    if st.session_state.get("logged_in") and st.session_state.get(
        "_hm_auth_role_resolved"
    ):
        st.session_state.pop("_hm_member_restore_retry", None)
        return True

    restored = False
    if supabase_auth_enabled():
        try:
            restored = restore_supabase_login_from_session()
        except Exception:
            restored = False

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
    if restored:
        st.session_state.pop("_hm_member_restore_retry", None)
    return bool(restored)


def _current_page_filename() -> str:
    """Return the active Streamlit page filename without URL parsing."""
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
        if st.button(
            "Go to Login",
            key=f"hm_go_to_login_{normalized_role or 'user'}",
        ):
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
    """Apply Member Home spacing and hide disabled library widgets."""
    if current_page != "02_Member_Home.py":
        return
    st.markdown(
        """
        <style>
        header[data-testid="stHeader"],[data-testid="stToolbar"],[data-testid="stDecoration"],[data-testid="stStatusWidget"]{display:none!important;visibility:hidden!important;height:0!important;min-height:0!important;margin:0!important;padding:0!important;}
        html body [data-testid="stAppViewContainer"],html body [data-testid="stMain"],html body section.main{padding-top:0!important;margin-top:0!important;}
        html body [data-testid="stMainBlockContainer"],html body [data-testid="stAppViewBlockContainer"],html body section.main>div.block-container,html body .main .block-container,html body .stMainBlockContainer,html body .block-container{padding-top:0!important;margin-top:0!important;}
        div[data-testid="stElementContainer"]:has(>div[data-testid="stMarkdownContainer"]>style),div[data-testid="stElementContainer"]:has(>div>div[data-testid="stMarkdownContainer"]>style){height:0!important;min-height:0!important;margin:0!important;padding:0!important;overflow:hidden!important;}
        .st-key-hm_home_recipe_repo,.st-key-hm_home_exercise_repo,.st-key-hm_home_supplements{display:none!important;height:0!important;min-height:0!important;margin:0!important;padding:0!important;overflow:hidden!important;}
        div[data-testid="stElementContainer"]:has(>div[data-testid="stMarkdownContainer"] .hm-home-reference-title),div[data-testid="stElementContainer"]:has(>div>div[data-testid="stMarkdownContainer"] .hm-home-reference-title),div[data-testid="stElementContainer"]:has(>div[data-testid="stMarkdownContainer"] .hm-home-muted-anchor),div[data-testid="stElementContainer"]:has(>div>div[data-testid="stMarkdownContainer"] .hm-home-muted-anchor),div[data-testid="stElementContainer"]:has(>div[data-testid="stMarkdownContainer"] .hm-home-muted-anchor)+div[data-testid="stElementContainer"],div[data-testid="stElementContainer"]:has(>div>div[data-testid="stMarkdownContainer"] .hm-home-muted-anchor)+div[data-testid="stElementContainer"]{display:none!important;height:0!important;min-height:0!important;margin:0!important;padding:0!important;overflow:hidden!important;}
        </style>
        """,
        unsafe_allow_html=True,
    )


def _normalise_12_hour_value(value):
    """Return a 12-hour hour, minute and AM/PM period."""
    if value in (None, ""):
        return None, None, None
    if value == "now":
        value = datetime.now().time()
    elif isinstance(value, str):
        parsed = None
        for fmt in ("%H:%M", "%I:%M %p", "%I %p"):
            try:
                parsed = datetime.strptime(value.strip(), fmt).time()
                break
            except Exception:
                pass
        value = parsed
    hour = getattr(value, "hour", None)
    minute = getattr(value, "minute", None)
    if hour is None or minute is None:
        return None, None, None
    period = "PM" if hour >= 12 else "AM"
    display_hour = hour % 12 or 12
    return f"{display_hour:02d}", f"{minute:02d}", period


def _install_daily_log_time_input_wrapper() -> None:
    """Render Daily Log times as HH, MM and AM/PM in one compact row."""
    wrapper_version = "daily-log-hh-mm-select-v12-no-colon-wider"
    if getattr(st, "_hm_daily_log_time_input_version", "") == wrapper_version:
        return

    original_time_input = getattr(
        st,
        "_hm_daily_log_original_time_input",
        st.time_input,
    )
    st._hm_daily_log_original_time_input = original_time_input

    def daily_log_time_input(label, *args, **kwargs):
        if _current_page_filename() != "18_Daily_Log.py" or args:
            return original_time_input(label, *args, **kwargs)

        value = kwargs.pop("value", "now")
        key = kwargs.pop("key", None)
        help_text = kwargs.pop("help", None)
        disabled = bool(kwargs.pop("disabled", False))
        for option_name in (
            "label_visibility",
            "step",
            "min_value",
            "max_value",
            "format",
            "width",
        ):
            kwargs.pop(option_name, None)

        default_hour, default_minute, default_period = _normalise_12_hour_value(value)
        base_key = str(key or f"hm_daily_time_{abs(hash(str(label)))}")
        hour_key = f"hm_daily_hour_v12_{base_key}"
        minute_key = f"hm_daily_minute_v12_{base_key}"
        period_key = f"hm_daily_ampm_v12_{base_key}"

        hour_placeholder, minute_placeholder, period_placeholder = "HH", "MM", "AM/PM"
        hour_options = [hour_placeholder] + [f"{hour:02d}" for hour in range(1, 13)]
        minute_options = [minute_placeholder] + [f"{minute:02d}" for minute in range(60)]
        period_options = [period_placeholder, "AM", "PM"]

        hour_index = hour_options.index(default_hour) if default_hour in hour_options else 0
        minute_index = minute_options.index(default_minute) if default_minute in minute_options else 0
        period_index = period_options.index(default_period) if default_period in period_options else 0

        st.markdown(
            """
            <div class='hm-daily-time-headings' aria-hidden='true'>
              <span>Hour</span><span>Minutes</span><span>AM/PM</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

        hour_col, minute_col, period_col = st.columns(
            [1.08, 1.08, 1.36],
            gap="small",
        )
        with hour_col:
            selected_hour = st.selectbox(
                "",
                hour_options,
                index=hour_index,
                key=hour_key,
                help=help_text,
                disabled=disabled,
                label_visibility="collapsed",
            )
        with minute_col:
            selected_minute = st.selectbox(
                "",
                minute_options,
                index=minute_index,
                key=minute_key,
                disabled=disabled,
                label_visibility="collapsed",
            )
        with period_col:
            selected_period = st.selectbox(
                "",
                period_options,
                index=period_index,
                key=period_key,
                disabled=disabled,
                label_visibility="collapsed",
            )

        if (
            selected_hour == hour_placeholder
            or selected_minute == minute_placeholder
            or selected_period == period_placeholder
        ):
            return None

        hour_12 = int(selected_hour)
        minute_value = int(selected_minute)
        hour_24 = hour_12 % 12
        if selected_period == "PM":
            hour_24 += 12
        return time(hour=hour_24, minute=minute_value)

    st.time_input = daily_log_time_input
    st._hm_daily_log_time_input_installed = True
    st._hm_daily_log_time_input_version = wrapper_version


def _apply_daily_log_ui_and_autosave(current_page: str) -> None:
    """Apply lightweight Daily Log controls without DOM-wide autosave scripts."""
    if current_page != "18_Daily_Log.py":
        return
    _install_daily_log_time_input_wrapper()
    st.markdown(
        """
        <style>
        [class*="st-key-hm_daily_toggle_"] button,[class*="st-key-hm_daily_toggle_"] [data-testid="stButton"]>button,[class*="st-key-hm_daily_toggle_"] .stButton>button{display:flex!important;width:100%!important;justify-content:flex-start!important;align-items:center!important;text-align:left!important;font-weight:950!important;}
        [class*="st-key-hm_daily_toggle_"] button *{width:100%!important;justify-content:flex-start!important;text-align:left!important;font-weight:950!important;}
        .hm-daily-time-headings{display:grid!important;grid-template-columns:minmax(0,1.08fr) minmax(0,1.08fr) minmax(0,1.36fr)!important;column-gap:.55rem!important;align-items:end!important;width:100%!important;margin:0 0 .28rem 0!important;color:#334155!important;font-size:.86rem!important;line-height:1.2!important;font-weight:650!important;white-space:nowrap!important;}
        [class*="st-key-hm_daily_hour_v12_"] [data-testid="stWidgetLabel"],[class*="st-key-hm_daily_minute_v12_"] [data-testid="stWidgetLabel"],[class*="st-key-hm_daily_ampm_v12_"] [data-testid="stWidgetLabel"],[class*="st-key-hm_daily_hour_v12_"] label,[class*="st-key-hm_daily_minute_v12_"] label,[class*="st-key-hm_daily_ampm_v12_"] label{display:none!important;height:0!important;min-height:0!important;margin:0!important;padding:0!important;overflow:hidden!important;}
        html body #root [data-testid="stAppViewContainer"] div[data-testid="stTextInput"] [data-baseweb="input"]{border:1.2px solid #DCC690!important;border-radius:13px!important;background:#FFFFFF!important;box-shadow:none!important;overflow:visible!important;box-sizing:border-box!important;min-height:2.70rem!important;}
        html body #root [data-testid="stAppViewContainer"] div[data-testid="stTextInput"] input{border:0!important;outline:0!important;box-shadow:none!important;background:transparent!important;color:#334155!important;min-height:2.62rem!important;}
        html body #root [data-testid="stAppViewContainer"] [class*="st-key-hm_daily_hour_v12_"] [data-baseweb="select"]>div,html body #root [data-testid="stAppViewContainer"] [class*="st-key-hm_daily_minute_v12_"] [data-baseweb="select"]>div,html body #root [data-testid="stAppViewContainer"] [class*="st-key-hm_daily_ampm_v12_"] [data-baseweb="select"]>div{display:flex!important;align-items:center!important;min-height:2.78rem!important;height:2.78rem!important;border:1.2px solid #DCC690!important;border-radius:13px!important;background:#FFFFFF!important;box-shadow:none!important;box-sizing:border-box!important;padding:0 .64rem!important;color:#475569!important;opacity:1!important;}
        html body #root [data-testid="stAppViewContainer"] [class*="st-key-hm_daily_hour_v12_"] [data-baseweb="select"] *,html body #root [data-testid="stAppViewContainer"] [class*="st-key-hm_daily_minute_v12_"] [data-baseweb="select"] *,html body #root [data-testid="stAppViewContainer"] [class*="st-key-hm_daily_ampm_v12_"] [data-baseweb="select"] *{color:#475569!important;opacity:1!important;visibility:visible!important;font-size:.88rem!important;line-height:1.15!important;}
        div[data-testid="stHorizontalBlock"]:has([class*="st-key-hm_daily_hour_v12_"]){display:grid!important;grid-template-columns:minmax(0,1.08fr) minmax(0,1.08fr) minmax(0,1.36fr)!important;column-gap:.55rem!important;row-gap:0!important;align-items:center!important;width:100%!important;flex-wrap:nowrap!important;}
        div[data-testid="stHorizontalBlock"]:has([class*="st-key-hm_daily_hour_v12_"])>div[data-testid="column"]{width:auto!important;min-width:0!important;max-width:none!important;flex:none!important;align-self:center!important;margin:0!important;padding:0!important;}
        @media(max-width:640px){
          .hm-daily-time-headings,div[data-testid="stHorizontalBlock"]:has([class*="st-key-hm_daily_hour_v12_"]){grid-template-columns:minmax(0,1fr) minmax(0,1fr) minmax(0,1.28fr)!important;column-gap:.34rem!important;}
          .hm-daily-time-headings{font-size:.76rem!important;}
          html body #root [data-testid="stAppViewContainer"] [class*="st-key-hm_daily_hour_v12_"] [data-baseweb="select"]>div,html body #root [data-testid="stAppViewContainer"] [class*="st-key-hm_daily_minute_v12_"] [data-baseweb="select"]>div,html body #root [data-testid="stAppViewContainer"] [class*="st-key-hm_daily_ampm_v12_"] [data-baseweb="select"]>div{min-width:0!important;width:100%!important;padding:0 .42rem!important;}
          html body #root [data-testid="stAppViewContainer"] [class*="st-key-hm_daily_ampm_v12_"] [data-baseweb="select"] *{font-size:.74rem!important;}
          div[data-testid="stHorizontalBlock"]:has(div[data-testid="stTextInput"]){row-gap:0!important;margin-bottom:.04rem!important;}
          div[data-testid="stHorizontalBlock"]:has(div[data-testid="stTextInput"])>div[data-testid="column"]{margin-bottom:.04rem!important;padding-bottom:0!important;}
          div[data-testid="stHorizontalBlock"]:has(div[data-testid="stTextInput"]) div[data-testid="stElementContainer"]{margin-bottom:.04rem!important;}
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
    if not current_user_is_admin():
        _show_access_required("Admin")
    st.session_state["is_admin"] = True
    st.session_state["admin_logged_in"] = True


def require_member():
    current_page = _current_page_filename()
    _redirect_disabled_reference_page(current_page)

    restore_any_login("member")
    if not st.session_state.get("logged_in"):
        if not st.session_state.get("_hm_member_restore_retry"):
            st.session_state["_hm_member_restore_retry"] = True
            time_module.sleep(0.35)
            st.rerun()
        _show_access_required("Member")
    st.session_state.pop("_hm_member_restore_retry", None)

    if not current_user_is_member():
        _show_access_required("Member")

    _apply_member_page_defaults(current_page)
    _apply_member_feature_visibility(current_page)
    _apply_daily_log_ui_and_autosave(current_page)
