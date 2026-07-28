import re
import json
import pathlib
import streamlit as st
from components.guards import require_member
from components.ui_common import inject_global_styles, apply_luxe_theme, topbar, card_start, card_end, utility_logout_bar, render_build_text_v12, render_back_to_top
from components.db import get_profile_with_laf_fallback, update_profile, sync_profile_from_laf
from components.member_timezone import (
    CITY_OTHER_OPTION,
    CITY_PLACEHOLDER,
    DEFAULT_MEMBER_TIMEZONE,
    cities_for_country,
    member_timezone_name,
    persist_member_timezone_profile,
    resolve_member_timezone,
    timezones_for_country,
)

st.set_page_config(page_title="My Profile", page_icon="💚", layout="wide", initial_sidebar_state="collapsed")
inject_global_styles(); apply_luxe_theme(); require_member(); utility_logout_bar(); render_back_to_top()

user_id = st.session_state["user_id"]
sync_profile_from_laf(user_id)
member_timezone_name(user_id, persist=True)
p = get_profile_with_laf_fallback(user_id)

def load_country_options():
    config_path = pathlib.Path(__file__).resolve().parents[1] / "config" / "laf_questions.json"
    try:
        laf_questions = json.loads(config_path.read_text(encoding="utf-8"))
        country_question = next((q for q in laf_questions if q.get("code") == "country"), None)
        options = country_question.get("options", []) if country_question else []
        return options or ["India", "Other"]
    except Exception:
        return ["India", "Other"]

COUNTRY_OPTIONS = load_country_options()
GENDER_OPTIONS = ["Female", "Male", "Non-binary", "Prefer not to say", "Other"]

def int_value(v, default, min_v, max_v):
    try:
        if v in [None, "", "Select"]:
            return default
        value = int(float(v))
        return max(min_v, min(value, max_v))
    except Exception:
        return default

def validate_mobile(mobile, country):
    rules = {
        "India": (10, 10),
        "United States": (10, 10),
        "Canada": (10, 10),
        "United Kingdom": (10, 10),
        "Australia": (9, 9),
        "United Arab Emirates": (9, 9),
        "Singapore": (8, 8),
        "Other": (7, 15),
    }
    prefixes = {
        "India": "91",
        "United States": "1",
        "Canada": "1",
        "United Kingdom": "44",
        "Australia": "61",
        "United Arab Emirates": "971",
        "Singapore": "65",
    }
    digits = re.sub(r"\D", "", mobile or "")
    if not digits:
        return False, "Mobile Number is mandatory."
    min_digits, max_digits = rules.get(country, rules["Other"])
    local_digits = digits
    prefix = prefixes.get(country)
    if prefix and len(digits) > max_digits and digits.startswith(prefix):
        local_digits = digits[len(prefix):]
    if len(set(local_digits)) == 1:
        return False, "Mobile Number cannot be all same digits."
    if not (min_digits <= len(local_digits) <= max_digits):
        if min_digits == max_digits:
            return False, f"Mobile Number for {country} should have {min_digits} digits."
        return False, f"Mobile Number for {country} should have {min_digits}-{max_digits} digits."
    return True, ""

def _widget_slug(value):
    return re.sub(r"[^A-Za-z0-9]+", "_", str(value or "")).strip("_") or "default"

topbar(
    "My Profile",
    "Profile fields are automatically populated from overlapping LAF responses. You can still update them here if needed.",
    "Member profile"
)

st.markdown(
    """
    <div class='info-banner'>
      <b>Auto-filled from LAF.</b><br>
      Country is pulled from the LAF. Select your city and exact timezone so Daily Log and future schedules use your local calendar date rather than the server location.
    </div>
    """,
    unsafe_allow_html=True,
)

card_start()
if st.button("Refresh from LAF", use_container_width=True):
    sync_profile_from_laf(user_id)
    member_timezone_name(user_id, persist=True)
    st.success("Profile refreshed from LAF.")
    st.rerun()

data = {}

c1, c2 = st.columns(2)
with c1:
    data["full_name"] = st.text_input("Full Name", value=str(p.get("full_name", "")))
    data["email_id"] = st.text_input("Email ID", value=str(p.get("email_id", "")))
    gender_default = p.get("gender", "")
    data["gender"] = st.selectbox(
        "Gender",
        GENDER_OPTIONS,
        index=GENDER_OPTIONS.index(gender_default) if gender_default in GENDER_OPTIONS else 0,
    )
    country_default = p.get("country", "India") or "India"
    data["country"] = st.selectbox(
        "Country",
        COUNTRY_OPTIONS,
        index=COUNTRY_OPTIONS.index(country_default) if country_default in COUNTRY_OPTIONS else 0,
        key="hm_profile_country",
    )
    data["mobile_number"] = st.text_input(
        "Mobile Number",
        value=str(p.get("mobile_number", p.get("phone", ""))),
        placeholder="Example: 9876543210 or +91 9876543210",
    )

with c2:
    data["age"] = str(st.number_input("Age", min_value=1, max_value=120, value=int_value(p.get("age"), 25, 1, 120), step=1))
    data["height_cm"] = str(st.number_input("Height (cm)", min_value=50, max_value=250, value=int_value(p.get("height_cm"), 160, 50, 250), step=1))
    data["weight_kg"] = str(st.number_input("Weight (kg)", min_value=20, max_value=250, value=int_value(p.get("weight_kg"), 60, 20, 250), step=1))
    data["occupation"] = st.text_input("Occupation", value=str(p.get("occupation", "")))

    stored_city = str(p.get("timezone_city") or p.get("city") or "").strip()
    if stored_city == data["country"]:
        stored_city = ""
    city_options = cities_for_country(data["country"], stored_city)
    city_default = stored_city if stored_city in city_options else CITY_PLACEHOLDER
    city_key = f"hm_profile_city_{_widget_slug(data['country'])}"
    data["city"] = st.selectbox(
        "City",
        city_options,
        index=city_options.index(city_default),
        key=city_key,
        help="City options are based on the selected country. Choose Other / Not listed when required, then select the correct timezone below.",
    )

    timezone_options = timezones_for_country(data["country"])
    if not timezone_options:
        timezone_options = [DEFAULT_MEMBER_TIMEZONE]

    stored_timezone = str(p.get("timezone_name") or "")
    city_changed = bool(stored_city and data["city"] != stored_city)
    if city_changed or stored_timezone not in timezone_options:
        stored_timezone, _ = resolve_member_timezone(
            data["country"],
            data["city"],
            "" if city_changed else stored_timezone,
        )
    timezone_index = timezone_options.index(stored_timezone) if stored_timezone in timezone_options else 0
    timezone_key = f"hm_profile_timezone_{_widget_slug(data['country'])}_{_widget_slug(data['city'])}"
    data["timezone_name"] = st.selectbox(
        "Timezone",
        timezone_options,
        index=timezone_index,
        key=timezone_key,
        help="IANA timezone used for Daily Log dates and future cross-timezone scheduling.",
    )

# v100.15 profile action row: Save left, Back to Home right
save_col_v10015, back_col_v10015 = st.columns([1, 1], gap="medium")
with save_col_v10015:
    if st.button("Save Profile", type="primary", use_container_width=True):
        errors = []
        if not data["full_name"].strip():
            errors.append("Full Name is mandatory.")
        if "@" in data["full_name"]:
            errors.append("Full Name should not contain email address.")
        if not re.match(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$", data["email_id"].strip()):
            errors.append("Email ID should be valid.")
        ok, mobile_error = validate_mobile(data["mobile_number"], data["country"])
        if not ok:
            errors.append(mobile_error)
        if data["city"] == CITY_PLACEHOLDER:
            errors.append("City should be selected from the dropdown.")

        if errors:
            for err in errors:
                st.error(err)
        else:
            data["phone"] = data["mobile_number"]
            update_profile(user_id, data)
            persist_member_timezone_profile(
                user_id,
                data["country"],
                data["city"],
                data["timezone_name"],
            )
            st.success("Profile saved with your local timezone.")

with back_col_v10015:
    if st.button("Back to Home", use_container_width=True):
        st.switch_page("pages/02_Member_Home.py")
card_end()
