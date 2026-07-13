from datetime import date, datetime, time
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


def _normalise_12_hour_value(value):
    """Return a 12-hour HH:MM display value and AM/PM period."""
    if value in (None, ""):
        return None, None

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
        return None, None

    period = "PM" if hour >= 12 else "AM"
    display_hour = hour % 12 or 12
    return f"{display_hour:02d}:{minute:02d}", period


def _install_daily_log_time_input_wrapper() -> None:
    """Render Daily Log times as a 12-hour selector plus AM/PM selector."""
    wrapper_version = "daily-log-12h-select-v2"
    if getattr(st, "_hm_daily_log_time_input_version", "") == wrapper_version:
        return

    original_time_input = getattr(
        st,
        "_hm_daily_log_original_time_input",
        st.time_input,
    )
    st._hm_daily_log_original_time_input = original_time_input

    def daily_log_time_input(label, *args, **kwargs):
        if _current_page_filename() != "18_Daily_Log.py":
            return original_time_input(label, *args, **kwargs)

        if args:
            # Current Daily Log calls use keyword arguments. Keep any future
            # positional call on Streamlit's native widget rather than guessing.
            return original_time_input(label, *args, **kwargs)

        value = kwargs.pop("value", "now")
        key = kwargs.pop("key", None)
        help_text = kwargs.pop("help", None)
        disabled = bool(kwargs.pop("disabled", False))
        label_visibility = kwargs.pop("label_visibility", "visible")

        # Native time-input-only parameters do not apply to the two selectboxes.
        kwargs.pop("step", None)
        kwargs.pop("min_value", None)
        kwargs.pop("max_value", None)
        kwargs.pop("format", None)
        kwargs.pop("width", None)

        display_time, default_period = _normalise_12_hour_value(value)
        base_key = str(key or f"hm_daily_time_{abs(hash(str(label)))}")
        time_key = f"hm_daily_time12_v2_{base_key}"
        period_key = f"hm_daily_ampm_v2_{base_key}"

        time_placeholder = "Select time"
        period_placeholder = "Select AM/PM"
        time_options = [time_placeholder] + [
            f"{hour:02d}:{minute:02d}"
            for hour in range(1, 13)
            for minute in range(60)
        ]
        period_options = [period_placeholder, "AM", "PM"]

        selected_time_index = (
            time_options.index(display_time)
            if display_time in time_options
            else 0
        )
        selected_period_index = (
            period_options.index(default_period)
            if default_period in period_options
            else 0
        )

        time_col, period_col = st.columns([5.0, 1.35], gap="small")
        with time_col:
            selected_time = st.selectbox(
                label,
                time_options,
                index=selected_time_index,
                key=time_key,
                help=help_text,
                disabled=disabled,
                label_visibility=label_visibility,
            )
        with period_col:
            period = st.selectbox(
                "AM / PM",
                period_options,
                index=selected_period_index,
                key=period_key,
                disabled=disabled,
                label_visibility="hidden",
            )

        if selected_time == time_placeholder or period == period_placeholder:
            return None

        hour_12, minute_value = [
            int(part) for part in selected_time.split(":", 1)
        ]
        hour_24 = hour_12 % 12
        if period == "PM":
            hour_24 += 12
        return time(hour=hour_24, minute=minute_value)

    st.time_input = daily_log_time_input
    st._hm_daily_log_time_input_installed = True
    st._hm_daily_log_time_input_version = wrapper_version


def _apply_daily_log_ui_and_autosave(current_page: str) -> None:
    """Apply Daily Log-only controls, field borders and debounced autosave."""
    if current_page != "18_Daily_Log.py":
        return

    _install_daily_log_time_input_wrapper()

    st.markdown(
        """
        <style>
        /* Use the actual Streamlit widget-key class. Marker-sibling selectors
           are not reliable because Streamlit wraps each element separately. */
        [class*="st-key-hm_daily_toggle_"] button,
        [class*="st-key-hm_daily_toggle_"] [data-testid="stButton"] > button,
        [class*="st-key-hm_daily_toggle_"] .stButton > button{
          display:flex!important;
          width:100%!important;
          justify-content:flex-start!important;
          align-items:center!important;
          text-align:left!important;
          font-weight:950!important;
        }
        [class*="st-key-hm_daily_toggle_"] button > div,
        [class*="st-key-hm_daily_toggle_"] button p,
        [class*="st-key-hm_daily_toggle_"] button span,
        [class*="st-key-hm_daily_toggle_"] button *{
          width:100%!important;
          justify-content:flex-start!important;
          text-align:left!important;
          font-weight:950!important;
        }

        /* Put the border on the BaseWeb input shell, not on both the shell
           and the inner input. This removes the double vertical line. */
        html body #root [data-testid="stAppViewContainer"] div[data-testid="stTimeInput"] [data-baseweb="input"],
        html body #root [data-testid="stAppViewContainer"] div[data-testid="stTextInput"] [data-baseweb="input"]{
          border:1.2px solid #DCC690!important;
          border-radius:13px!important;
          background:#FFFFFF!important;
          box-shadow:none!important;
          overflow:visible!important;
          box-sizing:border-box!important;
          min-height:2.70rem!important;
        }
        html body #root [data-testid="stAppViewContainer"] div[data-testid="stTimeInput"] input,
        html body #root [data-testid="stAppViewContainer"] div[data-testid="stTextInput"] input{
          border:0!important;
          border-left:0!important;
          border-right:0!important;
          border-top:0!important;
          border-bottom:0!important;
          border-radius:0!important;
          outline:0!important;
          box-shadow:none!important;
          background:transparent!important;
          box-sizing:border-box!important;
          min-height:2.62rem!important;
        }
        html body #root [data-testid="stAppViewContainer"] div[data-testid="stTextInput"],
        html body #root [data-testid="stAppViewContainer"] div[data-testid="stTimeInput"]{
          overflow:visible!important;
          padding-bottom:.18rem!important;
        }
        html body #root [data-testid="stAppViewContainer"] div[data-testid="stHorizontalBlock"]:has(div[data-testid="stTextInput"]){
          overflow:visible!important;
          padding-bottom:.26rem!important;
        }

        /* The 12-hour time and AM/PM controls use the same visual treatment. */
        [class*="st-key-hm_daily_time12_v2_"] [data-baseweb="select"] > div,
        [class*="st-key-hm_daily_ampm_v2_"] [data-baseweb="select"] > div{
          min-height:2.70rem!important;
          height:2.70rem!important;
          border:1.2px solid #DCC690!important;
          border-radius:13px!important;
          background:#FFFFFF!important;
          box-shadow:none!important;
          box-sizing:border-box!important;
          padding-top:0!important;
          padding-bottom:0!important;
        }
        [class*="st-key-hm_daily_time12_v2_"] [data-baseweb="select"],
        [class*="st-key-hm_daily_ampm_v2_"] [data-baseweb="select"]{
          width:100%!important;
        }
        [class*="st-key-hm_daily_time12_v2_"] [data-baseweb="select"] *,
        [class*="st-key-hm_daily_ampm_v2_"] [data-baseweb="select"] *{
          line-height:1.3!important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    import streamlit.components.v1 as components

    components.html(
        r"""
        <script>
        (function(){
          let host;
          let doc;
          try {
            host = window.parent;
            doc = host.document;
          } catch (e) {
            return;
          }

          if (host.__healthyMeDailyLogAutosaveB29) return;
          host.__healthyMeDailyLogAutosaveB29 = true;

          let timer = null;
          let suppressUntil = 0;

          function widgetKey(target){
            if (!target || !target.closest) return "";
            const holder = target.closest('[class*="st-key-"]');
            if (!holder) return "";
            const keyClass = Array.from(holder.classList || []).find(function(name){
              return name.indexOf("st-key-") === 0;
            });
            return keyClass ? keyClass.substring(7) : "";
          }

          function isDailyLogEntryKey(key){
            if (!key) return false;
            if (key.indexOf("hm_daily_time12_v2_") === 0) return true;
            if (key.indexOf("hm_daily_ampm_v2_") === 0) return true;
            if (key.endsWith("_ampm")) return true;
            const mealField = /^\d{4}-\d{2}-\d{2}_(breakfast|lunch|evening_snack|dinner|bedtime|snacking_\d+)_(time|food_\d+|portion_\d+|mood|energy)$/;
            const dayField = /^hm_h9a4c_(water|fluid_(type|time|qty|notes)|poop_(rounds|time|feeling)|activity|notes)_\d{4}-\d{2}-\d{2}/;
            return mealField.test(key) || dayField.test(key);
          }

          function findSaveButton(){
            return Array.from(doc.querySelectorAll('button')).find(function(button){
              return (button.innerText || button.textContent || "").trim() === "Save Day" && !button.disabled;
            });
          }

          function queueAutosave(target){
            if (Date.now() < suppressUntil) return;
            const key = widgetKey(target);
            if (!isDailyLogEntryKey(key)) return;
            if (timer) host.clearTimeout(timer);
            timer = host.setTimeout(function(){
              const saveButton = findSaveButton();
              if (!saveButton) return;
              suppressUntil = Date.now() + 4500;
              saveButton.click();
            }, 1800);
          }

          doc.addEventListener("change", function(event){
            queueAutosave(event.target);
          }, true);
          doc.addEventListener("focusout", function(event){
            queueAutosave(event.target);
          }, true);
          doc.addEventListener("click", function(event){
            const button = event.target && event.target.closest ? event.target.closest("button") : null;
            if (!button) return;
            if ((button.innerText || button.textContent || "").trim() === "Save Day") {
              if (timer) host.clearTimeout(timer);
              suppressUntil = Date.now() + 4500;
            }
          }, true);
        })();
        </script>
        """,
        height=0,
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
    _apply_daily_log_ui_and_autosave(current_page)
