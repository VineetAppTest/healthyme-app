import hashlib
import re
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
# an earlier Scheduling build can therefore reach the IANA timezone selector even
# when that value is no longer one of its options. Cache the unwrapped base
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
_TIMEZONE_SEARCH_KEY = "hm_tz_practitioner_timezone_search"
_TIMEZONE_SELECTION_READY_KEY = "hm_tz_practitioner_timezone_selection_ready"
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
_CITY_ALIASES_BY_TIMEZONE = {
    "Asia/Kolkata": (
        "Kolkata",
        "New Delhi",
        "Delhi",
        "Mumbai",
        "Lucknow",
        "Bengaluru",
        "Bangalore",
        "Chennai",
        "Hyderabad",
        "Pune",
        "Ahmedabad",
        "Jaipur",
        "Noida",
        "Gurugram",
        "Gurgaon",
    ),
    "Europe/London": (
        "London",
        "Manchester",
        "Birmingham",
        "Edinburgh",
        "Glasgow",
        "Liverpool",
        "Leeds",
        "Bristol",
    ),
    "Asia/Dubai": ("Dubai", "Abu Dhabi", "Sharjah", "Ajman"),
    "Asia/Singapore": ("Singapore",),
    "America/New_York": (
        "New York",
        "Boston",
        "Miami",
        "Washington DC",
        "Philadelphia",
        "Atlanta",
    ),
    "America/Chicago": (
        "Chicago",
        "Dallas",
        "Houston",
        "Austin",
        "Minneapolis",
        "New Orleans",
    ),
    "America/Denver": ("Denver", "Salt Lake City"),
    "America/Phoenix": ("Phoenix",),
    "America/Los_Angeles": (
        "Los Angeles",
        "San Francisco",
        "Seattle",
        "San Diego",
        "Portland",
        "Las Vegas",
    ),
    "America/Toronto": ("Toronto", "Ottawa"),
    "America/Vancouver": ("Vancouver", "Victoria"),
    "America/Edmonton": ("Edmonton", "Calgary"),
    "America/Winnipeg": ("Winnipeg",),
    "America/Halifax": ("Halifax",),
    "America/St_Johns": ("St Johns", "St. John's"),
    "Australia/Sydney": ("Sydney", "Canberra"),
    "Australia/Melbourne": ("Melbourne",),
    "Australia/Brisbane": ("Brisbane",),
    "Australia/Adelaide": ("Adelaide",),
    "Australia/Darwin": ("Darwin",),
    "Australia/Perth": ("Perth",),
    "Pacific/Auckland": ("Auckland", "Wellington"),
    "Asia/Tokyo": ("Tokyo", "Osaka", "Kyoto"),
    "Asia/Shanghai": ("Shanghai", "Beijing", "Shenzhen", "Guangzhou"),
    "Asia/Hong_Kong": ("Hong Kong",),
    "Europe/Paris": ("Paris",),
    "Europe/Berlin": ("Berlin", "Munich", "Frankfurt", "Hamburg"),
    "Europe/Rome": ("Rome", "Milan"),
    "Europe/Madrid": ("Madrid", "Barcelona"),
    "Europe/Amsterdam": ("Amsterdam",),
    "Europe/Zurich": ("Zurich", "Geneva"),
}
_COUNTRY_LABEL_OVERRIDES = {
    "Britain (UK)": "United Kingdom",
}


def _normalise_city(value: object) -> str:
    text = str(value or "").strip().lower()
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return " ".join(text.split())


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
        country_name = _COUNTRY_LABEL_OVERRIDES.get(country_name, country_name)
        for timezone_name in timezone_names:
            mapping.setdefault(str(timezone_name), country_name)
    return mapping


_TIMEZONE_COUNTRIES = _timezone_country_map()


def _iana_city_name(timezone_name: str) -> str:
    parts = str(timezone_name or "").split("/")
    return parts[-1].replace("_", " ") if len(parts) > 1 else ""


def _friendly_timezone_label(
    timezone_name: object,
    city_name: object = "",
) -> str:
    """Display the matched city, derived country and retained IANA timezone."""
    value = str(timezone_name or "").strip()
    if not value:
        return ""
    if value == "UTC":
        return "Coordinated Universal Time — UTC"

    location = str(city_name or "").strip() or _iana_city_name(value) or value
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


def _candidate_cities(timezone_name: str) -> list[str]:
    candidates: list[str] = []
    for city in _CITY_ALIASES_BY_TIMEZONE.get(timezone_name, ()):
        if city and city not in candidates:
            candidates.append(city)
    iana_city = _iana_city_name(timezone_name)
    if iana_city and iana_city not in candidates:
        candidates.append(iana_city)
    return candidates


def _match_city_timezones(
    options: list[str],
) -> tuple[list[str], dict[str, str]]:
    """Match only city names, then derive country and timezone from that city."""
    query = _normalise_city(st.session_state.get(_TIMEZONE_SEARCH_KEY))
    if not query:
        return [], {}

    ranked: list[tuple[int, str, str]] = []
    matched_city_by_timezone: dict[str, str] = {}
    for timezone_name in options:
        best_match: tuple[int, str] | None = None
        for city in _candidate_cities(timezone_name):
            city_key = _normalise_city(city)
            if not city_key:
                continue
            if query == city_key:
                score = 0
            elif city_key.startswith(query):
                score = 1
            elif query in city_key:
                score = 2
            else:
                continue
            if best_match is None or (score, city.lower()) < (
                best_match[0],
                best_match[1].lower(),
            ):
                best_match = (score, city)
        if best_match is not None:
            score, city = best_match
            ranked.append((score, city.lower(), timezone_name))
            matched_city_by_timezone[timezone_name] = city

    ranked.sort(
        key=lambda item: (
            item[0],
            item[1],
            _TIMEZONE_COUNTRIES.get(item[2], "").lower(),
            item[2].lower(),
        )
    )
    return [item[2] for item in ranked], matched_city_by_timezone


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


_BASE_MARKDOWN = getattr(
    st,
    "_hm_base_markdown_before_schedule_subtitle_removal",
    st.markdown,
)
st._hm_base_markdown_before_schedule_subtitle_removal = _BASE_MARKDOWN
_REMOVED_CONTEXT_SUBTITLE = (
    "<div class='hm-tz-context-sub'>All schedule creation, status, reschedule "
    "review and session usage below are for the selected member only.</div>"
)
_PRACTITIONER_TIMEZONE_STATUS_PREFIX = (
    "<div class='hm-schedule-muted'>Practitioner timezone:"
)


def _schedule_markdown_with_blank_unselected_timezone(body, *args, **kwargs):
    rendered = str(body or "")
    if rendered == _REMOVED_CONTEXT_SUBTITLE:
        return None
    if (
        rendered.startswith(_PRACTITIONER_TIMEZONE_STATUS_PREFIX)
        and not st.session_state.get(_TIMEZONE_SELECTION_READY_KEY, False)
    ):
        member_suffix = ""
        marker = " · Member timezone:"
        if marker in rendered:
            member_suffix = marker + rendered.split(marker, 1)[1]
        rendered = (
            "<div class='hm-schedule-muted'>Practitioner timezone: "
            "<b>Not selected</b>"
            f"{member_suffix}"
        )
    return _BASE_MARKDOWN(rendered, *args, **kwargs)


st.markdown = _schedule_markdown_with_blank_unselected_timezone
schedule_timezone_ui.st.markdown = _schedule_markdown_with_blank_unselected_timezone


# The scheduling component resolves the selected member before it resolves the
# practitioner timezone. Keep that data dependency intact while presenting the
# practitioner controls first and the member selector immediately afterwards.
_BASE_SELECTBOX = getattr(
    st,
    "_hm_base_selectbox_before_schedule_control_order",
    st.selectbox,
)
st._hm_base_selectbox_before_schedule_control_order = _BASE_SELECTBOX
_BASE_RADIO = getattr(
    st,
    "_hm_base_radio_before_practitioner_timezone_required",
    st.radio,
)
st._hm_base_radio_before_practitioner_timezone_required = _BASE_RADIO
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


def _lock_timezone_dropdown_typing() -> None:
    """Keep the timezone output controlled; city search is the only text input."""
    st.html(
        """
<script>
(() => {
  let root;
  try { root = window.parent.document; } catch (_error) { root = document; }
  const lock = () => {
    const inputs = root.querySelectorAll(
      'input[aria-label="Practitioner scheduling timezone"]'
    );
    inputs.forEach((input) => {
      input.readOnly = true;
      input.setAttribute('inputmode', 'none');
      input.setAttribute('autocomplete', 'off');
      input.style.cursor = 'pointer';
    });
  };
  lock();
  if (!root.body.__hmTimezoneReadonlyObserver) {
    const observer = new MutationObserver(lock);
    observer.observe(root.body, {childList: true, subtree: true});
    root.body.__hmTimezoneReadonlyObserver = observer;
  }
})();
</script>
""",
        unsafe_allow_javascript=True,
    )


def _render_timezone_search_status(message: str) -> None:
    st.markdown(
        f"<div class='hm-tz-search-status'>{message}</div>",
        unsafe_allow_html=True,
    )


def _city_query_widget_key(query: object) -> str:
    digest = hashlib.sha1(
        _normalise_city(query).encode("utf-8")
    ).hexdigest()[:10]
    return f"hm_tz_practitioner_timezone_city_{digest}"


def _selectbox_with_city_first_practitioner_timezone(
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
        all_options = list(options)
        original_index = kwargs.get("index", 0)
        original_index = original_index if isinstance(original_index, int) else 0
        original_index = max(0, min(original_index, len(all_options) - 1))
        retained = st.session_state.get(_TIMEZONE_WIDGET_KEY)
        current_value = retained if retained in all_options else all_options[original_index]

        st.text_input(
            "Search practitioner timezone",
            key=_TIMEZONE_SEARCH_KEY,
            placeholder="Type the practitioner city",
            help=(
                "HealthyMe matches the city first, derives the country, and then "
                "evaluates the valid IANA timezone. Country names alone are not used."
            ),
        )
        query = str(st.session_state.get(_TIMEZONE_SEARCH_KEY) or "").strip()
        matching_timezones, matched_cities = _match_city_timezones(all_options)

        timezone_kwargs = dict(kwargs)
        timezone_kwargs["key"] = _city_query_widget_key(query)
        timezone_kwargs["format_func"] = lambda timezone_name: (
            _friendly_timezone_label(
                timezone_name,
                matched_cities.get(timezone_name, ""),
            )
        )

        selected_timezone = None
        if not query:
            timezone_kwargs["index"] = None
            timezone_kwargs["placeholder"] = "Search for a practitioner city first"
            selected_timezone = _BASE_SELECTBOX(
                "Practitioner scheduling timezone",
                [],
                *args,
                **timezone_kwargs,
            )
            _render_timezone_search_status(
                "Enter a city to derive the country and practitioner timezone."
            )
        elif not matching_timezones:
            timezone_kwargs["index"] = None
            timezone_kwargs["placeholder"] = "No matching city found"
            selected_timezone = _BASE_SELECTBOX(
                "Practitioner scheduling timezone",
                [],
                *args,
                **timezone_kwargs,
            )
            _render_timezone_search_status(
                "No matching city found. Practitioner scheduling timezone remains empty."
            )
        else:
            timezone_kwargs["index"] = 0 if len(matching_timezones) == 1 else None
            timezone_kwargs["placeholder"] = (
                "Select the derived timezone"
                if len(matching_timezones) > 1
                else None
            )
            selected_timezone = _BASE_SELECTBOX(
                "Practitioner scheduling timezone",
                matching_timezones,
                *args,
                **timezone_kwargs,
            )
            if len(matching_timezones) > 1 and not selected_timezone:
                _render_timezone_search_status(
                    "More than one city match was found. Select the correct derived timezone."
                )

        selection_ready = bool(selected_timezone)
        st.session_state[_TIMEZONE_SELECTION_READY_KEY] = selection_ready
        if selection_ready:
            st.session_state[_TIMEZONE_WIDGET_KEY] = selected_timezone
        else:
            st.session_state.pop(_TIMEZONE_WIDGET_KEY, None)

        _lock_timezone_dropdown_typing()

        if _PENDING_MEMBER_SELECTBOX:
            selected_member = _BASE_SELECTBOX(
                "Select member controlling this page",
                _PENDING_MEMBER_SELECTBOX["options"],
                *_PENDING_MEMBER_SELECTBOX["args"],
                **_PENDING_MEMBER_SELECTBOX["kwargs"],
            )
            if selected_member != _PENDING_MEMBER_SELECTBOX["selected"]:
                st.rerun()

        # Preserve the underlying component's current valid value only to complete
        # rendering safely. The visible field remains blank and schedule actions are
        # blocked below until a city-derived timezone is selected.
        return selected_timezone or current_value

    return _BASE_SELECTBOX(label, options, *args, **kwargs)


def _radio_require_city_derived_timezone(label, options, *args, **kwargs):
    if (
        label == "Enter the schedule in"
        and not st.session_state.get(_TIMEZONE_SELECTION_READY_KEY, False)
    ):
        st.info(
            "Search for the practitioner city and confirm the derived timezone to continue."
        )
        st.stop()
    return _BASE_RADIO(label, options, *args, **kwargs)


st.selectbox = _selectbox_with_city_first_practitioner_timezone
schedule_timezone_ui.st.selectbox = _selectbox_with_city_first_practitioner_timezone
st.radio = _radio_require_city_derived_timezone
schedule_timezone_ui.st.radio = _radio_require_city_derived_timezone

# Keep city search and its derived timezone visually grouped while making the long
# timezone result list easy to navigate.
st.markdown(
    """
<style id="hm-friendly-timezone-selector-v4">
.st-key-hm_tz_practitioner_timezone_search{
  margin-top:.48rem!important;
  margin-bottom:-.42rem!important;
}
[class*="st-key-hm_tz_practitioner_timezone_city_"]{
  margin-top:0!important;
  margin-bottom:0!important;
}
.hm-tz-search-status{
  margin:-.36rem 0 .14rem 0!important;
  color:#7A6A55!important;
  font-size:.78rem!important;
  font-weight:650!important;
  line-height:1.25!important;
}
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
