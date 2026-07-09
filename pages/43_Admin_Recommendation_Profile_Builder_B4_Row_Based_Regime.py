import datetime as dt
import re

import streamlit as st

from components.guards import require_admin
from components.ui_common import (
    apply_luxe_theme,
    inject_global_styles,
    render_back_to_top,
    render_page_nav,
    utility_logout_bar,
)

APP_BUILD_VERSION = "v100.29"
APP_BUILD_LABEL = "Profile Builder B4 Row-Based Regime Variation"

EXERCISE_TIME_OF_DAY = ["Morning", "Afternoon", "Evening", "Night / As advised"]
EXERCISE_INTENSITY = ["-- Select intensity --", "Low", "Moderate", "High", "As tolerated"]

SUPPLEMENT_FREQUENCY = [
    "-- Select frequency --",
    "Once daily",
    "Twice daily",
    "Thrice daily",
    "Alternate days",
    "Weekly",
    "As advised",
    "Custom",
]
SUPPLEMENT_TIMELINE = [
    "Before Breakfast",
    "After Breakfast",
    "Before Lunch",
    "After Lunch",
    "Before Dinner",
    "After Dinner",
    "Before Bed",
]

SECTIONS = ["Profile Setup", "Exercise Regime", "Supplement Regime", "Preview & Flow"]


def safe_key(value: object) -> str:
    return re.sub(r"[^A-Za-z0-9]+", "_", str(value or "")).strip("_") or "blank"


def init_state() -> None:
    st.session_state.setdefault("b4_active_section", "Profile Setup")
    st.session_state.setdefault("b4_start_date", dt.date.today())
    st.session_state.setdefault("b4_profile_name", "")
    st.session_state.setdefault("b4_exercise_rows", {day: 1 for day in range(1, 8)})
    st.session_state.setdefault("b4_supplement_rows", {day: 1 for day in range(1, 8)})
    st.session_state.setdefault("b4_day", 1)


def set_section(section: str) -> None:
    st.session_state["b4_active_section"] = section


def set_day(day: int) -> None:
    st.session_state["b4_day"] = day


def day_label(day: int) -> str:
    start = st.session_state.get("b4_start_date", dt.date.today())
    return f"Day {day} - {(start + dt.timedelta(days=day - 1)).strftime('%a, %d %b')}"


def day_picker() -> int:
    for row in ([1, 2, 3, 4], [5, 6, 7]):
        cols = st.columns(len(row), gap="small")
        for col, day in zip(cols, row):
            with col:
                st.button(
                    day_label(day),
                    key=f"b4_day_{day}",
                    type=("primary" if st.session_state["b4_day"] == day else "secondary"),
                    use_container_width=True,
                    on_click=set_day,
                    args=(day,),
                )
    return st.session_state["b4_day"]


def frequency_expected_count(frequency: str) -> int | None:
    if frequency == "Once daily":
        return 1
    if frequency == "Twice daily":
        return 2
    if frequency == "Thrice daily":
        return 3
    return None


def add_exercise_row(day: int) -> None:
    st.session_state["b4_exercise_rows"][day] = st.session_state["b4_exercise_rows"].get(day, 1) + 1


def add_supplement_row(day: int) -> None:
    st.session_state["b4_supplement_rows"][day] = st.session_state["b4_supplement_rows"].get(day, 1) + 1


def exercise_row(day: int, index: int) -> dict:
    prefix = f"b4_ex_{day}_{index}"
    cols = st.columns([0.22, 0.30, 0.18, 0.30], gap="medium")
    tod = cols[0].selectbox("Time of Day", EXERCISE_TIME_OF_DAY, key=f"{prefix}_tod")
    exercise = cols[1].text_input("Exercise", key=f"{prefix}_exercise")
    intensity = cols[2].selectbox("Intensity", EXERCISE_INTENSITY, key=f"{prefix}_intensity")
    instruction = cols[3].text_input("Instruction", key=f"{prefix}_instruction")
    return {
        "Type": "Exercise",
        "Day": day,
        "Time/Timeline": tod,
        "Item": exercise,
        "Frequency": "NA",
        "Dosage": "NA",
        "Intensity": intensity if not intensity.startswith("-- Select") else "NA",
        "Instruction": instruction,
    }


def supplement_row(day: int, index: int) -> dict:
    prefix = f"b4_supp_{day}_{index}"
    cols = st.columns([0.18, 0.24, 0.22, 0.16, 0.20], gap="medium")
    frequency = cols[0].selectbox("Frequency", SUPPLEMENT_FREQUENCY, key=f"{prefix}_frequency")
    timeline = cols[1].multiselect("Timeline", SUPPLEMENT_TIMELINE, key=f"{prefix}_timeline")
    supplement = cols[2].text_input("Supplement", key=f"{prefix}_supplement")
    dosage = cols[3].text_input("Dosage", key=f"{prefix}_dosage")
    instruction = cols[4].text_input("Instruction", key=f"{prefix}_instruction")

    expected = frequency_expected_count(frequency)
    if expected is not None and timeline and len(timeline) != expected:
        st.caption(f"{frequency} should normally have {expected} timeline selection(s).")

    return {
        "Type": "Supplement",
        "Day": day,
        "Time/Timeline": ", ".join(timeline) if timeline else "NA",
        "Item": supplement,
        "Frequency": frequency if not frequency.startswith("-- Select") else "NA",
        "Dosage": dosage,
        "Intensity": "NA",
        "Instruction": instruction,
    }


def collect_preview_rows() -> list[dict]:
    rows = []
    for day in range(1, 8):
        for index in range(st.session_state["b4_exercise_rows"].get(day, 1)):
            row = {
                "Type": "Exercise",
                "Day": day,
                "Time/Timeline": st.session_state.get(f"b4_ex_{day}_{index}_tod", ""),
                "Item": st.session_state.get(f"b4_ex_{day}_{index}_exercise", ""),
                "Frequency": "NA",
                "Dosage": "NA",
                "Intensity": st.session_state.get(f"b4_ex_{day}_{index}_intensity", ""),
                "Instruction": st.session_state.get(f"b4_ex_{day}_{index}_instruction", ""),
            }
            if any(str(row.get(field, "")).strip() for field in ("Item", "Instruction")):
                rows.append(row)
        for index in range(st.session_state["b4_supplement_rows"].get(day, 1)):
            timeline = st.session_state.get(f"b4_supp_{day}_{index}_timeline", [])
            row = {
                "Type": "Supplement",
                "Day": day,
                "Time/Timeline": ", ".join(timeline) if timeline else "",
                "Item": st.session_state.get(f"b4_supp_{day}_{index}_supplement", ""),
                "Frequency": st.session_state.get(f"b4_supp_{day}_{index}_frequency", ""),
                "Dosage": st.session_state.get(f"b4_supp_{day}_{index}_dosage", ""),
                "Intensity": "NA",
                "Instruction": st.session_state.get(f"b4_supp_{day}_{index}_instruction", ""),
            }
            if any(str(row.get(field, "")).strip() for field in ("Item", "Dosage", "Instruction")):
                rows.append(row)
    return rows


st.set_page_config(
    page_title="Recommendation Profile Builder B4",
    page_icon="💚",
    layout="wide",
    initial_sidebar_state="collapsed",
)
inject_global_styles()
apply_luxe_theme()
require_admin()
utility_logout_bar()
init_state()

st.markdown(
    f"""
    <div class='hero-shell'>
      <div class='hm-pb-brand-row'>
        <span class='hm-pb-brand'>HealthyMe</span>
        <span class='hm-pb-version'>{APP_BUILD_VERSION} · {APP_BUILD_LABEL}</span>
      </div>
      <div class='hero-kicker'>Admin recommendations · B4 variation</div>
      <div class='hero-title'>Recommendation Profile Builder B4</div>
      <div class='hero-subtitle'>Separate row-based variation for Exercise and Supplement Regime. This does not replace the current V2 page.</div>
      <div><span class='meta-pill'>Variation for decision</span></div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
<style>
.hm-pb-brand-row{display:flex;align-items:baseline;gap:.55rem;flex-wrap:wrap;margin-bottom:.35rem;}
.hm-pb-brand{color:#064E3B;font-size:.82rem;font-weight:950;letter-spacing:.02em;text-transform:uppercase;}
.hm-pb-version{color:#72551A;font-size:.72rem;font-weight:900;background:#F5E7C8;border-radius:999px;padding:.22rem .55rem;}
.hm-title{color:#064E3B;font-size:1.04rem;font-weight:950;margin:0 0 .25rem}.hm-sub{color:#64748B;font-size:.82rem;font-weight:720;margin:0 0 .7rem}
.hm-section-nav{margin:.35rem 0 .55rem 0;}.hm-section-rule{height:1px;background:linear-gradient(90deg,transparent,rgba(216,168,78,.8),transparent);margin:.3rem 0 .72rem 0;}
.hm-section-nav [data-testid="stButton"]>button{min-height:2.7rem!important;border-radius:15px!important;font-weight:930!important;border:1.15px solid rgba(216,180,98,.72)!important;background:#fff!important;color:#064E3B!important;box-shadow:0 4px 10px rgba(15,23,42,.035)!important;white-space:normal!important;line-height:1.15!important;padding:.55rem .5rem!important;}
.hm-section-nav [data-testid="stButton"]>button[kind="primary"]{background:linear-gradient(135deg,#FFF3D6,#FFFFFF)!important;border:1.5px solid #B89345!important;color:#064E3B!important;box-shadow:0 8px 18px rgba(15,23,42,.08)!important;}
.hm-preview{border:1px dashed #D8A84E;background:#FFF9EC;border-radius:16px;padding:.75rem .85rem;margin:.35rem 0;color:#475569;font-size:.83rem;font-weight:740;line-height:1.45}
.hm-store-box{border:1px solid #E3C98E;background:#FFFDF8;border-radius:16px;padding:.85rem .9rem;margin:.35rem 0 1rem;box-shadow:0 6px 14px rgba(15,23,42,.035)}
</style>
""",
    unsafe_allow_html=True,
)

st.markdown("<div class='hm-section-nav'>", unsafe_allow_html=True)
nav_cols = st.columns(len(SECTIONS), gap="small")
for col, section in zip(nav_cols, SECTIONS):
    with col:
        st.button(
            section,
            key=f"b4_nav_{safe_key(section)}",
            type=("primary" if st.session_state["b4_active_section"] == section else "secondary"),
            use_container_width=True,
            on_click=set_section,
            args=(section,),
        )
st.markdown("</div><div class='hm-section-rule'></div>", unsafe_allow_html=True)

section = st.session_state["b4_active_section"]

if section == "Profile Setup":
    st.markdown("<div class='hm-title'>Profile Setup · B4 Variation</div>", unsafe_allow_html=True)
    st.markdown("<div class='hm-store-box'>", unsafe_allow_html=True)
    c1, c2 = st.columns(2, gap="large")
    with c1:
        st.text_input("Profile Name", key="b4_profile_name")
        st.date_input("Plan Start Date", key="b4_start_date")
    with c2:
        st.text_input("Implementation Status", value="B4 variation only. Current V2 is untouched.", disabled=True)
        st.text_input("Backend Status", value="Visual/UI variation. No publish or member-facing change.", disabled=True)
    st.markdown("</div>", unsafe_allow_html=True)
    st.info("Use this page to compare the row-based Exercise/Supplement structure before deciding which version to keep.")

elif section == "Exercise Regime":
    day = day_picker()
    st.markdown("<div class='hm-title'>Exercise Regime · Row-based variation</div><div class='hm-sub'>Fields: Time of Day | Exercise | Intensity | Instruction</div>", unsafe_allow_html=True)
    for idx in range(st.session_state["b4_exercise_rows"].get(day, 1)):
        exercise_row(day, idx)
    st.button("Add workout item", key=f"b4_add_ex_{day}", use_container_width=True, on_click=add_exercise_row, args=(day,))

elif section == "Supplement Regime":
    day = day_picker()
    st.markdown("<div class='hm-title'>Supplement Regime · Row-based variation</div><div class='hm-sub'>Fields: Frequency | Timeline | Supplement | Dosage | Instruction. Frequency guides the number of timelines.</div>", unsafe_allow_html=True)
    for idx in range(st.session_state["b4_supplement_rows"].get(day, 1)):
        supplement_row(day, idx)
    st.button("Add supplement item", key=f"b4_add_supp_{day}", use_container_width=True, on_click=add_supplement_row, args=(day,))

else:
    rows = collect_preview_rows()
    st.markdown("<div class='hm-title'>Preview & Flow · B4 Variation</div>", unsafe_allow_html=True)
    st.markdown("<div class='hm-preview'><b>Decision note:</b> This page is intentionally separate from the current Profile Builder. Once reviewed, we can decide whether B4 should replace the current version.</div>", unsafe_allow_html=True)
    if rows:
        st.dataframe(rows, use_container_width=True, hide_index=True)
    else:
        st.info("No Exercise or Supplement rows have been added yet.")

render_page_nav(
    "Recommendation Profile Builder B4",
    back_page="pages/10_Admin_Dashboard.py",
    dashboard_page="pages/10_Admin_Dashboard.py",
    show_evaluation=False,
    show_dashboard=True,
    location="bottom",
)
render_back_to_top()
