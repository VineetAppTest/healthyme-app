from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import streamlit as st

from components import guards, ui_common
import components.schedule_timezone_ui as schedule_timezone_ui


schedule_timezone_ui.require_admin = guards.require_admin
schedule_timezone_ui.require_member = guards.require_member
schedule_timezone_ui.inject_global_styles = ui_common.inject_global_styles
schedule_timezone_ui.apply_luxe_theme = ui_common.apply_luxe_theme
schedule_timezone_ui.utility_logout_bar = ui_common.utility_logout_bar
schedule_timezone_ui.render_back_to_top = ui_common.render_back_to_top
schedule_timezone_ui.topbar = ui_common.topbar
schedule_timezone_ui.render_page_nav = ui_common.render_page_nav


# Streamlit keeps widget values across reruns and deployments. A stale value from
# an earlier Scheduling build can therefore reach the new IANA timezone selector
# even when that value is no longer one of its options. Sanitize both the available
# choices and the retained widget value before the page renders.
_ORIGINAL_TIMEZONE_OPTIONS = schedule_timezone_ui.timezone_options
_ORIGINAL_PERSIST_PRACTITIONER_TIMEZONE = (
    schedule_timezone_ui.persist_practitioner_timezone
)
_TIMEZONE_WIDGET_KEY = "hm_tz_practitioner_timezone"


def _valid_iana_timezone(value: object) -> bool:
    candidate = str(value or "").strip()
    if not candidate:
        return False
    try:
        ZoneInfo(candidate)
        return True
    except (ZoneInfoNotFoundError, ValueError):
        return False


def _safe_timezone_options() -> list[str]:
    options = []
    for timezone_name in _ORIGINAL_TIMEZONE_OPTIONS():
        candidate = str(timezone_name or "").strip()
        if candidate and _valid_iana_timezone(candidate) and candidate not in options:
            options.append(candidate)
    if "Asia/Kolkata" not in options:
        options.insert(0, "Asia/Kolkata")
    return options


def _safe_persist_practitioner_timezone(
    user_id: object,
    timezone_name: object,
) -> str:
    candidate = str(timezone_name or "").strip()
    if candidate not in _safe_timezone_options():
        st.session_state.pop(_TIMEZONE_WIDGET_KEY, None)
        return schedule_timezone_ui.practitioner_timezone_name(
            user_id,
            persist=True,
        )
    return _ORIGINAL_PERSIST_PRACTITIONER_TIMEZONE(user_id, candidate)


schedule_timezone_ui.timezone_options = _safe_timezone_options
schedule_timezone_ui.persist_practitioner_timezone = (
    _safe_persist_practitioner_timezone
)

_retained_timezone = st.session_state.get(_TIMEZONE_WIDGET_KEY)
if _retained_timezone is not None and str(_retained_timezone) not in _safe_timezone_options():
    st.session_state.pop(_TIMEZONE_WIDGET_KEY, None)


schedule_timezone_ui.render_admin_scheduling_page()
