from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import pytz
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
_COMMON_TIMEZONE_ORDER = [
    "Asia/Kolkata",
    "Europe/London",
    "Asia/Dubai",
    "Asia/Singapore",
    "America/New_York",
    "America/Chicago",
    "America/Los_Angeles",
    "Australia/Sydney",
]


def _valid_iana_timezone(value: object) -> bool:
    candidate = str(value or "").strip()
    if not candidate:
        return False
    try:
        ZoneInfo(candidate)
        return True
    except (ZoneInfoNotFoundError, ValueError):
        return False


def _timezone_country_map() -> dict[str, str]:
    mapping: dict[str, str] = {}
    for country_code, timezone_names in pytz.country_timezones.items():
        country_name = str(pytz.country_names.get(country_code) or country_code)
        for timezone_name in timezone_names:
            mapping.setdefault(str(timezone_name), country_name)
    return mapping


_TIMEZONE_COUNTRIES = _timezone_country_map()


def _friendly_timezone_label(timezone_name: object) -> str:
    """Display a human-readable location while retaining the IANA value."""
    value = str(timezone_name or "").strip()
    if not value:
        return "Select timezone"
    if value == "UTC":
        return "Coordinated Universal Time — UTC"

    parts = value.split("/")
    location = parts[-1].replace("_", " ") if parts else value
    country = _TIMEZONE_COUNTRIES.get(value, "")
    if country:
        return f"{location}, {country} — {value}"
    return f"{location} — {value}"


def _safe_timezone_options() -> list[str]:
    options: list[str] = []
    for timezone_name in _ORIGINAL_TIMEZONE_OPTIONS():
        candidate = str(timezone_name or "").strip()
        if candidate and _valid_iana_timezone(candidate) and candidate not in options:
            options.append(candidate)
    if "Asia/Kolkata" not in options:
        options.append("Asia/Kolkata")

    priority = {name: index for index, name in enumerate(_COMMON_TIMEZONE_ORDER)}
    return sorted(
        options,
        key=lambda name: (
            0 if name in priority else 1,
            priority.get(name, 9999),
            _friendly_timezone_label(name).lower(),
        ),
    )


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
        timezone_kwargs = dict(kwargs)
        # Streamlit searches against the formatted labels while still returning only
        # one of the approved IANA values. Arbitrary text can never be persisted.
        timezone_kwargs["format_func"] = _friendly_timezone_label
        selected_timezone = _BASE_SELECTBOX(
            "Practitioner scheduling timezone",
            options,
            *args,
            **timezone_kwargs,
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

# Make the long timezone list easier to navigate. The selector remains a closed
# approved-value control; typing only filters the dropdown options.
st.markdown(
    """
<style id="hm-friendly-timezone-selector-v1">
div[data-baseweb="popover"] [role="listbox"],
div[data-baseweb="popover"] ul{
  scrollbar-width:auto!important;
  scrollbar-color:#B89345 #FFF7E6!important;
}
div[data-baseweb="popover"] [role="listbox"]::-webkit-scrollbar,
div[data-baseweb="popover"] ul::-webkit-scrollbar{
  width:12px!important;
}
div[data-baseweb="popover"] [role="listbox"]::-webkit-scrollbar-track,
div[data-baseweb="popover"] ul::-webkit-scrollbar-track{
  background:#FFF7E6!important;
  border-radius:999px!important;
}
div[data-baseweb="popover"] [role="listbox"]::-webkit-scrollbar-thumb,
div[data-baseweb="popover"] ul::-webkit-scrollbar-thumb{
  background:#B89345!important;
  border:2px solid #FFF7E6!important;
  border-radius:999px!important;
}
div[data-baseweb="popover"] [role="option"]{
  line-height:1.28!important;
  padding-top:.58rem!important;
  padding-bottom:.58rem!important;
}
</style>
""",
    unsafe_allow_html=True,
)

schedule_timezone_ui.render_admin_scheduling_page()
