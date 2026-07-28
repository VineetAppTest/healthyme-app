from __future__ import annotations

from datetime import date, datetime
import re
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import pytz

from components.db import load_db, save_db


DEFAULT_MEMBER_TIMEZONE = "Asia/Kolkata"

# Common aliases used by the LAF country list and historical HealthyMe records.
_COUNTRY_CODE_ALIASES = {
    "uae": "AE",
    "united arab emirates": "AE",
    "usa": "US",
    "united states": "US",
    "united states of america": "US",
    "uk": "GB",
    "united kingdom": "GB",
    "south korea": "KR",
    "north korea": "KP",
    "russia": "RU",
    "vietnam": "VN",
    "viet nam": "VN",
    "bolivia": "BO",
    "tanzania": "TZ",
    "iran": "IR",
    "laos": "LA",
    "moldova": "MD",
    "brunei": "BN",
    "venezuela": "VE",
}

# Safe defaults for multi-timezone countries when an older LAF record has no
# city/timezone value yet. These are only fallbacks; an existing stored IANA
# timezone or a recognised LAF city always wins.
_COUNTRY_DEFAULT_TIMEZONES = {
    "US": "America/New_York",
    "CA": "America/Toronto",
    "AU": "Australia/Sydney",
    "BR": "America/Sao_Paulo",
    "MX": "America/Mexico_City",
    "RU": "Europe/Moscow",
    "ID": "Asia/Jakarta",
    "KZ": "Asia/Almaty",
    "CL": "America/Santiago",
    "EC": "America/Guayaquil",
    "NZ": "Pacific/Auckland",
    "PT": "Europe/Lisbon",
    "ES": "Europe/Madrid",
}

# City resolution is intentionally local and deterministic. It never uses IP,
# VPN location, browser location or an external geocoding service.
_CITY_TIMEZONE_OVERRIDES = {
    ("US", "new york"): "America/New_York",
    ("US", "washington"): "America/New_York",
    ("US", "boston"): "America/New_York",
    ("US", "miami"): "America/New_York",
    ("US", "chicago"): "America/Chicago",
    ("US", "dallas"): "America/Chicago",
    ("US", "houston"): "America/Chicago",
    ("US", "denver"): "America/Denver",
    ("US", "phoenix"): "America/Phoenix",
    ("US", "los angeles"): "America/Los_Angeles",
    ("US", "san francisco"): "America/Los_Angeles",
    ("US", "seattle"): "America/Los_Angeles",
    ("US", "honolulu"): "Pacific/Honolulu",
    ("US", "anchorage"): "America/Anchorage",
    ("CA", "toronto"): "America/Toronto",
    ("CA", "ottawa"): "America/Toronto",
    ("CA", "montreal"): "America/Toronto",
    ("CA", "winnipeg"): "America/Winnipeg",
    ("CA", "calgary"): "America/Edmonton",
    ("CA", "edmonton"): "America/Edmonton",
    ("CA", "vancouver"): "America/Vancouver",
    ("CA", "halifax"): "America/Halifax",
    ("AU", "sydney"): "Australia/Sydney",
    ("AU", "melbourne"): "Australia/Melbourne",
    ("AU", "brisbane"): "Australia/Brisbane",
    ("AU", "adelaide"): "Australia/Adelaide",
    ("AU", "darwin"): "Australia/Darwin",
    ("AU", "perth"): "Australia/Perth",
    ("BR", "sao paulo"): "America/Sao_Paulo",
    ("BR", "rio de janeiro"): "America/Sao_Paulo",
    ("BR", "brasilia"): "America/Sao_Paulo",
    ("BR", "manaus"): "America/Manaus",
    ("MX", "mexico city"): "America/Mexico_City",
    ("MX", "cancun"): "America/Cancun",
    ("MX", "tijuana"): "America/Tijuana",
    ("RU", "moscow"): "Europe/Moscow",
    ("RU", "saint petersburg"): "Europe/Moscow",
    ("RU", "novosibirsk"): "Asia/Novosibirsk",
    ("RU", "vladivostok"): "Asia/Vladivostok",
    ("ID", "jakarta"): "Asia/Jakarta",
    ("ID", "bali"): "Asia/Makassar",
    ("ID", "denpasar"): "Asia/Makassar",
    ("KZ", "almaty"): "Asia/Almaty",
    ("KZ", "astana"): "Asia/Almaty",
}


def _normalise(value: object) -> str:
    text = str(value or "").strip().lower()
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return " ".join(text.split())


def _valid_timezone_name(timezone_name: object) -> str:
    candidate = str(timezone_name or "").strip()
    if not candidate:
        return ""
    try:
        ZoneInfo(candidate)
        return candidate
    except (ZoneInfoNotFoundError, ValueError):
        return ""


def _country_code(country: object) -> str:
    normalised = _normalise(country)
    if not normalised:
        return ""
    if normalised in _COUNTRY_CODE_ALIASES:
        return _COUNTRY_CODE_ALIASES[normalised]

    for code, display_name in pytz.country_names.items():
        if _normalise(display_name) == normalised:
            return str(code).upper()
    return ""


def timezones_for_country(country: object) -> list[str]:
    """Return valid IANA timezones for the LAF country value."""
    code = _country_code(country)
    if not code:
        return []
    return [str(value) for value in pytz.country_timezones.get(code, [])]


def resolve_member_timezone(
    country: object,
    city: object = "",
    timezone_name: object = "",
) -> tuple[str, str]:
    """Resolve an IANA timezone without using server or network location.

    Priority:
    1. Existing valid timezone stored for the member.
    2. Recognised LAF country + city.
    3. The country's only timezone.
    4. A deterministic country default for multi-timezone countries.
    5. HealthyMe deployment fallback: Asia/Kolkata.
    """
    country_code = _country_code(country)
    country_timezones = timezones_for_country(country)

    explicit = _valid_timezone_name(timezone_name)
    if explicit and (not country_timezones or explicit in country_timezones):
        return explicit, "stored"

    city_key = _normalise(city)
    city_timezone = _CITY_TIMEZONE_OVERRIDES.get((country_code, city_key), "")
    if city_timezone and (
        not country_timezones or city_timezone in country_timezones
    ):
        return city_timezone, "laf_country_city"

    if len(country_timezones) == 1:
        return country_timezones[0], "laf_country"

    country_default = _COUNTRY_DEFAULT_TIMEZONES.get(country_code, "")
    if country_default and (
        not country_timezones or country_default in country_timezones
    ):
        return country_default, "laf_country_default"

    return DEFAULT_MEMBER_TIMEZONE, "healthyme_fallback"


def member_timezone_name(user_id: object, persist: bool = True) -> str:
    """Resolve and optionally persist the member's profile timezone."""
    user_key = str(user_id or "").strip()
    if not user_key:
        return DEFAULT_MEMBER_TIMEZONE

    db = load_db()
    laf = db.setdefault("laf_responses", {}).get(user_key, {}) or {}
    profile = db.setdefault("profiles", {}).setdefault(user_key, {})

    country = laf.get("country") or profile.get("country") or ""
    city = (
        laf.get("city")
        or laf.get("client_city")
        or profile.get("city")
        or profile.get("client_city")
        or ""
    )
    stored_timezone = (
        profile.get("timezone_name")
        or laf.get("timezone_name")
        or ""
    )

    resolved, source = resolve_member_timezone(
        country=country,
        city=city,
        timezone_name=stored_timezone,
    )

    if persist:
        changed = False
        updates = {
            "timezone_name": resolved,
            "timezone_source": source,
            "timezone_country": str(country or "").strip(),
            "timezone_city": str(city or "").strip(),
        }
        for key, value in updates.items():
            if profile.get(key) != value:
                profile[key] = value
                changed = True
        if changed:
            db["profiles"][user_key] = profile
            save_db(db)

    return resolved


def member_local_today(user_id: object) -> date:
    """Return today's date in the member's resolved IANA timezone."""
    timezone_name = member_timezone_name(user_id, persist=True)
    try:
        return datetime.now(ZoneInfo(timezone_name)).date()
    except (ZoneInfoNotFoundError, ValueError):
        return datetime.now(ZoneInfo(DEFAULT_MEMBER_TIMEZONE)).date()
