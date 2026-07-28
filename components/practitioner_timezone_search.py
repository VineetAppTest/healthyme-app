from __future__ import annotations

import hashlib
import re
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import pytz
import streamlit as st

from components import guards, ui_common
import components.schedule_timezone_ui as schedule_timezone_ui


SEARCH_KEY = "hm_tz_practitioner_timezone_search"
VISIBLE_TIMEZONE_KEY = "hm_tz_practitioner_timezone"
SELECTION_READY_KEY = "hm_tz_practitioner_timezone_selection_ready"

COUNTRY_NAME_OVERRIDES = {"Britain (UK)": "United Kingdom"}

CITY_ALIASES_BY_TIMEZONE = {
    "Asia/Kolkata": (
        "Kolkata", "New Delhi", "Delhi", "Mumbai", "Lucknow", "Bengaluru",
        "Bangalore", "Chennai", "Hyderabad", "Pune", "Ahmedabad", "Jaipur",
        "Noida", "Gurugram", "Gurgaon",
    ),
    "Europe/London": (
        "London", "Manchester", "Birmingham", "Edinburgh", "Glasgow",
        "Liverpool", "Leeds", "Bristol",
    ),
    "Asia/Dubai": ("Dubai", "Abu Dhabi", "Sharjah", "Ajman"),
    "Asia/Singapore": ("Singapore",),
    "America/New_York": (
        "New York", "Boston", "Miami", "Washington DC", "Philadelphia", "Atlanta",
    ),
    "America/Chicago": (
        "Chicago", "Dallas", "Houston", "Austin", "Minneapolis", "New Orleans",
    ),
    "America/Denver": ("Denver", "Salt Lake City"),
    "America/Phoenix": ("Phoenix",),
    "America/Los_Angeles": (
        "Los Angeles", "San Francisco", "Seattle", "San Diego", "Portland", "Las Vegas",
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

COMMON_TIMEZONE_ORDER = [
    "Asia/Kolkata", "Europe/London", "Asia/Dubai", "Asia/Singapore",
    "America/New_York", "America/Chicago", "America/Los_Angeles", "Australia/Sydney",
]


def _normalise(value: object) -> str:
    text = str(value or "").strip().lower()
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return " ".join(text.split())


def _valid_timezone(value: object) -> bool:
    candidate = str(value or "").strip()
    if not candidate:
        return False
    try:
        ZoneInfo(candidate)
        return True
    except (ZoneInfoNotFoundError, ValueError):
        return False


def _country_by_timezone() -> dict[str, str]:
    result: dict[str, str] = {}
    for country_code, timezone_names in pytz.country_timezones.items():
        country = str(pytz.country_names.get(country_code) or country_code)
        country = COUNTRY_NAME_OVERRIDES.get(country, country)
        for timezone_name in timezone_names:
            result.setdefault(str(timezone_name), country)
    return result


COUNTRY_BY_TIMEZONE = _country_by_timezone()


def _iana_city(timezone_name: str) -> str:
    parts = str(timezone_name or "").split("/")
    return parts[-1].replace("_", " ") if len(parts) > 1 else ""


def _cities_for_timezone(timezone_name: str) -> list[str]:
    values: list[str] = []
    for city in CITY_ALIASES_BY_TIMEZONE.get(timezone_name, ()):
        if city and city not in values:
            values.append(city)
    iana_city = _iana_city(timezone_name)
    if iana_city and iana_city not in values:
        values.append(iana_city)
    return values


def _friendly_label(timezone_name: object, city_name: object = "") -> str:
    value = str(timezone_name or "").strip()
    if not value:
        return ""
    if value == "UTC":
        return "Coordinated Universal Time — UTC"
    city = str(city_name or "").strip() or _iana_city(value) or value
    country = COUNTRY_BY_TIMEZONE.get(value, "")
    return f"{city}, {country} — {value}" if country else f"{city} — {value}"


def _safe_timezone_options(base_options) -> list[str]:
    options: list[str] = []
    for value in base_options():
        candidate = str(value or "").strip()
        if candidate and _valid_timezone(candidate) and candidate not in options:
            options.append(candidate)
    priority = {name: index for index, name in enumerate(COMMON_TIMEZONE_ORDER)}
    return sorted(
        options,
        key=lambda name: (
            0 if name in priority else 1,
            priority.get(name, 9999),
            _friendly_label(name).lower(),
        ),
    )


def _match_search(options: list[str], query_value: object) -> tuple[list[str], dict[str, str]]:
    """Accept city, country or IANA input and return city-based timezone choices."""
    query = _normalise(query_value)
    if not query:
        return [], {}

    ranked: list[tuple[int, str, str]] = []
    matched_city: dict[str, str] = {}

    for timezone_name in options:
        country = COUNTRY_BY_TIMEZONE.get(timezone_name, "")
        timezone_key = _normalise(timezone_name)
        country_key = _normalise(country)
        candidate_cities = _cities_for_timezone(timezone_name)

        best: tuple[int, str] | None = None
        for city in candidate_cities:
            city_key = _normalise(city)
            if query == city_key:
                score = 0
            elif city_key.startswith(query):
                score = 1
            elif query in city_key:
                score = 2
            else:
                continue
            candidate = (score, city)
            if best is None or (candidate[0], candidate[1].lower()) < (
                best[0], best[1].lower()
            ):
                best = candidate

        if best is None:
            if query == timezone_key:
                best = (3, _iana_city(timezone_name))
            elif timezone_key.startswith(query) or query in timezone_key:
                best = (4, _iana_city(timezone_name))
            elif query == country_key:
                best = (5, candidate_cities[0] if candidate_cities else _iana_city(timezone_name))
            elif country_key.startswith(query) or query in country_key:
                best = (6, candidate_cities[0] if candidate_cities else _iana_city(timezone_name))

        if best is not None:
            score, city = best
            ranked.append((score, city.lower(), timezone_name))
            matched_city[timezone_name] = city

    ranked.sort(
        key=lambda item: (
            item[0],
            COUNTRY_BY_TIMEZONE.get(item[2], "").lower(),
            item[1],
            item[2].lower(),
        )
    )
    return [item[2] for item in ranked], matched_city


def _query_widget_key(query: object) -> str:
    digest = hashlib.sha1(_normalise(query).encode("utf-8")).hexdigest()[:10]
    return f"hm_tz_practitioner_timezone_result_{digest}"


def install() -> None:
    schedule_timezone_ui.require_admin = guards.require_admin
    schedule_timezone_ui.require_member = guards.require_member
    schedule_timezone_ui.inject_global_styles = ui_common.inject_global_styles
    schedule_timezone_ui.apply_luxe_theme = ui_common.apply_luxe_theme
    schedule_timezone_ui.utility_logout_bar = ui_common.utility_logout_bar
    schedule_timezone_ui.render_back_to_top = ui_common.render_back_to_top
    schedule_timezone_ui.topbar = ui_common.topbar
    schedule_timezone_ui.render_page_nav = ui_common.render_page_nav

    base_timezone_options = getattr(
        schedule_timezone_ui,
        "_hm_base_timezone_options_before_unified_search",
        schedule_timezone_ui.timezone_options,
    )
    schedule_timezone_ui._hm_base_timezone_options_before_unified_search = base_timezone_options
    schedule_timezone_ui.timezone_options = lambda: _safe_timezone_options(base_timezone_options)

    base_selectbox = getattr(
        st,
        "_hm_base_selectbox_before_unified_timezone_search",
        st.selectbox,
    )
    st._hm_base_selectbox_before_unified_timezone_search = base_selectbox
    base_radio = getattr(
        st,
        "_hm_base_radio_before_unified_timezone_search",
        st.radio,
    )
    st._hm_base_radio_before_unified_timezone_search = base_radio
    pending_member: dict[str, object] = {}

    def selected_without_render(options: list, kwargs: dict):
        if not options:
            return None
        key = kwargs.get("key")
        retained = st.session_state.get(key) if key else None
        if retained in options:
            return retained
        index = kwargs.get("index", 0)
        index = index if isinstance(index, int) else 0
        index = max(0, min(index, len(options) - 1))
        selected = options[index]
        if key:
            st.session_state[key] = selected
        return selected

    def patched_selectbox(label, options, *args, **kwargs):
        if label == "Select member controlling this page":
            option_list = list(options)
            selected = selected_without_render(option_list, kwargs)
            pending_member.clear()
            pending_member.update(
                {"options": option_list, "args": args, "kwargs": dict(kwargs), "selected": selected}
            )
            return selected

        if label == "Your scheduling timezone":
            all_options = list(options)
            st.text_input(
                "Search practitioner timezone",
                key=SEARCH_KEY,
                placeholder="Type a city, country or timezone",
                help=(
                    "HealthyMe first maps the entered text to matching cities, then derives "
                    "the country and valid IANA timezone."
                ),
            )
            query = str(st.session_state.get(SEARCH_KEY) or "").strip()
            matches, city_map = _match_search(all_options, query)

            result_kwargs = dict(kwargs)
            result_kwargs["key"] = _query_widget_key(query)
            result_kwargs["format_func"] = lambda value: _friendly_label(value, city_map.get(value, ""))
            result_kwargs["index"] = None

            if not query:
                result_kwargs["placeholder"] = "Search first to evaluate timezone"
                selected_timezone = base_selectbox(
                    "Practitioner scheduling timezone", [], *args, **result_kwargs
                )
                st.caption("Enter a city, country or timezone to view matching city-based options.")
            elif not matches:
                result_kwargs["placeholder"] = "No matching location found"
                selected_timezone = base_selectbox(
                    "Practitioner scheduling timezone", [], *args, **result_kwargs
                )
                st.caption("No match found. Practitioner scheduling timezone remains empty.")
            else:
                if len(matches) == 1:
                    result_kwargs["index"] = 0
                else:
                    result_kwargs["placeholder"] = "Select the correct city and timezone"
                selected_timezone = base_selectbox(
                    "Practitioner scheduling timezone", matches, *args, **result_kwargs
                )
                if len(matches) > 1 and not selected_timezone:
                    st.caption("Multiple city-based options found. Select the correct one.")

            ready = bool(selected_timezone)
            st.session_state[SELECTION_READY_KEY] = ready
            if ready:
                st.session_state[VISIBLE_TIMEZONE_KEY] = selected_timezone
            else:
                st.session_state.pop(VISIBLE_TIMEZONE_KEY, None)

            if pending_member:
                selected_member = base_selectbox(
                    "Select member controlling this page",
                    pending_member["options"],
                    *pending_member["args"],
                    **pending_member["kwargs"],
                )
                if selected_member != pending_member["selected"]:
                    st.rerun()

            current = schedule_timezone_ui.practitioner_timezone_name(
                st.session_state.get("user_id") or "admin",
                persist=True,
            )
            return selected_timezone or current

        return base_selectbox(label, options, *args, **kwargs)

    def patched_radio(label, options, *args, **kwargs):
        if label == "Enter the schedule in" and not st.session_state.get(SELECTION_READY_KEY, False):
            st.info("Search and select the practitioner timezone to continue.")
            st.stop()
        return base_radio(label, options, *args, **kwargs)

    st.selectbox = patched_selectbox
    schedule_timezone_ui.st.selectbox = patched_selectbox
    st.radio = patched_radio
    schedule_timezone_ui.st.radio = patched_radio

    st.markdown(
        """
<style id="hm-unified-practitioner-timezone-search">
.st-key-hm_tz_practitioner_timezone_search{margin-top:.48rem!important;margin-bottom:-.42rem!important;}
[class*="st-key-hm_tz_practitioner_timezone_result_"]{margin-top:0!important;margin-bottom:0!important;}
div[data-baseweb="popover"] [role="listbox"],div[data-baseweb="popover"] ul{scrollbar-width:auto!important;scrollbar-color:#B89345 #FFF7E6!important;}
div[data-baseweb="popover"] [role="listbox"]::-webkit-scrollbar,div[data-baseweb="popover"] ul::-webkit-scrollbar{width:12px!important;}
div[data-baseweb="popover"] [role="listbox"]::-webkit-scrollbar-thumb,div[data-baseweb="popover"] ul::-webkit-scrollbar-thumb{background:#B89345!important;border:2px solid #FFF7E6!important;border-radius:999px!important;}
</style>
""",
        unsafe_allow_html=True,
    )
