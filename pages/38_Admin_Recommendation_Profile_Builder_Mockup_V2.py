import datetime as dt
import streamlit as st

from components.guards import require_admin
from components.db import list_members
from components.ui_common import inject_global_styles, apply_luxe_theme, utility_logout_bar, topbar, render_page_nav, render_back_to_top

st.set_page_config(page_title="Recommendation Profile Builder Mock-up V2", page_icon="💚", layout="wide", initial_sidebar_state="collapsed")
inject_global_styles()
apply_luxe_theme()
require_admin()
utility_logout_bar()

topbar("Recommendation Profile Builder Mock-up V2", "Clean structure review before implementation.", "Admin recommendations")

st.markdown("""
<style>
.hm-card{border:1px solid #E3C98E;background:#FFFDF8;border-radius:18px;padding:1rem;margin:.65rem 0 1rem;box-shadow:0 8px 18px rgba(15,23,42,.04)}
.hm-title{color:#064E3B;font-size:1.04rem;font-weight:950;margin:0 0 .25rem}.hm-sub{color:#64748B;font-size:.82rem;font-weight:720;margin:0 0 .7rem}
.hm-slot{font-size:.78rem;color:#72551A;font-weight:880;margin:.75rem 0 .25rem}.hm-head{font-size:.68rem;text-transform:uppercase;color:#64748B;font-weight:950;margin:.12rem 0 -.12rem}
.hm-day{border:1px solid #E3C98E;background:white;border-radius:16px;padding:.7rem .8rem;margin:.45rem 0 .85rem}.hm-day [data-testid="stButton"]>button{min-height:2.35rem!important;border-radius:14px!important;font-weight:900!important}
div[data-baseweb="tab-list"]{gap:.55rem!important;border:1px solid #E3C98E!important;background:linear-gradient(135deg,#FFFDF8,#FFF6E4)!important;border-radius:20px!important;padding:.5rem!important;box-shadow:0 9px 20px rgba(15,23,42,.055)!important;margin:.4rem 0 1rem!important;}
button[data-baseweb="tab"]{background:#fff!important;border:1.15px solid rgba(216,180,98,.72)!important;border-radius:15px!important;min-height:2.55rem!important;padding:.48rem .86rem!important;font-weight:900!important;box-shadow:0 4px 10px rgba(15,23,42,.035)!important;}
button[data-baseweb="tab"] p{font-size:.87rem!important;font-weight:930!important;color:#064E3B!important;}
button[data-baseweb="tab"][aria-selected="true"]{background:linear-gradient(135deg,#FFF3D6,#FFFFFF)!important;border:1.5px solid #B89345!important;box-shadow:0 8px 18px rgba(15,23,42,.08)!important;}
.hm-preview{border:1px dashed #D8A84E;background:#FFF9EC;border-radius:16px;padding:.75rem .85rem;margin:.35rem 0;color:#475569;font-size:.83rem;font-weight:740;line-height:1.4}
</style>
""", unsafe_allow_html=True)

RECIPES = ["-- Select recipe --", "Moong Chilla", "Paneer Salad", "Fruit + Nuts", "Herbal Tea"]
EXERCISES = ["-- Select exercise --", "Brisk Walking", "Cat-Cow Stretch", "Breathing Exercise", "Mobility Flow"]
SUPPLEMENTS = ["-- Select supplement --", "Magnesium", "Vitamin D", "Omega 3", "Probiotic"]

members = list_members()
member_options = [f"{m.get('name') or 'Member'} - {m.get('email') or m.get('id')}" for m in members] if members else ["No active member available"]


def current_start_date():
    return st.session_state.get("v2_plan_start_date", dt.date.today())


def dlabel(day):
    date_value = current_start_date() + dt.timedelta(days=day - 1)
    return f"Day {day} - {date_value.strftime('%a, %d %b')}"


def row_count(key):
    st.session_state.setdefault(key, 1)
    return st.session_state[key]


def add_row(key):
    st.session_state[key] = row_count(key) + 1


def select_day(key):
    st.session_state.setdefault(key, 1)
    st.markdown("<div class='hm-day'><b>Select day to edit</b><br><span style='color:#64748B;font-size:.8rem;font-weight:720;'>Row 1: Day 1 to Day 4. Row 2: Day 5 to Day 7.</span></div>", unsafe_allow_html=True)
    for row in ([1, 2, 3, 4], [5, 6, 7]):
        cols = st.columns(len(row), gap="small")
        for col, day in zip(cols, row):
            with col:
                if st.button(dlabel(day), key=f"{key}_{day}", type=("primary" if st.session_state[key] == day else "secondary"), use_container_width=True):
                    st.session_state[key] = day
                    st.rerun()
    return st.session_state[key]


def meal_rows(day, slot):
    key = f"meal_{day}_{slot}"
    for i in range(row_count(key)):
        st.markdown("<div class='hm-head'>Recipe - Portion - Instruction</div>", unsafe_allow_html=True)
        a, b, c = st.columns([.44, .2, .36])
        a.selectbox("Recipe", RECIPES, key=f"recipe_{key}_{i}", label_visibility="collapsed")
        b.text_input("Portion", key=f"portion_{key}_{i}", label_visibility="collapsed")
        c.text_input("Instruction", key=f"instruction_{key}_{i}", label_visibility="collapsed")
    if st.button("Add food item", key=f"add_{key}", use_container_width=True):
        add_row(key); st.rerun()


def exercise_rows(day, slot):
    key = f"exercise_{day}_{slot}"
    for i in range(row_count(key)):
        st.markdown("<div class='hm-head'>Exercise - Time - Intensity - Instruction</div>", unsafe_allow_html=True)
        a, b, c, d = st.columns([.4, .18, .18, .24])
        a.selectbox("Exercise", EXERCISES, key=f"ex_{key}_{i}", label_visibility="collapsed")
        b.time_input("Time", value=dt.time(7, 0), key=f"extime_{key}_{i}", label_visibility="collapsed")
        c.selectbox("Intensity", ["Low", "Moderate", "High", "As tolerated"], key=f"intensity_{key}_{i}", label_visibility="collapsed")
        d.text_input("Instruction", key=f"exinst_{key}_{i}", label_visibility="collapsed")
    if st.button("Add workout item", key=f"add_{key}", use_container_width=True):
        add_row(key); st.rerun()


def supplement_rows(day, slot):
    key = f"supplement_{day}_{slot}"
    for i in range(row_count(key)):
        st.markdown("<div class='hm-head'>Supplement - Time - Dosage/Frequency - Instruction</div>", unsafe_allow_html=True)
        a, b, c, d = st.columns([.36, .16, .24, .24])
        a.selectbox("Supplement", SUPPLEMENTS, key=f"supp_{key}_{i}", label_visibility="collapsed")
        b.time_input("Time", value=dt.time(8, 0), key=f"supptime_{key}_{i}", label_visibility="collapsed")
        c.text_input("Dosage/Frequency", key=f"dose_{key}_{i}", label_visibility="collapsed")
        d.text_input("Instruction", key=f"suppinst_{key}_{i}", label_visibility="collapsed")
    if st.button("Add supplement item", key=f"add_{key}", use_container_width=True):
        add_row(key); st.rerun()


t1, t2, t3, t4, t5 = st.tabs(["Profile Setup", "Meal Structure", "Exercise Regime", "Supplement Regime", "Preview & End-to-End Flow"])

with t1:
    st.markdown("<div class='hm-card'>", unsafe_allow_html=True)
    st.markdown("<div class='hm-title'>Recommendation Profile Setup</div><div class='hm-sub'>Reusable profile with cloning, categorisation, member assignment and cycle context.</div>", unsafe_allow_html=True)
    c1, c2 = st.columns(2, gap="large")
    with c1:
        profile_name = st.text_input("Profile Name", value="North India - Adult - Weight Management - Vegetarian", key="v2_profile_name")
        clone_from = st.selectbox("Clone From Existing Profile", ["New profile", "Profile A - Gut Reset", "Profile B - Weight Management", "Profile C - Senior Wellness"], key="v2_clone_from")
        change_note = st.text_input("Change Note", value="Cloned and adjusted for member preference / region / concern", key="v2_change_note")
        profile_status = st.selectbox("Profile Status", ["Draft", "Active", "Archived"], key="v2_profile_status")
    with c2:
        region = st.text_input("Region / Food Culture", value="North India", key="v2_region")
        age_band = st.selectbox("Age Band", ["Teen", "18-30", "31-45", "46-60", "60+"], index=2, key="v2_age_band")
        concerns = st.multiselect("Health Concerns", ["Weight Management", "Gut Health", "Diabetes Support", "Energy", "Inflammation", "Sleep", "General Wellness"], default=["Weight Management"], key="v2_health_concerns")
        diet_type = st.selectbox("Diet Type", ["Vegetarian", "Non-vegetarian", "Vegan", "Eggetarian", "Jain", "Custom"], key="v2_diet_type")
    a1, a2 = st.columns(2, gap="large")
    with a1:
        assigned_member = st.selectbox("Example Member Assignment", member_options, key="v2_assigned_member")
        profile_note = st.text_area("Profile-level Nutritionist Note", value="", height=90, key="v2_profile_note")
    with a2:
        start_date = st.date_input("Plan Start Date", value=dt.date.today(), key="v2_plan_start_date")
        cycle_rule = st.text_input("Cycle Rule", value="Weekly cyclical until replaced or stopped", disabled=True, key="v2_cycle_rule")
        st.text_input("Implementation Status", value="Mock-up only: no save or publish yet", disabled=True, key="v2_implementation_status")
    st.markdown("</div>", unsafe_allow_html=True)

with t2:
    st.markdown("<div class='hm-card'>", unsafe_allow_html=True)
    st.markdown("<div class='hm-title'>Meal Structure</div><div class='hm-sub'>Recipe, Portion and Instruction stay constant. Add food item creates extra recipe rows.</div>", unsafe_allow_html=True)
    day = select_day("meal_day")
    for slot in ["Wake-up / Early Morning", "Breakfast", "Mid-morning Snack", "Lunch", "Evening Snack / Tea", "Dinner", "Bedtime"]:
        st.markdown(f"<div class='hm-slot'>{slot}</div>", unsafe_allow_html=True)
        meal_rows(day, slot)
    c1, c2 = st.columns(2)
    c1.button("Copy Day 1 to all days", key=f"meal_copy_all_{day}", use_container_width=True)
    c2.button("Copy previous day", key=f"meal_copy_previous_{day}", use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

with t3:
    st.markdown("<div class='hm-card'>", unsafe_allow_html=True)
    st.markdown("<div class='hm-title'>Exercise Regime</div><div class='hm-sub'>Exercise, Time, Intensity and Instruction stay constant.</div>", unsafe_allow_html=True)
    day = select_day("exercise_day")
    for slot in ["Morning", "Evening", "Preferred Time"]:
        st.markdown(f"<div class='hm-slot'>{slot}</div>", unsafe_allow_html=True)
        exercise_rows(day, slot)
    c1, c2, c3 = st.columns(3)
    c1.button("Copy Day 1 to all days", key=f"exercise_copy_all_{day}", use_container_width=True)
    c2.button("Copy previous day", key=f"exercise_copy_previous_{day}", use_container_width=True)
    c3.button("Add preferred-time slot", key=f"exercise_add_preferred_time_{day}", use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

with t4:
    st.markdown("<div class='hm-card'>", unsafe_allow_html=True)
    st.markdown("<div class='hm-title'>Supplement Regime</div><div class='hm-sub'>Supplement, Time, Dosage/Frequency and Instruction stay constant.</div>", unsafe_allow_html=True)
    day = select_day("supp_day")
    for slot in ["Morning", "Afternoon", "Evening", "Before Bed", "Preferred Time"]:
        st.markdown(f"<div class='hm-slot'>{slot}</div>", unsafe_allow_html=True)
        supplement_rows(day, slot)
    c1, c2, c3 = st.columns(3)
    c1.button("Copy active regimen", key=f"supp_copy_active_{day}", use_container_width=True)
    c2.button("Copy Day 1 to all days", key=f"supp_copy_all_{day}", use_container_width=True)
    c3.button("Copy previous day", key=f"supp_copy_previous_{day}", use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

with t5:
    st.markdown("<div class='hm-card'>", unsafe_allow_html=True)
    st.markdown("<div class='hm-title'>Preview & End-to-End Flow Review</div><div class='hm-sub'>Objective: freeze the shared admin, web member and Flutter member data contract before implementation.</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='hm-preview'><b>Profile:</b> {profile_name}<br><b>Clone Source:</b> {clone_from}<br><b>Status:</b> {profile_status}<br><b>Assigned Member:</b> {assigned_member}<br><b>Start Date:</b> {start_date.isoformat()}<br><b>Tags:</b> {region} - {age_band} - {diet_type} - {', '.join(concerns) if concerns else 'No health concern selected'}<br><b>Change Note:</b> {change_note or 'NA'}</div>", unsafe_allow_html=True)
    st.code("My Recommendations = full active weekly profile\nToday's Journey = current day slice from the active weekly cycle", language="text")
    st.markdown("</div>", unsafe_allow_html=True)

render_page_nav("Recommendation Profile Builder Mock-up V2", back_page="pages/10_Admin_Dashboard.py", dashboard_page="pages/10_Admin_Dashboard.py", show_evaluation=False, show_dashboard=True, location="bottom")
render_back_to_top()
