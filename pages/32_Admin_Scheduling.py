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
# even when that value is no longer one of its options. Cache the unwrapped base
# functions once, sanitize the choices and clear an invalid retained value.
_ORIGINAL_TIMEZONE_OPTIONS = getattr(
    schedule_timezone_ui,
    "_hm_base_timezone_options_before_sanitizer",
    schedule_timezone_ui.timezone_options,
)
schedule_timezone_ui._hm_base_timezone_options_before_sanitizer = (
    _ORIGINAL_TIMEZONE_OPTIONS
)
_ORIGINAL_PERSIST_PRACTITIONER_TIMEZONE = getattr(
    schedule_timezone_ui,
    "_hm_base_persist_practitioner_timezone_before_sanitizer",
    schedule_timezone_ui.persist_practitioner_timezone,
)
schedule_timezone_ui._hm_base_persist_practitioner_timezone_before_sanitizer = (
    _ORIGINAL_PERSIST_PRACTITIONER_TIMEZONE
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


# The scheduling component resolves the selected member before it resolves the
# practitioner timezone. Keep that data dependency intact while presenting the
# two controls in the requested order: practitioner timezone first, member second.
_BASE_SELECTBOX = getattr(
    st,
    "_hm_base_selectbox_before_schedule_control_order",
    st.selectbox,
)
st._hm_base_selectbox_before_schedule_control_order = _BASE_SELECTBOX
_PENDING_MEMBER_SELECTBOX = {}


def _selected_value_without_render(options: list, kwargs: dict):
    if not options:
        return None
    key = kwargs.get("key")
    retained = st.session_state.get(key) if key else None
    if retained in options:
        return retained
    raw_index = kwargs.get("index", 0)
    index = raw_index if isinstance(raw_index, int) else 0
    index = max(0, min(index, len(options) - 1))
    selected = options[index]
    if key:
        st.session_state[key] = selected
    return selected


def _selectbox_with_practitioner_timezone_first(
    label,
    options,
    *args,
    **kwargs,
):
    if label == "Select member controlling this page":
        member_options = list(options)
        selected = _selected_value_without_render(member_options, kwargs)
        _PENDING_MEMBER_SELECTBOX.clear()
        _PENDING_MEMBER_SELECTBOX.update(
            {
                "options": member_options,
                "args": args,
                "kwargs": dict(kwargs),
                "selected": selected,
            }
        )
        return selected

    if label == "Your scheduling timezone":
        selected_timezone = _BASE_SELECTBOX(
            "Practitioner scheduling timezone",
            options,
            *args,
            **kwargs,
        )
        if _PENDING_MEMBER_SELECTBOX:
            selected_member = _BASE_SELECTBOX(
                "Select member controlling this page",
                _PENDING_MEMBER_SELECTBOX["options"],
                *_PENDING_MEMBER_SELECTBOX["args"],
                **_PENDING_MEMBER_SELECTBOX["kwargs"],
            )
            if selected_member != _PENDING_MEMBER_SELECTBOX["selected"]:
                st.rerun()
        return selected_timezone

    return _BASE_SELECTBOX(label, options, *args, **kwargs)


st.selectbox = _selectbox_with_practitioner_timezone_first
schedule_timezone_ui.st.selectbox = _selectbox_with_practitioner_timezone_first


schedule_timezone_ui.render_admin_scheduling_page()
