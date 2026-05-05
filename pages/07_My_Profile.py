import re
import streamlit as st
from components.guards import require_member
from components.ui_common import inject_global_styles, apply_luxe_theme, topbar, card_start, card_end, utility_logout_bar
from components.db import get_profile_with_laf_fallback, update_profile, sync_profile_from_laf

st.set_page_config(page_title="My Profile", page_icon="💚", layout="wide", initial_sidebar_state="collapsed")
inject_global_styles(); apply_luxe_theme(); require_member(); utility_logout_bar()

user_id = st.session_state["user_id"]
sync_profile_from_laf(user_id)
p = get_profile_with_laf_fallback(user_id)

COUNTRY_OPTIONS = [
    "India",
    "United States",
    "Canada",
    "United Kingdom",
    "Australia",
    "United Arab Emirates",
    "Singapore",
    "Other",
]
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

topbar(
    "My Profile",
    "Profile fields are automatically populated from overlapping LAF responses. You can still update them here if needed.",
    "Member profile"
)

st.markdown(
    """
    <div class='info-banner'>
      <b>Auto-filled from LAF.</b><br>
      Full name, email, gender, age, height, weight, country, mobile number and occupation are pulled from LAF wherever available.
    </div>
    """,
    unsafe_allow_html=True,
)

card_start()
if st.button("Refresh from LAF", use_container_width=True):
    sync_profile_from_laf(user_id)
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
    country_default = p.get("country", p.get("city", "India")) or "India"
    data["country"] = st.selectbox(
        "Country",
        COUNTRY_OPTIONS,
        index=COUNTRY_OPTIONS.index(country_default) if country_default in COUNTRY_OPTIONS else 0,
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

if st.button("Save Profile", type="primary"):
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

    if errors:
        for err in errors:
            st.error(err)
    else:
        # Backward-compatible aliases
        data["phone"] = data["mobile_number"]
        data["city"] = data["country"]
        update_profile(user_id, data)
        st.success("Profile saved.")

if st.button("Back to Home"):
    st.switch_page("pages/02_Member_Home.py")
card_end()