import datetime as dt
import streamlit as st

from components.guards import require_admin
from components.ui_common import inject_global_styles, apply_luxe_theme, utility_logout_bar, topbar, render_page_nav, render_back_to_top

st.set_page_config(page_title="Recommendation Profile Builder Mock-up V4", page_icon="💚", layout="wide", initial_sidebar_state="collapsed")
inject_global_styles()
apply_luxe_theme()
require_admin()
utility_logout_bar()

topbar("Recommendation Profile Builder Mock-up V4", "Full profile setup, weekly planner and expanded end-to-end flow review.", "Admin recommendations")

st.markdown("""
<style>
.hm-title{color:#064E3B;font-size:1.04rem;font-weight:950;margin:0 0 .25rem}.hm-sub{color:#64748B;font-size:.82rem;font-weight:720;margin:0 0 .7rem}
.hm-slot{font-size:.78rem;color:#72551A;font-weight:880;margin:.75rem 0 .25rem}.hm-head{font-size:.68rem;text-transform:uppercase;color:#64748B;font-weight:950;margin:.12rem 0 -.12rem}
.hm-day{border:1px solid #E3C98E;background:white;border-radius:16px;padding:.7rem .8rem;margin:.45rem 0 .85rem}.hm-day [data-testid="stButton"]>button{min-height:2.35rem!important;border-radius:14px!important;font-weight:900!important}
.hm-section-nav{margin:.35rem 0 .8rem 0;}
.hm-section-nav [data-testid="stButton"]>button{min-height:2.55rem!important;border-radius:15px!important;font-weight:930!important;border:1.15px solid rgba(216,180,98,.72)!important;background:#fff!important;color:#064E3B!important;box-shadow:0 4px 10px rgba(15,23,42,.035)!important;}
.hm-section-nav [data-testid="stButton"]>button[kind="primary"]{background:linear-gradient(135deg,#FFF3D6,#FFFFFF)!important;border:1.5px solid #B89345!important;color:#064E3B!important;box-shadow:0 8px 18px rgba(15,23,42,.08)!important;}
.hm-section-nav [data-testid="stButton"]>button[kind="primary"] *{color:#064E3B!important;}
.hm-preview{border:1px dashed #D8A84E;background:#FFF9EC;border-radius:16px;padding:.75rem .85rem;margin:.35rem 0;color:#475569;font-size:.83rem;font-weight:740;line-height:1.45}
.hm-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:.7rem;margin:.55rem 0}.hm-mini{border:1px solid #E3C98E;background:#fff;border-radius:16px;padding:.75rem .85rem}.hm-mini b{color:#064E3B}
.hm-readiness{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:.55rem;margin:.55rem 0 0}.hm-readiness-item{background:#fff;border:1px solid #E3C98E;border-radius:14px;padding:.58rem .68rem;line-height:1.35}
.hm-pill{display:inline-block;border-radius:999px;padding:.13rem .5rem;margin:.15rem .2rem .15rem 0;font-size:.7rem;font-weight:950}.hm-ok{background:#ECFDF5;color:#047857;border:1px solid #A7F3D0}.hm-pending{background:#FFF7ED;color:#B45309;border:1px solid #FED7AA}.hm-info{background:#EFF6FF;color:#1D4ED8;border:1px solid #BFDBFE}
.hm-member-flow{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:.7rem;margin:.55rem 0}.hm-member-card{border:1px solid #E3C98E;background:#fff;border-radius:16px;padding:.8rem .9rem;min-height:8rem}.hm-member-card b{display:block;color:#064E3B;font-size:.92rem;margin-bottom:.32rem}.hm-member-card span{color:#475569;font-size:.82rem;font-weight:740;line-height:1.45}
</style>
""", unsafe_allow_html=True)

RECIPES = ["-- Select recipe --", "Moong Chilla", "Paneer Salad", "Fruit + Nuts", "Herbal Tea"]
EXERCISES = ["-- Select exercise --", "Brisk Walking", "Cat-Cow Stretch", "Breathing Exercise", "Mobility Flow"]
SUPPLEMENTS = ["-- Select supplement --", "Magnesium", "Vitamin D", "Omega 3", "Probiotic"]
SECTIONS = ["Profile Setup", "Meal Structure", "Exercise Regime", "Supplement Regime", "Preview & End-to-End Flow"]


def base_date():
    return st.session_state.get("v4_start_date", dt.date.today())


def day_label(day):
    return f"Day {day} - {(base_date() + dt.timedelta(days=day-1)).strftime('%a, %d %b')}"


def count(key):
    st.session_state.setdefault(key, 1)
    return st.session_state[key]


def add_row(key):
    st.session_state[key] = count(key) + 1


def day_picker(key):
    st.session_state.setdefault(key, 1)
    st.markdown("<div class='hm-day'><b>Select day to edit</b><br><span style='color:#64748B;font-size:.8rem;font-weight:720;'>Row 1: Day 1 to Day 4. Row 2: Day 5 to Day 7.</span></div>", unsafe_allow_html=True)
    for row in ([1, 2, 3, 4], [5, 6, 7]):
        cols = st.columns(len(row), gap="small")
        for col, day in zip(cols, row):
            with col:
                if st.button(day_label(day), key=f"{key}_{day}", type=("primary" if st.session_state[key] == day else "secondary"), use_container_width=True):
                    st.session_state[key] = day
                    st.rerun()
    return st.session_state[key]


def item_row(kind, day, slot):
    key = f"{kind}_{day}_{slot}"
    for idx in range(count(key)):
        if kind == "meal":
            st.markdown("<div class='hm-head'>Recipe - Portion - Instruction</div>", unsafe_allow_html=True)
            a, b, c = st.columns([.44, .20, .36])
            a.selectbox("Recipe", RECIPES, key=f"{key}_recipe_{idx}", label_visibility="collapsed")
            b.text_input("Portion", key=f"{key}_portion_{idx}", label_visibility="collapsed")
            c.text_input("Instruction", key=f"{key}_instruction_{idx}", label_visibility="collapsed")
        elif kind == "exercise":
            st.markdown("<div class='hm-head'>Exercise - Time - Intensity - Instruction</div>", unsafe_allow_html=True)
            a, b, c, d = st.columns([.40, .18, .18, .24])
            a.selectbox("Exercise", EXERCISES, key=f"{key}_exercise_{idx}", label_visibility="collapsed")
            b.time_input("Time", value=dt.time(7, 0), key=f"{key}_time_{idx}", label_visibility="collapsed")
            c.selectbox("Intensity", ["Low", "Moderate", "High", "As tolerated"], key=f"{key}_intensity_{idx}", label_visibility="collapsed")
            d.text_input("Instruction", key=f"{key}_instruction_{idx}", label_visibility="collapsed")
        else:
            st.markdown("<div class='hm-head'>Supplement - Time - Dosage/Frequency - Instruction</div>", unsafe_allow_html=True)
            a, b, c, d = st.columns([.36, .16, .24, .24])
            a.selectbox("Supplement", SUPPLEMENTS, key=f"{key}_supplement_{idx}", label_visibility="collapsed")
            b.time_input("Time", value=dt.time(8, 0), key=f"{key}_time_{idx}", label_visibility="collapsed")
            c.text_input("Dosage/Frequency", key=f"{key}_dose_{idx}", label_visibility="collapsed")
            d.text_input("Instruction", key=f"{key}_instruction_{idx}", label_visibility="collapsed")
    label = {"meal": "Add food item", "exercise": "Add workout item", "supplement": "Add supplement item"}[kind]
    if st.button(label, key=f"add_{key}", use_container_width=True):
        add_row(key)
        st.rerun()

st.session_state.setdefault("v4_active_section", "Profile Setup")
st.markdown("<div class='hm-section-nav'>", unsafe_allow_html=True)
nav_cols = st.columns(len(SECTIONS), gap="small")
for col, section_name in zip(nav_cols, SECTIONS):
    with col:
        if st.button(section_name, key=f"v4_nav_{section_name}", type=("primary" if st.session_state["v4_active_section"] == section_name else "secondary"), use_container_width=True):
            st.session_state["v4_active_section"] = section_name
            st.rerun()
st.markdown("</div>", unsafe_allow_html=True)
section = st.session_state["v4_active_section"]

profile_name = st.session_state.get("v4_profile_name", "North India - Adult - Weight Management - Vegetarian")
clone_from = st.session_state.get("v4_clone_from", "New profile")
change_note = st.session_state.get("v4_change_note", "Cloned and adjusted for member preference / region / concern")
profile_status = st.session_state.get("v4_profile_status", "Draft")
region = st.session_state.get("v4_region", "North India")
age_band = st.session_state.get("v4_age_band", "31-45")
concerns = st.session_state.get("v4_concerns", ["Weight Management"])
diet_type = st.session_state.get("v4_diet_type", "Vegetarian")
assigned_member = st.session_state.get("v4_member", "Select member")
plan_start = st.session_state.get("v4_start_date", dt.date.today())
profile_note = st.session_state.get("v4_note", "")

if section == "Profile Setup":
    st.markdown("<div class='hm-title'>Recommendation Profile Setup</div><div class='hm-sub'>Reusable profile with cloning, categorisation, member assignment and cycle context.</div>", unsafe_allow_html=True)
    c1, c2 = st.columns(2, gap="large")
    with c1:
        profile_name = st.text_input("Profile Name", value=profile_name, key="v4_profile_name")
        clone_from = st.selectbox("Clone From Existing Profile", ["New profile", "Profile A - Gut Reset", "Profile B - Weight Management", "Profile C - Senior Wellness"], key="v4_clone_from")
        change_note = st.text_input("Change Note", value=change_note, key="v4_change_note")
        profile_status = st.selectbox("Profile Status", ["Draft", "Active", "Archived"], key="v4_profile_status")
    with c2:
        region = st.text_input("Region / Food Culture", value=region, key="v4_region")
        age_band = st.selectbox("Age Band", ["Teen", "18-30", "31-45", "46-60", "60+"], index=2, key="v4_age_band")
        concerns = st.multiselect("Health Concerns", ["Weight Management", "Gut Health", "Diabetes Support", "Energy", "Inflammation", "Sleep", "General Wellness"], default=concerns, key="v4_concerns")
        diet_type = st.selectbox("Diet Type", ["Vegetarian", "Non-vegetarian", "Vegan", "Eggetarian", "Jain", "Custom"], key="v4_diet_type")
    a1, a2 = st.columns(2, gap="large")
    with a1:
        assigned_member = st.selectbox("Example Member Assignment", ["Select member", "Example member"], key="v4_member")
        profile_note = st.text_area("Profile-level Nutritionist Note", value=profile_note, height=150, key="v4_note")
    with a2:
        plan_start = st.date_input("Plan Start Date", value=plan_start, key="v4_start_date")
        st.text_input("Cycle Rule", value="Weekly cyclical until replaced or stopped", disabled=True, key="v4_cycle")
        st.text_input("Implementation Status", value="Mock-up only: no save or publish yet", disabled=True, key="v4_status")

elif section == "Meal Structure":
    day = day_picker("v4_meal_day")
    for slot in ["Wake-up / Early Morning", "Breakfast", "Mid-morning Snack", "Lunch", "Evening Snack / Tea", "Dinner", "Bedtime"]:
        st.markdown(f"<div class='hm-slot'>{slot}</div>", unsafe_allow_html=True)
        item_row("meal", day, slot)
    x, y = st.columns(2)
    x.button("Copy Day 1 to all days", key=f"v4_meal_copy_all_{day}", use_container_width=True)
    y.button("Copy previous day", key=f"v4_meal_copy_prev_{day}", use_container_width=True)

elif section == "Exercise Regime":
    day = day_picker("v4_exercise_day")
    for slot in ["Morning", "Evening", "Preferred Time"]:
        st.markdown(f"<div class='hm-slot'>{slot}</div>", unsafe_allow_html=True)
        item_row("exercise", day, slot)
    x, y, z = st.columns(3)
    x.button("Copy Day 1 to all days", key=f"v4_ex_copy_all_{day}", use_container_width=True)
    y.button("Copy previous day", key=f"v4_ex_copy_prev_{day}", use_container_width=True)
    z.button("Add preferred-time slot", key=f"v4_ex_add_pref_{day}", use_container_width=True)

elif section == "Supplement Regime":
    day = day_picker("v4_supp_day")
    for slot in ["Morning", "Afternoon", "Evening", "Before Bed", "Preferred Time"]:
        st.markdown(f"<div class='hm-slot'>{slot}</div>", unsafe_allow_html=True)
        item_row("supplement", day, slot)
    x, y, z = st.columns(3)
    x.button("Copy active regimen", key=f"v4_supp_active_{day}", use_container_width=True)
    y.button("Copy Day 1 to all days", key=f"v4_supp_all_{day}", use_container_width=True)
    z.button("Copy previous day", key=f"v4_supp_prev_{day}", use_container_width=True)

else:
    member_ready = assigned_member != "Select member"
    member_pill = "hm-ok" if member_ready else "hm-pending"
    member_status = "Complete" if member_ready else "Pending"

    st.markdown("<div class='hm-title'>Preview & End-to-End Flow Review</div><div class='hm-sub'>This is the contract review page before implementation. It checks what Admin creates, what gets published, and what Web Member and Flutter Member consume.</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='hm-preview'><b>Profile Summary</b><br><b>Profile:</b> {profile_name}<br><b>Clone Source:</b> {clone_from}<br><b>Status:</b> {profile_status}<br><b>Assigned Member:</b> {assigned_member}<br><b>Start Date:</b> {plan_start.isoformat()}<br><b>Cycle:</b> Weekly cyclical until replaced or stopped<br><b>Tags:</b> {region} - {age_band} - {diet_type} - {', '.join(concerns) if concerns else 'No health concern selected'}<br><b>Change Note:</b> {change_note or 'NA'}<br><b>Profile Note:</b> {profile_note or 'NA'}</div>", unsafe_allow_html=True)
    st.markdown("""
<div class='hm-grid'>
  <div class='hm-mini'><b>1. Admin Creates</b><br>Profile setup, weekly meal structure, weekly exercise regime and weekly supplement regime.</div>
  <div class='hm-mini'><b>2. Admin Publishes</b><br>One active member recommendation profile with start date, weekly cycle rule and profile metadata.</div>
  <div class='hm-mini'><b>3. Member Web Reads</b><br>Today's Journey calculates the correct current-day slice from the active weekly cycle.</div>
  <div class='hm-mini'><b>4. Flutter Reads</b><br>My Recommendations shows the full active weekly profile and the same current cycle details.</div>
</div>
""", unsafe_allow_html=True)
    st.markdown(f"""
<div class='hm-preview'>
<b>Publish Readiness Checklist</b><br>
This checklist should remain on the admin side as the final gate before publish. It is useful because it prevents assigning an incomplete weekly profile to a member.
<div class='hm-readiness'>
  <div class='hm-readiness-item'><span class='hm-pill hm-ok'>Complete</span><br><b>Profile name added</b><br>Reusable profile identity is available.</div>
  <div class='hm-readiness-item'><span class='hm-pill hm-info'>Ready</span><br><b>Clone / source context captured</b><br>Admin can trace whether this is new or cloned.</div>
  <div class='hm-readiness-item'><span class='hm-pill {member_pill}'>{member_status}</span><br><b>Member assigned</b><br>Publishing must stay blocked until a member is selected.</div>
  <div class='hm-readiness-item'><span class='hm-pill hm-ok'>Complete</span><br><b>Start date selected</b><br>Start date drives the day-slice calculation.</div>
  <div class='hm-readiness-item'><span class='hm-pill hm-ok'>Complete</span><br><b>Weekly cycle rule present</b><br>Cycle continues until replaced or stopped.</div>
  <div class='hm-readiness-item'><span class='hm-pill hm-info'>Review</span><br><b>Profile-level note reviewed</b><br>Nutritionist/practitioner note should be checked before publish.</div>
  <div class='hm-readiness-item'><span class='hm-pill hm-info'>Review</span><br><b>Meal, exercise and supplement tabs reviewed</b><br>Admin confirms Day 1 to Day 7 content is ready.</div>
  <div class='hm-readiness-item'><span class='hm-pill hm-info'>Review</span><br><b>Preview checked</b><br>Admin confirms web and Flutter consumption logic before implementation.</div>
</div>
</div>
""", unsafe_allow_html=True)
    st.markdown("""
<div class='hm-preview'>
<b>How this profile will appear to the member</b><br>
<div class='hm-member-flow'>
  <div class='hm-member-card'>
    <b>My Recommendations</b>
    <span>Shows the member's full active weekly recommendation profile. This is the master 7-day view, including meal guidance, exercise guidance, supplement guidance, profile-level notes and active practitioner/admin instructions.</span>
  </div>
  <div class='hm-member-card'>
    <b>Today's Journey</b>
    <span>Shows only the current day's slice from the active weekly cycle. The day is calculated from the profile start date; for example, if today maps to Day 3, the member sees only Day 3 guidance.</span>
  </div>
  <div class='hm-member-card'>
    <b>Cycle Rule</b>
    <span>The same weekly cycle repeats until an admin replaces or stops the profile. This keeps the member experience simple without losing the complete weekly recommendation structure.</span>
  </div>
</div>
</div>
""", unsafe_allow_html=True)
    st.markdown("""
<div class='hm-preview'>
<b>Published Contract Sections</b><br>
recommendation_profile: profile id, name, clone source, status, tags, notes and cycle rule.<br>
weekly_meal_structure: Day 1 to Day 7, fixed meal slots, flexible food items, recipe, portion and instruction.<br>
weekly_exercise_regime: Day 1 to Day 7, morning/evening/preferred time, exercise, time, intensity and instruction.<br>
weekly_supplement_regime: Day 1 to Day 7, supplement, time, dosage/frequency and instruction.<br>
member_assignment: member id, start date, active/replaced/stopped status and assigned profile version.<br>
member_consumption: My Recommendations shows the full profile; Today's Journey shows today's calculated slice.
</div>
""", unsafe_allow_html=True)
    st.markdown("""
<div class='hm-preview'>
<b>No-data-loss checkpoints before implementation</b><br>
[ ] Clone creates a new profile version without overwriting the older profile.<br>
[ ] Meal combinations are stored as multiple recipe rows under the same meal slot.<br>
[ ] Flexible in-between food/drink items are not lost or forced into wrong meal slots.<br>
[ ] Exercise supports multiple workout rows and preferred-time rows.<br>
[ ] Supplement overrides keep supplement, time, dosage/frequency and instruction.<br>
[ ] Admin, Web Member and Flutter Member read the same published structure.<br>
[ ] Replacing or stopping a profile does not delete historical recommendations.
</div>
""", unsafe_allow_html=True)

render_page_nav("Recommendation Profile Builder Mock-up V4", back_page="pages/10_Admin_Dashboard.py", dashboard_page="pages/10_Admin_Dashboard.py", show_evaluation=False, show_dashboard=True, location="bottom")
render_back_to_top()
