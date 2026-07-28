from __future__ import annotations

import hashlib
import re
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import pytz
import streamlit as st


_TIMEZONE_WIDGET_KEY = "hm_tz_practitioner_timezone"
_TIMEZONE_SEARCH_KEY = "hm_tz_practitioner_timezone_search"
_TIMEZONE_SELECTION_READY_KEY = "hm_tz_practitioner_timezone_selection_ready"
_SEARCH_BEHAVIOUR_VERSION_KEY = "hm_tz_practitioner_search_behaviour_version"
_SEARCH_BEHAVIOUR_VERSION = "broad-location-v1"

_COMMON_TIMEZONE_ORDER = [
    "Asia/Kolkata",
    "Europe/London",
    "Asia/Dubai",
    "Asia/Singapore",
    "America/New_York",
    "America/Toronto",
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
    "America/Edmonton": ("Calgary", "Edmonton"),
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

_COUNTRY_SEARCH_ALIASES = {
    "uk": "United Kingdom",
    "u k": "United Kingdom",
    "britain": "United Kingdom",
    "great britain": "United Kingdom",
    "uae": "United Arab Emirates",
    "u a e": "United Arab Emirates",
    "usa": "United States",
    "u s a": "United States",
    "us": "United States",
    "u s": "United States",
    "united states of america": "United States",
}


def _normalise(value: object) -> str:
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


def _candidate_cities(timezone_name: str) -> list[str]:
    candidates: list[str] = []
    for city in _CITY_ALIASES_BY_TIMEZONE.get(timezone_name, ()):
        if city and city not in candidates:
            candidates.append(city)
    iana_city = _iana_city_name(timezone_name)
    if iana_city and iana_city not in candidates:
        candidates.append(iana_city)
    return candidates


def _representative_city(timezone_name: str) -> str:
    candidates = _candidate_cities(timezone_name)
    return candidates[0] if candidates else _iana_city_name(timezone_name)


def _friendly_timezone_label(
    timezone_name: object,
    city_name: object = "",
) -> str:
    value = str(timezone_name or "").strip()
    if not value:
        return ""
    if value == "UTC":
        return "Coordinated Universal Time — UTC"

    location = str(city_name or "").strip() or _representative_city(value) or value
    country = _TIMEZONE_COUNTRIES.get(value, "")
    if country:
        return f"{location}, {country} — {value}"
    return f"{location} — {value}"


def _text_match_score(query: str, candidate: object) -> int | None:
    candidate_key = _normalise(candidate)
    if not query or not candidate_key:
        return None
    if query == candidate_key:
        return 0
    if candidate_key.startswith(query):
        return 1
    if query in candidate_key:
        return 2
    return None


def _country_search_terms(country_name: str) -> list[str]:
    terms = [country_name]
    normalised_country = _normalise(country_name)
    for alias, canonical_country in _COUNTRY_SEARCH_ALIASES.items():
        if _normalise(canonical_country) == normalised_country:
            terms.append(alias)
    return terms


def _safe_timezone_options(original_timezone_options) -> list[str]:
    options: list[str] = []
    for timezone_name in original_timezone_options():
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


def _supported_country_timezones(options: list[str]) -> dict[str, set[str]]:
    supported: dict[str, set[str]] = {}
    for timezone_name in options:
        if timezone_name not in _CITY_ALIASES_BY_TIMEZONE:
            continue
        country = _TIMEZONE_COUNTRIES.get(timezone_name, "")
        if country:
            supported.setdefault(country, set()).add(timezone_name)
    return supported


def _match_location_timezones(
    options: list[str],
) -> tuple[list[str], dict[str, str]]:
    """Accept city, country or IANA input and return city-based timezone choices."""
    query = _normalise(st.session_state.get(_TIMEZONE_SEARCH_KEY))
    if not query:
        return [], {}

    supported_by_country = _supported_country_timezones(options)
    ranked: list[tuple[int, str, str, str]] = []
    matched_city_by_timezone: dict[str, str] = {}

    for timezone_name in options:
        country = _TIMEZONE_COUNTRIES.get(timezone_name, "")
        best_city_match: tuple[int, str] | None = None
        for city in _candidate_cities(timezone_name):
            score = _text_match_score(query, city)
            if score is None:
                continue
            candidate = (score, city)
            if best_city_match is None or (
                candidate[0], candidate[1].lower()
            ) < (
                best_city_match[0], best_city_match[1].lower()
            ):
                best_city_match = candidate

        timezone_score = _text_match_score(query, timezone_name)
        country_scores = [
            score
            for term in _country_search_terms(country)
            if (score := _text_match_score(query, term)) is not None
        ]
        country_score = min(country_scores) if country_scores else None

        match_rank: int | None = None
        display_city = ""
        if best_city_match is not None:
            match_rank = best_city_match[0]
            display_city = best_city_match[1]
        elif timezone_score is not None:
            match_rank = 10 + timezone_score
            display_city = _representative_city(timezone_name)
        elif country_score is not None:
            preferred_timezones = supported_by_country.get(country, set())
            if preferred_timezones and timezone_name not in preferred_timezones:
                continue
            match_rank = 20 + country_score
            display_city = _representative_city(timezone_name)

        if match_rank is None:
            continue

        ranked.append(
            (
                match_rank,
                display_city.lower(),
                country.lower(),
                timezone_name,
            )
        )
        matched_city_by_timezone[timezone_name] = display_city

    ranked.sort(key=lambda item: item)
    ordered_timezones = [item[3] for item in ranked]
    return ordered_timezones, matched_city_by_timezone


def _query_widget_key(query: object) -> str:
    digest = hashlib.sha1(_normalise(query).encode("utf-8")).hexdigest()[:10]
    return f"hm_tz_practitioner_timezone_location_{digest}"


def _lock_timezone_dropdown_typing() -> None:
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


def _inject_timezone_selector_css() -> None:
    st.markdown(
        """
<style id="hm-friendly-timezone-selector-v5">
.st-key-hm_tz_practitioner_timezone_search{
  margin-top:.48rem!important;
  margin-bottom:-.42rem!important;
}
[class*="st-key-hm_tz_practitioner_timezone_location_"]{
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


def install_admin_scheduling_timezone_selector(schedule_timezone_ui) -> None:
    """Install broad location search while preserving the accepted scheduling engine."""
    original_timezone_options = getattr(
        schedule_timezone_ui,
        "_hm_base_timezone_options_before_sanitizer",
        schedule_timezone_ui.timezone_options,
    )
    schedule_timezone_ui._hm_base_timezone_options_before_sanitizer = (
        original_timezone_options
    )
    original_persist = getattr(
        schedule_timezone_ui,
        "_hm_base_persist_practitioner_timezone_before_sanitizer",
        schedule_timezone_ui.persist_practitioner_timezone,
    )
    schedule_timezone_ui._hm_base_persist_practitioner_timezone_before_sanitizer = (
        original_persist
    )

    def safe_timezone_options() -> list[str]:
        return _safe_timezone_options(original_timezone_options)

    def safe_persist_practitioner_timezone(
        user_id: object,
        timezone_name: object,
    ) -> str:
        candidate = str(timezone_name or "").strip()
        if candidate not in safe_timezone_options():
            st.session_state.pop(_TIMEZONE_WIDGET_KEY, None)
            return schedule_timezone_ui.practitioner_timezone_name(
                user_id,
                persist=True,
            )
        return original_persist(user_id, candidate)

    schedule_timezone_ui.timezone_options = safe_timezone_options
    schedule_timezone_ui.persist_practitioner_timezone = (
        safe_persist_practitioner_timezone
    )

    if st.session_state.get(_SEARCH_BEHAVIOUR_VERSION_KEY) != _SEARCH_BEHAVIOUR_VERSION:
        st.session_state[_SEARCH_BEHAVIOUR_VERSION_KEY] = _SEARCH_BEHAVIOUR_VERSION
        st.session_state.pop(_TIMEZONE_SEARCH_KEY, None)
        st.session_state.pop(_TIMEZONE_WIDGET_KEY, None)
        st.session_state[_TIMEZONE_SELECTION_READY_KEY] = False

    retained_timezone = st.session_state.get(_TIMEZONE_WIDGET_KEY)
    if retained_timezone is not None and str(retained_timezone) not in safe_timezone_options():
        st.session_state.pop(_TIMEZONE_WIDGET_KEY, None)

    base_markdown = getattr(
        st,
        "_hm_base_markdown_before_schedule_subtitle_removal",
        st.markdown,
    )
    st._hm_base_markdown_before_schedule_subtitle_removal = base_markdown
    removed_context_subtitle = (
        "<div class='hm-tz-context-sub'>All schedule creation, status, reschedule "
        "review and session usage below are for the selected member only.</div>"
    )
    practitioner_status_prefix = (
        "<div class='hm-schedule-muted'>Practitioner timezone:"
    )

    def schedule_markdown_with_blank_unselected_timezone(body, *args, **kwargs):
        rendered = str(body or "")
        if rendered == removed_context_subtitle:
            return None
        if (
            rendered.startswith(practitioner_status_prefix)
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
        return base_markdown(rendered, *args, **kwargs)

    st.markdown = schedule_markdown_with_blank_unselected_timezone
    schedule_timezone_ui.st.markdown = (
        schedule_markdown_with_blank_unselected_timezone
    )

    base_selectbox = getattr(
        st,
        "_hm_base_selectbox_before_schedule_control_order",
        st.selectbox,
    )
    st._hm_base_selectbox_before_schedule_control_order = base_selectbox
    base_radio = getattr(
        st,
        "_hm_base_radio_before_practitioner_timezone_required",
        st.radio,
    )
    st._hm_base_radio_before_practitioner_timezone_required = base_radio
    pending_member_selectbox: dict[str, object] = {}

    def selected_value_without_render(options: list, kwargs: dict):
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

    def selectbox_with_broad_practitioner_timezone(
        label,
        options,
        *args,
        **kwargs,
    ):
        if label == "Select member controlling this page":
            member_options = list(options)
            selected = selected_value_without_render(member_options, kwargs)
            pending_member_selectbox.clear()
            pending_member_selectbox.update(
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
            current_value = (
                retained
                if retained in all_options
                else all_options[original_index]
            )

            st.text_input(
                "Search practitioner timezone",
                key=_TIMEZONE_SEARCH_KEY,
                placeholder="Type a city, country or timezone",
                help=(
                    "HealthyMe accepts a city, country or IANA timezone, maps it "
                    "to city-based choices, and stores only the selected valid timezone."
                ),
            )
            query = str(st.session_state.get(_TIMEZONE_SEARCH_KEY) or "").strip()
            matching_timezones, matched_cities = _match_location_timezones(
                all_options
            )

            timezone_kwargs = dict(kwargs)
            timezone_kwargs["key"] = _query_widget_key(query)
            timezone_kwargs["format_func"] = lambda timezone_name: (
                _friendly_timezone_label(
                    timezone_name,
                    matched_cities.get(timezone_name, ""),
                )
            )

            selected_timezone = None
            if not query:
                timezone_kwargs["index"] = None
                timezone_kwargs["placeholder"] = (
                    "Search by city, country or timezone first"
                )
                selected_timezone = base_selectbox(
                    "Practitioner scheduling timezone",
                    [],
                    *args,
                    **timezone_kwargs,
                )
                _render_timezone_search_status(
                    "Enter a city, country or timezone to view city-based choices."
                )
            elif not matching_timezones:
                timezone_kwargs["index"] = None
                timezone_kwargs["placeholder"] = "No matching location found"
                selected_timezone = base_selectbox(
                    "Practitioner scheduling timezone",
                    [],
                    *args,
                    **timezone_kwargs,
                )
                _render_timezone_search_status(
                    "No matching city, country or timezone found. Practitioner scheduling timezone remains empty."
                )
            else:
                timezone_kwargs["index"] = (
                    0 if len(matching_timezones) == 1 else None
                )
                timezone_kwargs["placeholder"] = (
                    "Select a city-based timezone"
                    if len(matching_timezones) > 1
                    else None
                )
                selected_timezone = base_selectbox(
                    "Practitioner scheduling timezone",
                    matching_timezones,
                    *args,
                    **timezone_kwargs,
                )
                if len(matching_timezones) > 1 and not selected_timezone:
                    _render_timezone_search_status(
                        "Multiple matching locations were found. Select the correct city-based timezone."
                    )

            selection_ready = bool(selected_timezone)
            st.session_state[_TIMEZONE_SELECTION_READY_KEY] = selection_ready
            if selection_ready:
                st.session_state[_TIMEZONE_WIDGET_KEY] = selected_timezone
            else:
                st.session_state.pop(_TIMEZONE_WIDGET_KEY, None)

            _lock_timezone_dropdown_typing()

            if pending_member_selectbox:
                selected_member = base_selectbox(
                    "Select member controlling this page",
                    pending_member_selectbox["options"],
                    *pending_member_selectbox["args"],
                    **pending_member_selectbox["kwargs"],
                )
                if selected_member != pending_member_selectbox["selected"]:
                    st.rerun()

            # Keep the underlying accepted component render-safe. The visible field
            # remains blank and scheduling is blocked until selection_ready is true.
            return selected_timezone or current_value

        return base_selectbox(label, options, *args, **kwargs)

    def radio_require_selected_timezone(label, options, *args, **kwargs):
        if (
            label == "Enter the schedule in"
            and not st.session_state.get(_TIMEZONE_SELECTION_READY_KEY, False)
        ):
            st.info(
                "Search by city, country or timezone and confirm a city-based timezone to continue."
            )
            st.stop()
        return base_radio(label, options, *args, **kwargs)

    st.selectbox = selectbox_with_broad_practitioner_timezone
    schedule_timezone_ui.st.selectbox = selectbox_with_broad_practitioner_timezone
    st.radio = radio_require_selected_timezone
    schedule_timezone_ui.st.radio = radio_require_selected_timezone

    _inject_timezone_selector_css()
