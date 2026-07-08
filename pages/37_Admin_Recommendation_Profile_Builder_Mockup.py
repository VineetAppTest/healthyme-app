import datetime as dt

import streamlit as st

from components.guards import require_admin
from components.db import list_active_member_supplements, list_members
from components.recommendation_contract import list_repository_items
from components.ui_common import (
    inject_global_styles,
    apply_luxe_theme,
    utility_logout_bar,
    topbar,
    render_page_nav,
    render_back_to_top,
)


st.set_page_config(
    page_title="Recommendation Profile Builder Mock-up",
    page_icon="💚",
    layout="wide",
    initial_sidebar_state="collapsed",
)
inject_global_styles()
apply_luxe_theme()
require_admin()
utility_logout_bar()

topbar(
    "Recommendation Profile Builder Mock-up",
    "H9A.5E.1 visual structure only: profile library, 7-day meal structure, exercise regime, supplement regime and member-facing preview.",
    "Admin recommendations",
)

st.markdown(
    """
<style>
.hm-mock-note{border:1px solid #E3C98E;background:#FFFDF8;border-radius:16px;padding:.72rem .9rem;color:#475569;font-size:.84rem;font-weight:760;line-height:1.38;margin:.3rem 0 .8rem;}
.hm-mock-alert{border:1px solid #F4C56F;background:#FFFBEB;border-radius:16px;padding:.72rem .9rem;color:#7C4A03;font-size:.84rem;font-weight:840;line-height:1.38;margin:.3rem 0 .8rem;}
.hm-mock-section{border:1px solid #E3C98E;background:#FFFDF8;border-radius:18px;padding:.9rem .95rem;margin:.7rem 0 1rem;box-shadow:0 8px 18px rgba(15,23,42,.04);}
.hm-mock-title{color:#064E3B;font-size:1.02rem;font-weight:950;margin:0 0 .2rem;}
.hm-mock-sub{color:#64748B;font-size:.81rem;font-weight:720;line-height:1.35;margin:0 0 .65rem;}
.hm-flow{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:.55rem;margin:.45rem 0 .75rem;}
.hm-flow-card{border:1px solid #E3C98E;background:#FFFFFF;border-radius:14px;padding:.62rem .65rem;min-height:4.2rem;}
.hm-flow-num{display:inline-flex;align-items:center;justify-content:center;width:1.35rem;height:1.35rem;border-radius:999px;background:#064E3B;color:white;font-weight:950;font-size:.75rem;margin-bottom:.28rem;}
.hm-flow-title{color:#064E3B;font-size:.78rem;font-weight:950;line-height:1.15;}
.hm-flow-sub{color:#64748B;font-size:.70rem;font-weight:720;line-height:1.25;margin-top:.12rem;}
.hm-mini-grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:.55rem;margin:.4rem 0 .7rem;}
.hm-mini{border:1px solid #E3C98E;background:#fff;border-radius:14px;padding:.55rem .65rem;}
.hm-mini-label{font-size:.68rem;text-transform:uppercase;letter-spacing:.04em;color:#64748B;font-weight:900;}
.hm-mini-value{font-size:1.05rem;color:#064E3B;font-weight:950;line-height:1.05;margin-top:.12rem;}
.hm-slot-caption{font-size:.78rem;color:#72551A;font-weight:870;margin:.55rem 0 .25rem;}
.hm-preview-box{border:1px dashed #D8A84E;background:#FFF9EC;border-radius:16px;padding:.7rem .8rem;margin:.35rem 0;color:#475569;font-size:.82rem;font-weight:740;line-height:1.38;}
@media(max-width:900px){.hm-flow{grid-template-columns:repeat(2,minmax(0,1fr));}.hm-mini-grid{grid-template-columns:repeat(2,minmax(0,1fr));}}
</style>
""",
    unsafe_allow_html=True,
)

MEAL_SLOTS = [
    "Wake-up / Early Morning",
    "Breakfast",
    "Mid-morning Snack",
    "Lunch",
    "Evening Snack / Tea",
    "Dinner",
    "Bedtime",
]
EXERCISE_SLOTS = ["Morning", "Evening", "Preferred Time"]
SUPPLEMENT_SLOTS = ["Morning", "Afternoon", "Evening", "Before Bed", "Preferred Time"]
INTENSITY_OPTIONS = ["Low", "Moderate", "High", "As tolerated"]
FREQUENCY_OPTIONS = ["Once", "Twice", "Thrice", "Custom"]


def _clean(value):
    text = str(value or "").strip()
    if text.lower() in {"nan", "none", "null", "na", "n/a", "select"}:
        return ""
    return text


def _member_label(row):
    return f"{row.get('name') or 'Member'} — {row.get('email') or row.get('id')}"


def _resource_label(row, fallback):
    title = _clean(row.get("title")) or fallback
    meta = _clean(row.get("meal_type")) or _clean(row.get("duration_or_reps")) or _clean(row.get("category"))
    return f"{row.get('id')} — {title}{' · ' + meta if meta else ''}"


def _day_label(start_date, day_number):
    day = start_date + dt.timedelta(days=day_number - 1)
    return f"Day {day_number} · {day.strftime('%a, %d %b %Y')}"


def _render_flow():
    st.markdown(
        """
<div class='hm-flow'>
  <div class='hm-flow-card'><div class='hm-flow-num'>1</div><div class='hm-flow-title'>Base Units</div><div class='hm-flow-sub'>Recipe, exercise and supplement repositories.</div></div>
  <div class='hm-flow-card'><div class='hm-flow-num'>2</div><div class='hm-flow-title'>Weekly Structures</div><div class='hm-flow-sub'>Meal structure, exercise regime and supplement regime.</div></div>
  <div class='hm-flow-card'><div class='hm-flow-num'>3</div><div class='hm-flow-title'>Recommendation Profile</div><div class='hm-flow-sub'>Reusable template with region, age, concerns and goals.</div></div>
  <div class='hm-flow-card'><div class='hm-flow-num'>4</div><div class='hm-flow-title'>Assign / Clone</div><div class='hm-flow-sub'>Clone profile, adjust, assign to member and set start date.</div></div>
  <div class='hm-flow-card'><div class='hm-flow-num'>5</div><div class='hm-flow-title'>Member View</div><div class='hm-flow-sub'>My Recommendations = full week; Today’s Journey = today’s slice.</div></div>
</div>
""",
        unsafe_allow_html=True,
    )


st.markdown(
    """
<div class='hm-mock-alert'>
<b>Mock-up only.</b> This page does not publish or overwrite member recommendation data. It is for structure review before implementation.
</div>
""",
    unsafe_allow_html=True,
)

_render_flow()

members = list_members()
member_options = {_member_label(m): m for m in members} if members else {}
recipe_rows = list_repository_items("recipes", active_only=True)
exercise_rows = list_repository_items("exercises", active_only=True)
recipe_options = ["— Select recipe —"] + [_resource_label(r, "Recipe") for r in recipe_rows]
exercise_options = ["— Select exercise —"] + [_resource_label(r, "Exercise") for r in exercise_rows]

profile_tab, meal_tab, exercise_tab, supplement_tab, preview_tab = st.tabs([
    "1. Profile Setup",
    "2. Meal Structure",
    "3. Exercise Regime",
    "4. Supplement Regime",
    "5. Preview & End-to-End Flow",
])

with profile_tab:
    st.markdown("<div class='hm-mock-section'>", unsafe_allow_html=True)
    st.markdown("<div class='hm-mock-title'>Recommendation Profile Setup</div>", unsafe_allow_html=True)
    st.markdown("<div class='hm-mock-sub'>Profiles are reusable templates. A nutritionist can clone Profile A, change it, and save it as Profile B.</div>", unsafe_allow_html=True)
    c1, c2 = st.columns(2, gap="large")
    with c1:
        profile_name = st.text_input("Profile Name", value="North India · Adult · Weight Management · Vegetarian", key="mock_profile_name")
        clone_from = st.selectbox("Clone From Existing Profile", ["— New profile —", "Profile A · Gut Reset", "Profile B · Weight Management", "Profile C · Senior Wellness"], key="mock_clone_from")
        clone_note = st.text_input("Change Note", value="Cloned and adjusted for member preference / region / health concern", key="mock_clone_note")
        status = st.selectbox("Profile Status", ["Draft", "Active", "Archived"], key="mock_profile_status")
    with c2:
        region = st.text_input("Region / Food Culture", value="North India", key="mock_region")
        age_band = st.selectbox("Age Band", ["Teen", "18-30", "31-45", "46-60", "60+"], index=2, key="mock_age_band")
        health_concern = st.multiselect("Health Concerns", ["Weight Management", "Gut Health", "Diabetes Support", "Energy", "Inflammation", "Sleep", "General Wellness"], default=["Weight Management"], key="mock_health")
        diet_type = st.selectbox("Diet Type", ["Vegetarian", "Non-vegetarian", "Vegan", "Eggetarian", "Jain", "Custom"], key="mock_diet")
    assign_col, cycle_col = st.columns(2, gap="large")
    with assign_col:
        if member_options:
            selected_member = st.selectbox("Example Member Assignment", list(member_options.keys()), key="mock_member_select")
        else:
            selected_member = "No member available"
            st.info("No active members found for assignment preview.")
    with cycle_col:
        start_date = st.date_input("Plan Start Date", value=dt.date.today(), key="mock_start_date")
        st.text_input("Cycle Rule", value="Weekly cyclical until replaced or stopped", disabled=True)
    st.markdown("</div>", unsafe_allow_html=True)

with meal_tab:
    st.markdown("<div class='hm-mock-section'>", unsafe_allow_html=True)
    st.markdown("<div class='hm-mock-title'>Meal Structure · Day 1 to Day 7</div>", unsafe_allow_html=True)
    st.markdown("<div class='hm-mock-sub'>A meal can be one recipe or a combination of recipes. Flexible in-between items capture wake-up drinks, tea, snacks, pre/post workout items or notes without data loss.</div>", unsafe_allow_html=True)
    st.markdown("<div class='hm-mini-grid'><div class='hm-mini'><div class='hm-mini-label'>Fixed Slots</div><div class='hm-mini-value'>7</div></div><div class='hm-mini'><div class='hm-mini-label'>Flexible Add-ons</div><div class='hm-mini-value'>Yes</div></div><div class='hm-mini'><div class='hm-mini-label'>Recipe Combination</div><div class='hm-mini-value'>Yes</div></div><div class='hm-mini'><div class='hm-mini-label'>Cycle</div><div class='hm-mini-value'>7 Days</div></div></div>", unsafe_allow_html=True)
    for day_number in range(1, 8):
        with st.expander(_day_label(start_date, day_number), expanded=(day_number == 1)):
            for slot in MEAL_SLOTS:
                st.markdown(f"<div class='hm-slot-caption'>{slot}</div>", unsafe_allow_html=True)
                r1, r2, qty, instr = st.columns([0.30, 0.30, 0.16, 0.24], gap="small")
                with r1:
                    st.selectbox("Recipe 1", recipe_options, key=f"meal_{day_number}_{slot}_r1", label_visibility="collapsed")
                with r2:
                    st.selectbox("Recipe 2 / combination", recipe_options, key=f"meal_{day_number}_{slot}_r2", label_visibility="collapsed")
                with qty:
                    st.text_input("Quantity", value="", placeholder="Portion", key=f"meal_{day_number}_{slot}_qty", label_visibility="collapsed")
                with instr:
                    st.text_input("Instruction", value="", placeholder="Instruction", key=f"meal_{day_number}_{slot}_inst", label_visibility="collapsed")
            st.markdown("<div class='hm-slot-caption'>Flexible add-on / in-between item</div>", unsafe_allow_html=True)
            f1, f2, f3, f4 = st.columns([0.16, 0.24, 0.26, 0.34], gap="small")
            with f1:
                st.text_input("Time", value="", placeholder="e.g. 4:30 PM", key=f"meal_{day_number}_flex_time", label_visibility="collapsed")
            with f2:
                st.selectbox("Type", ["Snack", "Drink", "Recipe", "Note", "Pre-workout", "Post-workout"], key=f"meal_{day_number}_flex_type", label_visibility="collapsed")
            with f3:
                st.text_input("Item", value="", placeholder="Tea / fruit / nuts / recipe", key=f"meal_{day_number}_flex_item", label_visibility="collapsed")
            with f4:
                st.text_input("Instruction", value="", placeholder="Quantity and instruction", key=f"meal_{day_number}_flex_inst", label_visibility="collapsed")
            b1, b2, b3 = st.columns(3)
            with b1:
                st.button("Copy Day 1 to all days", key=f"meal_copy_all_{day_number}", use_container_width=True, disabled=True)
            with b2:
                st.button("Copy previous day", key=f"meal_copy_prev_{day_number}", use_container_width=True, disabled=True)
            with b3:
                st.button("Add another flexible item", key=f"meal_add_flex_{day_number}", use_container_width=True, disabled=True)
    st.markdown("</div>", unsafe_allow_html=True)

with exercise_tab:
    st.markdown("<div class='hm-mock-section'>", unsafe_allow_html=True)
    st.markdown("<div class='hm-mock-title'>Exercise Regime · Day 1 to Day 7</div>", unsafe_allow_html=True)
    st.markdown("<div class='hm-mock-sub'>Each slot supports multiple exercises. Preferred Time handles personalised exercise windows.</div>", unsafe_allow_html=True)
    for day_number in range(1, 8):
        with st.expander(_day_label(start_date, day_number), expanded=(day_number == 1)):
            rest_day = st.checkbox("Rest day / mobility-only day", key=f"exercise_rest_{day_number}")
            for slot in EXERCISE_SLOTS:
                st.markdown(f"<div class='hm-slot-caption'>{slot}</div>", unsafe_allow_html=True)
                e1, e2, dur, intensity, instr = st.columns([0.25, 0.25, 0.13, 0.14, 0.23], gap="small")
                with e1:
                    st.selectbox("Exercise 1", exercise_options, key=f"exercise_{day_number}_{slot}_e1", label_visibility="collapsed", disabled=rest_day)
                with e2:
                    st.selectbox("Exercise 2", exercise_options, key=f"exercise_{day_number}_{slot}_e2", label_visibility="collapsed", disabled=rest_day)
                with dur:
                    st.text_input("Duration", value="", placeholder="30 min", key=f"exercise_{day_number}_{slot}_dur", label_visibility="collapsed", disabled=rest_day)
                with intensity:
                    st.selectbox("Intensity", INTENSITY_OPTIONS, key=f"exercise_{day_number}_{slot}_intensity", label_visibility="collapsed", disabled=rest_day)
                with instr:
                    st.text_input("Instruction", value="", placeholder="Instruction", key=f"exercise_{day_number}_{slot}_inst", label_visibility="collapsed", disabled=rest_day)
            b1, b2, b3 = st.columns(3)
            with b1:
                st.button("Copy Day 1 to all days", key=f"exercise_copy_all_{day_number}", use_container_width=True, disabled=True)
            with b2:
                st.button("Copy previous day", key=f"exercise_copy_prev_{day_number}", use_container_width=True, disabled=True)
            with b3:
                st.button("Add exercise row", key=f"exercise_add_row_{day_number}", use_container_width=True, disabled=True)
    st.markdown("</div>", unsafe_allow_html=True)

with supplement_tab:
    st.markdown("<div class='hm-mock-section'>", unsafe_allow_html=True)
    st.markdown("<div class='hm-mock-title'>Supplement Regime · Day 1 to Day 7</div>", unsafe_allow_html=True)
    st.markdown("<div class='hm-mock-sub'>Supplements can be pulled from active member regimen and overridden inside this weekly profile/snapshot.</div>", unsafe_allow_html=True)
    active_supps = []
    if member_options:
        active_supps = list_active_member_supplements(member_options.get(selected_member, {}).get("id", ""))
    supp_options = ["— Select supplement —"] + [
        f"{row.get('id')} — {_clean(row.get('supplement_name')) or 'Supplement'} · {_clean(row.get('dosage'))} · {_clean(row.get('frequency'))}" for row in active_supps
    ]
    if not active_supps:
        st.info("No active member supplements found. Mock-up still shows the override structure below.")
    for day_number in range(1, 8):
        with st.expander(_day_label(start_date, day_number), expanded=(day_number == 1)):
            for slot in SUPPLEMENT_SLOTS:
                st.markdown(f"<div class='hm-slot-caption'>{slot}</div>", unsafe_allow_html=True)
                s1, dose, freq, timing, instr = st.columns([0.30, 0.15, 0.15, 0.16, 0.24], gap="small")
                with s1:
                    st.selectbox("Supplement", supp_options, key=f"supp_{day_number}_{slot}_s1", label_visibility="collapsed")
                with dose:
                    st.text_input("Dosage", value="", placeholder="400 mg", key=f"supp_{day_number}_{slot}_dose", label_visibility="collapsed")
                with freq:
                    st.selectbox("Frequency", FREQUENCY_OPTIONS, key=f"supp_{day_number}_{slot}_freq", label_visibility="collapsed")
                with timing:
                    st.text_input("Timing", value=slot if slot != "Preferred Time" else "", placeholder="Timing", key=f"supp_{day_number}_{slot}_timing", label_visibility="collapsed")
                with instr:
                    st.text_input("Instruction", value="", placeholder="With food / after dinner", key=f"supp_{day_number}_{slot}_inst", label_visibility="collapsed")
            b1, b2, b3 = st.columns(3)
            with b1:
                st.button("Copy active regimen", key=f"supp_copy_active_{day_number}", use_container_width=True, disabled=True)
            with b2:
                st.button("Copy Day 1 to all days", key=f"supp_copy_all_{day_number}", use_container_width=True, disabled=True)
            with b3:
                st.button("Add supplement row", key=f"supp_add_row_{day_number}", use_container_width=True, disabled=True)
    st.markdown("</div>", unsafe_allow_html=True)

with preview_tab:
    st.markdown("<div class='hm-mock-section'>", unsafe_allow_html=True)
    st.markdown("<div class='hm-mock-title'>Preview & End-to-End Flow Review</div>", unsafe_allow_html=True)
    st.markdown("<div class='hm-mock-sub'>Before implementation, this section is used to verify that admin, web member and Flutter member will read the same contract without data loss.</div>", unsafe_allow_html=True)
    st.markdown(
        f"""
<div class='hm-preview-box'>
<b>Recommendation Profile:</b> {profile_name}<br>
<b>Clone Source:</b> {clone_from}<br>
<b>Assigned Member:</b> {selected_member if member_options else 'NA'}<br>
<b>Start Date:</b> {start_date.isoformat()}<br>
<b>Cycle:</b> Weekly cyclical until replaced or stopped<br>
<b>Profile Tags:</b> {region} · {age_band} · {diet_type} · {', '.join(health_concern) if health_concern else 'No concern selected'}
</div>
""",
        unsafe_allow_html=True,
    )
    st.markdown("#### Contract sections expected after implementation")
    st.code(
        """recommendation_profile
  profile_id, profile_name, clone_from_profile_id, version, tags

weekly_meal_structure
  day_1 ... day_7
  fixed_slots + flexible_add_on_slots
  each meal can contain one recipe or recipe combination

weekly_exercise_regime
  day_1 ... day_7
  morning/evening/preferred_time
  multiple exercises allowed

weekly_supplement_regime
  day_1 ... day_7
  dosage/frequency/timing/instruction
  supplement override allowed

member_assignment
  member_id, start_date, weekly_cyclical=true, status=active/replaced/stopped

member_consumption
  My Recommendations = full active weekly profile
  Today’s Journey = calculated current day slice from active cycle""",
        language="text",
    )
    st.markdown("#### Review checkpoints before final coding")
    st.checkbox("Admin can create/clone Recommendation Profile without overwriting existing profile", key="mock_check_1")
    st.checkbox("Meal structure captures fixed meals and in-between items without forcing data into wrong slots", key="mock_check_2")
    st.checkbox("Exercise regime supports multiple exercises and rest-day guidance", key="mock_check_3")
    st.checkbox("Supplement regime supports active-regimen pull plus weekly override", key="mock_check_4")
    st.checkbox("Published snapshot can feed both Web Today’s Journey and Flutter My Recommendations", key="mock_check_5")
    st.checkbox("No data loss between admin, web member and Flutter member contracts", key="mock_check_6")
    st.markdown("</div>", unsafe_allow_html=True)

render_page_nav(
    "Recommendation Profile Builder Mock-up",
    back_page="pages/10_Admin_Dashboard.py",
    dashboard_page="pages/10_Admin_Dashboard.py",
    show_evaluation=False,
    show_dashboard=True,
    location="bottom",
)
render_back_to_top()
