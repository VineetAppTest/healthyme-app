import datetime as dt
import streamlit as st

from components.guards import require_admin
from components.ui_common import inject_global_styles, apply_luxe_theme, utility_logout_bar, topbar, render_page_nav, render_back_to_top

st.set_page_config(page_title="Recommendation Profile Builder Mock-up V3", page_icon="💚", layout="wide", initial_sidebar_state="collapsed")
inject_global_styles()
apply_luxe_theme()
require_admin()
utility_logout_bar()

topbar("Recommendation Profile Builder Mock-up V3", "Full profile setup and clean weekly planner review.", "Admin recommendations")

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


def start_date():
    return st.session_state.get("v3_start_date", dt.date.today())


def day_label(day):
    return f"Day {day} - {(start_date() + dt.timedelta(days=day-1)).strftime('%a, %d %b')}"


def count(key):
    st.session_state.setdefault(key, 1)
    return st.session_state[key]


def add(key):
    st.session_state[key] = count(key) + 1


def day_picker(key):
    st.session_state.setdefault(key, 1)
    st.markdown("<div class='hm-day'><b>Select day to edit</b><br><span style='color:#64748B;font-size:.8rem;font-weight:720;'>Row 1: Day 1 to Day 4. Row 2: Day 5 to Day 7.</span></div>", unsafe_allow_html=True)
    for row in ([1,2,3,4],[5,6,7]):
        cols = st.columns(len(row), gap="small")
        for col, day in zip(cols, row):
            with col:
                if st.button(day_label(day), key=f"{key}_{day}", type=("primary" if st.session_state[key] == day else "secondary"), use_container_width=True):
                    st.session_state[key] = day
                    st.rerun()
    return st.session_state[key]


def item_rows(kind, day, slot, options, cols):
    key = f"{kind}_{day}_{slot}"
    for idx in range(count(key)):
        if kind == "meal":
            st.markdown("<div class='hm-head'>Recipe - Portion - Instruction</div>", unsafe_allow_html=True)
            a,b,c = st.columns([.44,.2,.36])
            a.selectbox("Recipe", options, key=f"{key}_recipe_{idx}", label_visibility="collapsed")
            b.text_input("Portion", key=f"{key}_portion_{idx}", label_visibility="collapsed")
            c.text_input("Instruction", key=f"{key}_instruction_{idx}", label_visibility="collapsed")
        elif kind == "exercise":
            st.markdown("<div class='hm-head'>Exercise - Time - Intensity - Instruction</div>", unsafe_allow_html=True)
            a,b,c,d = st.columns(cols)
            a.selectbox("Exercise", options, key=f"{key}_exercise_{idx}", label_visibility="collapsed")
            b.time_input("Time", value=dt.time(7,0), key=f"{key}_time_{idx}", label_visibility="collapsed")
            c.selectbox("Intensity", ["Low","Moderate","High","As tolerated"], key=f"{key}_intensity_{idx}", label_visibility="collapsed")
            d.text_input("Instruction", key=f"{key}_instruction_{idx}", label_visibility="collapsed")
        else:
            st.markdown("<div class='hm-head'>Supplement - Time - Dosage/Frequency - Instruction</div>", unsafe_allow_html=True)
            a,b,c,d = st.columns(cols)
            a.selectbox("Supplement", options, key=f"{key}_supplement_{idx}", label_visibility="collapsed")
            b.time_input("Time", value=dt.time(8,0), key=f"{key}_time_{idx}", label_visibility="collapsed")
            c.text_input("Dosage/Frequency", key=f"{key}_dose_{idx}", label_visibility="collapsed")
            d.text_input("Instruction", key=f"{key}_instruction_{idx}", label_visibility="collapsed")
    label = {"meal":"Add food item", "exercise":"Add workout item", "supplement":"Add supplement item"}[kind]
    if st.button(label, key=f"add_{key}", use_container_width=True):
        add(key)
        st.rerun()

profile, meal, exercise, supplement, preview = st.tabs(["Profile Setup", "Meal Structure", "Exercise Regime", "Supplement Regime", "Preview & End-to-End Flow"])

with profile:
    st.markdown("<div class='hm-card'>", unsafe_allow_html=True)
    st.markdown("<div class='hm-title'>Recommendation Profile Setup</div><div class='hm-sub'>Reusable profile with cloning, categorisation, member assignment and cycle context.</div>", unsafe_allow_html=True)
    c1,c2 = st.columns(2, gap="large")
    with c1:
        profile_name = st.text_input("Profile Name", value="North India - Adult - Weight Management - Vegetarian", key="v3_profile_name")
        clone_from = st.selectbox("Clone From Existing Profile", ["New profile", "Profile A - Gut Reset", "Profile B - Weight Management", "Profile C - Senior Wellness"], key="v3_clone_from")
        change_note = st.text_input("Change Note", value="Cloned and adjusted for member preference / region / concern", key="v3_change_note")
        profile_status = st.selectbox("Profile Status", ["Draft", "Active", "Archived"], key="v3_profile_status")
    with c2:
        region = st.text_input("Region / Food Culture", value="North India", key="v3_region")
        age_band = st.selectbox("Age Band", ["Teen", "18-30", "31-45", "46-60", "60+"], index=2, key="v3_age_band")
        concerns = st.multiselect("Health Concerns", ["Weight Management", "Gut Health", "Diabetes Support", "Energy", "Inflammation", "Sleep", "General Wellness"], default=["Weight Management"], key="v3_concerns")
        diet_type = st.selectbox("Diet Type", ["Vegetarian", "Non-vegetarian", "Vegan", "Eggetarian", "Jain", "Custom"], key="v3_diet_type")
    a1,a2 = st.columns(2, gap="large")
    with a1:
        assigned_member = st.selectbox("Example Member Assignment", ["Select member", "Example member"], key="v3_member")
        st.text_area("Profile-level Nutritionist Note", value="", height=90, key="v3_note")
    with a2:
        plan_start = st.date_input("Plan Start Date", value=dt.date.today(), key="v3_start_date")
        st.text_input("Cycle Rule", value="Weekly cyclical until replaced or stopped", disabled=True, key="v3_cycle")
        st.text_input("Implementation Status", value="Mock-up only: no save or publish yet", disabled=True, key="v3_status")
    st.markdown("</div>", unsafe_allow_html=True)

with meal:
    st.markdown("<div class='hm-card'>", unsafe_allow_html=True)
    day = day_picker("v3_meal_day")
    for slot in ["Wake-up / Early Morning", "Breakfast", "Mid-morning Snack", "Lunch", "Evening Snack / Tea", "Dinner", "Bedtime"]:
        st.markdown(f"<div class='hm-slot'>{slot}</div>", unsafe_allow_html=True)
        item_rows("meal", day, slot, RECIPES, [.44,.2,.36])
    x,y = st.columns(2)
    x.button("Copy Day 1 to all days", key=f"v3_meal_copy_all_{day}", use_container_width=True)
    y.button("Copy previous day", key=f"v3_meal_copy_prev_{day}", use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

with exercise:
    st.markdown("<div class='hm-card'>", unsafe_allow_html=True)
    day = day_picker("v3_exercise_day")
    for slot in ["Morning", "Evening", "Preferred Time"]:
        st.markdown(f"<div class='hm-slot'>{slot}</div>", unsafe_allow_html=True)
        item_rows("exercise", day, slot, EXERCISES, [.4,.18,.18,.24])
    x,y,z = st.columns(3)
    x.button("Copy Day 1 to all days", key=f"v3_ex_copy_all_{day}", use_container_width=True)
    y.button("Copy previous day", key=f"v3_ex_copy_prev_{day}", use_container_width=True)
    z.button("Add preferred-time slot", key=f"v3_ex_add_pref_{day}", use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

with supplement:
    st.markdown("<div class='hm-card'>", unsafe_allow_html=True)
    day = day_picker("v3_supp_day")
    for slot in ["Morning", "Afternoon", "Evening", "Before Bed", "Preferred Time"]:
        st.markdown(f"<div class='hm-slot'>{slot}</div>", unsafe_allow_html=True)
        item_rows("supplement", day, slot, SUPPLEMENTS, [.36,.16,.24,.24])
    x,y,z = st.columns(3)
    x.button("Copy active regimen", key=f"v3_supp_active_{day}", use_container_width=True)
    y.button("Copy Day 1 to all days", key=f"v3_supp_all_{day}", use_container_width=True)
    z.button("Copy previous day", key=f"v3_supp_prev_{day}", use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

with preview:
    st.markdown("<div class='hm-card'>", unsafe_allow_html=True)
    st.markdown(f"<div class='hm-preview'><b>Profile:</b> {profile_name}<br><b>Clone Source:</b> {clone_from}<br><b>Status:</b> {profile_status}<br><b>Assigned Member:</b> {assigned_member}<br><b>Start Date:</b> {plan_start.isoformat()}<br><b>Tags:</b> {region} - {age_band} - {diet_type} - {', '.join(concerns) if concerns else 'No health concern selected'}<br><b>Change Note:</b> {change_note or 'NA'}</div>", unsafe_allow_html=True)
    st.code("My Recommendations = full active weekly profile\nToday's Journey = current day slice from active weekly cycle", language="text")
    st.markdown("</div>", unsafe_allow_html=True)

render_page_nav("Recommendation Profile Builder Mock-up V3", back_page="pages/10_Admin_Dashboard.py", dashboard_page="pages/10_Admin_Dashboard.py", show_evaluation=False, show_dashboard=True, location="bottom")
render_back_to_top()
