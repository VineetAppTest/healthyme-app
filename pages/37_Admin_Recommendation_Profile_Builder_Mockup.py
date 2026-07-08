import datetime as dt

import streamlit as st

from components.guards import require_admin
from components.db import list_active_member_supplements, list_members
from components.recommendation_contract import list_repository_items
from components.ui_common import inject_global_styles, apply_luxe_theme, utility_logout_bar, topbar, render_page_nav, render_back_to_top

st.set_page_config(page_title="Recommendation Profile Builder Mock-up", page_icon="💚", layout="wide", initial_sidebar_state="collapsed")
inject_global_styles()
apply_luxe_theme()
require_admin()
utility_logout_bar()

topbar(
    "Recommendation Profile Builder Mock-up",
    "H9A.5E.1 structure review: 7-day meal, exercise and supplement planning before final implementation.",
    "Admin recommendations",
)

st.markdown("""
<style>
.hm-box{border:1px solid #E3C98E;background:#FFFDF8;border-radius:18px;padding:.9rem 1rem;margin:.65rem 0 1rem;box-shadow:0 8px 18px rgba(15,23,42,.04)}
.hm-note{border:1px solid #F4C56F;background:#FFFBEB;border-radius:16px;padding:.7rem .85rem;color:#7C4A03;font-size:.84rem;font-weight:840;line-height:1.38;margin:.3rem 0 .8rem}
.hm-title{color:#064E3B;font-size:1.02rem;font-weight:950;margin:0 0 .2rem}.hm-sub{color:#64748B;font-size:.81rem;font-weight:720;line-height:1.35;margin:0 0 .65rem}
.hm-slot{font-size:.78rem;color:#72551A;font-weight:870;margin:.7rem 0 .25rem}.hm-head{font-size:.68rem;text-transform:uppercase;letter-spacing:.04em;color:#64748B;font-weight:950;margin:.12rem 0 -.12rem}
.hm-preview{border:1px dashed #D8A84E;background:#FFF9EC;border-radius:16px;padding:.7rem .8rem;margin:.35rem 0;color:#475569;font-size:.82rem;font-weight:740;line-height:1.38}
.hm-flow{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:.55rem;margin:.45rem 0 .75rem}.hm-flow-card{border:1px solid #E3C98E;background:white;border-radius:14px;padding:.62rem .65rem;min-height:4.2rem}.hm-flow-title{color:#064E3B;font-size:.78rem;font-weight:950;line-height:1.15}.hm-flow-sub{color:#64748B;font-size:.70rem;font-weight:720;line-height:1.25;margin-top:.12rem}.hm-num{display:inline-flex;align-items:center;justify-content:center;width:1.35rem;height:1.35rem;border-radius:999px;background:#064E3B;color:white;font-weight:950;font-size:.75rem;margin-bottom:.28rem}
.hm-day{border:1px solid #E3C98E;background:white;border-radius:16px;padding:.65rem .75rem;margin:.45rem 0 .8rem}.hm-day [data-testid="stButton"]>button{min-height:2.35rem!important;border-radius:14px!important;font-weight:900!important}
@media(max-width:900px){.hm-flow{grid-template-columns:repeat(2,minmax(0,1fr));}}
</style>
""", unsafe_allow_html=True)

MEAL_SLOTS = ["Wake-up / Early Morning", "Breakfast", "Mid-morning Snack", "Lunch", "Evening Snack / Tea", "Dinner", "Bedtime"]
EXERCISE_SLOTS = ["Morning", "Evening", "Preferred Time"]
SUPPLEMENT_SLOTS = ["Morning", "Afternoon", "Evening", "Before Bed", "Preferred Time"]
INTENSITY_OPTIONS = ["Low", "Moderate", "High", "As tolerated"]
FREQUENCY_OPTIONS = ["Once", "Twice", "Thrice", "Custom"]


def clean(value):
    text = str(value or "").strip()
    return "" if text.lower() in {"nan", "none", "null", "na", "n/a", "select"} else text


def member_label(row):
    return f"{row.get('name') or 'Member'} — {row.get('email') or row.get('id')}"


def resource_label(row, fallback):
    title = clean(row.get("title")) or fallback
    meta = clean(row.get("meal_type")) or clean(row.get("duration_or_reps")) or clean(row.get("category"))
    return f"{row.get('id')} — {title}{' · ' + meta if meta else ''}"


def day_label(start_date, day_number):
    day = start_date + dt.timedelta(days=day_number - 1)
    return f"Day {day_number} · {day.strftime('%a, %d %b')}"


def count_key(kind, day_number, slot):
    safe_slot = str(slot).replace(" ", "_").replace("/", "_").replace("-", "_")
    return f"mock_count_{kind}_{day_number}_{safe_slot}"


def get_count(kind, day_number, slot, default=1):
    key = count_key(kind, day_number, slot)
    if key not in st.session_state:
        st.session_state[key] = default
    return int(st.session_state[key])


def add_item(kind, day_number, slot):
    key = count_key(kind, day_number, slot)
    st.session_state[key] = int(st.session_state.get(key, 1)) + 1


def copy_counts(kind, from_day, to_day, slots):
    for slot in slots:
        st.session_state[count_key(kind, to_day, slot)] = int(st.session_state.get(count_key(kind, from_day, slot), 1))


def copy_day_1_all(kind, slots, label):
    for day in range(2, 8):
        copy_counts(kind, 1, day, slots)
    st.success(f"{label}: Day 1 row structure copied to all days in this mock-up session.")


def copy_previous(kind, day_number, slots, label):
    if day_number <= 1:
        st.info(f"{label}: Day 1 has no previous day to copy from.")
        return
    copy_counts(kind, day_number - 1, day_number, slots)
    st.success(f"{label}: previous day row structure copied to Day {day_number} in this mock-up session.")


def day_selector(section_key, start_date):
    selected_key = f"{section_key}_selected_day"
    st.session_state.setdefault(selected_key, 1)
    st.markdown("<div class='hm-day'><b>Select day to edit</b><br><span style='color:#64748B;font-size:.8rem;font-weight:720;'>Day 1 to Day 4 are on the first row. Day 5 to Day 7 are on the second row.</span></div>", unsafe_allow_html=True)
    row1 = st.columns(4, gap="small")
    for idx, day in enumerate(range(1, 5)):
        with row1[idx]:
            button_type = "primary" if st.session_state[selected_key] == day else "secondary"
            if st.button(day_label(start_date, day), key=f"{section_key}_day_{day}", use_container_width=True, type=button_type):
                st.session_state[selected_key] = day
                st.rerun()
    row2 = st.columns(3, gap="small")
    for idx, day in enumerate(range(5, 8)):
        with row2[idx]:
            button_type = "primary" if st.session_state[selected_key] == day else "secondary"
            if st.button(day_label(start_date, day), key=f"{section_key}_day_{day}", use_container_width=True, type=button_type):
                st.session_state[selected_key] = day
                st.rerun()
    return int(st.session_state[selected_key])


st.markdown("""
<div class='hm-flow'>
  <div class='hm-flow-card'><div class='hm-num'>1</div><div class='hm-flow-title'>Base Units</div><div class='hm-flow-sub'>Recipe, exercise and supplement repositories.</div></div>
  <div class='hm-flow-card'><div class='hm-num'>2</div><div class='hm-flow-title'>Weekly Structures</div><div class='hm-flow-sub'>Meal, exercise and supplement weekly planning.</div></div>
  <div class='hm-flow-card'><div class='hm-num'>3</div><div class='hm-flow-title'>Recommendation Profile</div><div class='hm-flow-sub'>Reusable template with region, age, concerns and goals.</div></div>
  <div class='hm-flow-card'><div class='hm-num'>4</div><div class='hm-flow-title'>Assign / Clone</div><div class='hm-flow-sub'>Clone profile, adjust, assign and set start date.</div></div>
  <div class='hm-flow-card'><div class='hm-num'>5</div><div class='hm-flow-title'>Member View</div><div class='hm-flow-sub'>My Recommendations = full week; Today’s Journey = today’s slice.</div></div>
</div>
""", unsafe_allow_html=True)

st.markdown("<div class='hm-note'><b>Mock-up only.</b> Buttons add/copy visible row structures for review. Final save/publish comes in the implementation sprint.</div>", unsafe_allow_html=True)

members = list_members()
member_options = {member_label(m): m for m in members} if members else {}
recipe_options = ["— Select recipe —"] + [resource_label(r, "Recipe") for r in list_repository_items("recipes", active_only=True)]
exercise_options = ["— Select exercise —"] + [resource_label(r, "Exercise") for r in list_repository_items("exercises", active_only=True)]

profile_tab, meal_tab, exercise_tab, supplement_tab, preview_tab = st.tabs(["1. Profile Setup", "2. Meal Structure", "3. Exercise Regime", "4. Supplement Regime", "5. Preview & End-to-End Flow"])

with profile_tab:
    st.markdown("<div class='hm-box'>", unsafe_allow_html=True)
    st.markdown("<div class='hm-title'>Recommendation Profile Setup</div><div class='hm-sub'>Profiles are reusable templates. A nutritionist can clone Profile A, change it, and save it as Profile B.</div>", unsafe_allow_html=True)
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
        selected_member = st.selectbox("Example Member Assignment", list(member_options.keys()), key="mock_member_select") if member_options else "No member available"
    with cycle_col:
        start_date = st.date_input("Plan Start Date", value=dt.date.today(), key="mock_start_date")
        st.text_input("Cycle Rule", value="Weekly cyclical until replaced or stopped", disabled=True)
    st.markdown("</div>", unsafe_allow_html=True)

with meal_tab:
    st.markdown("<div class='hm-box'>", unsafe_allow_html=True)
    st.markdown("<div class='hm-title'>Meal Structure · Day 1 to Day 7</div><div class='hm-sub'>Recipe, Portion and Instruction stay constant. Add food item creates extra recipe rows.</div>", unsafe_allow_html=True)
    day_number = day_selector("meal", start_date)
    st.markdown(f"#### {day_label(start_date, day_number)}")
    for slot in MEAL_SLOTS:
        st.markdown(f"<div class='hm-slot'>{slot}</div>", unsafe_allow_html=True)
        for item_index in range(1, get_count("meal", day_number, slot) + 1):
            st.markdown("<div class='hm-head'>Recipe · Portion · Instruction</div>", unsafe_allow_html=True)
            recipe_col, portion_col, instr_col = st.columns([0.44, 0.20, 0.36], gap="small")
            with recipe_col:
                st.selectbox("Recipe", recipe_options, key=f"meal_{day_number}_{slot}_recipe_{item_index}", label_visibility="collapsed")
            with portion_col:
                st.text_input("Portion", placeholder="Portion", key=f"meal_{day_number}_{slot}_portion_{item_index}", label_visibility="collapsed")
            with instr_col:
                st.text_input("Instruction", placeholder="Instruction", key=f"meal_{day_number}_{slot}_instruction_{item_index}", label_visibility="collapsed")
        if st.button("Add food item", key=f"meal_{day_number}_{slot}_add_food", use_container_width=True):
            add_item("meal", day_number, slot)
            st.rerun()
    st.markdown("<div class='hm-slot'>Flexible add-on / in-between item</div>", unsafe_allow_html=True)
    for item_index in range(1, get_count("meal_flex", day_number, "flexible_item") + 1):
        st.markdown("<div class='hm-head'>Time · Item Type · Food / Drink Item · Quantity and Instruction</div>", unsafe_allow_html=True)
        f1, f2, f3, f4 = st.columns([0.18, 0.22, 0.28, 0.32], gap="small")
        with f1:
            st.time_input("Time", value=dt.time(16, 30), key=f"meal_{day_number}_flex_time_{item_index}", label_visibility="collapsed")
        with f2:
            st.selectbox("Type", ["Snack", "Drink", "Recipe", "Note", "Pre-workout", "Post-workout"], key=f"meal_{day_number}_flex_type_{item_index}", label_visibility="collapsed")
        with f3:
            st.text_input("Item", placeholder="Tea / fruit / nuts / recipe", key=f"meal_{day_number}_flex_item_{item_index}", label_visibility="collapsed")
        with f4:
            st.text_input("Instruction", placeholder="Quantity and instruction", key=f"meal_{day_number}_flex_inst_{item_index}", label_visibility="collapsed")
    if st.button("Add another flexible item", key=f"meal_add_flex_{day_number}", use_container_width=True):
        add_item("meal_flex", day_number, "flexible_item")
        st.rerun()
    b1, b2 = st.columns(2)
    with b1:
        if st.button("Copy Day 1 to all days", key=f"meal_copy_all_{day_number}", use_container_width=True):
            copy_day_1_all("meal", MEAL_SLOTS, "Meals")
            copy_day_1_all("meal_flex", ["flexible_item"], "Flexible add-ons")
    with b2:
        if st.button("Copy previous day", key=f"meal_copy_prev_{day_number}", use_container_width=True):
            copy_previous("meal", day_number, MEAL_SLOTS, "Meals")
            copy_previous("meal_flex", day_number, ["flexible_item"], "Flexible add-ons")
    st.markdown("</div>", unsafe_allow_html=True)

with exercise_tab:
    st.markdown("<div class='hm-box'>", unsafe_allow_html=True)
    st.markdown("<div class='hm-title'>Exercise Regime · Day 1 to Day 7</div><div class='hm-sub'>Exercise, Time, Intensity and Instruction stay constant. Add workout item creates extra exercise rows.</div>", unsafe_allow_html=True)
    day_number = day_selector("exercise", start_date)
    st.markdown(f"#### {day_label(start_date, day_number)}")
    rest_day = st.checkbox("Rest day / mobility-only day", key=f"exercise_rest_{day_number}")
    for slot in EXERCISE_SLOTS:
        st.markdown(f"<div class='hm-slot'>{slot}</div>", unsafe_allow_html=True)
        for item_index in range(1, get_count("exercise", day_number, slot) + 1):
            st.markdown("<div class='hm-head'>Exercise · Time · Intensity · Instruction</div>", unsafe_allow_html=True)
            ex_col, time_col, intensity_col, instr_col = st.columns([0.40, 0.18, 0.18, 0.24], gap="small")
            with ex_col:
                st.selectbox("Exercise", exercise_options, key=f"exercise_{day_number}_{slot}_exercise_{item_index}", label_visibility="collapsed", disabled=rest_day)
            with time_col:
                st.time_input("Time", value=dt.time(7, 0) if slot == "Morning" else dt.time(18, 0), key=f"exercise_{day_number}_{slot}_time_{item_index}", label_visibility="collapsed", disabled=rest_day)
            with intensity_col:
                st.selectbox("Intensity", INTENSITY_OPTIONS, key=f"exercise_{day_number}_{slot}_intensity_{item_index}", label_visibility="collapsed", disabled=rest_day)
            with instr_col:
                st.text_input("Instruction", placeholder="Instruction", key=f"exercise_{day_number}_{slot}_instruction_{item_index}", label_visibility="collapsed", disabled=rest_day)
        if st.button("Add workout item", key=f"exercise_{day_number}_{slot}_add_workout", use_container_width=True, disabled=rest_day):
            add_item("exercise", day_number, slot)
            st.rerun()
    b1, b2, b3 = st.columns(3)
    with b1:
        if st.button("Copy Day 1 to all days", key=f"exercise_copy_all_{day_number}", use_container_width=True):
            copy_day_1_all("exercise", EXERCISE_SLOTS, "Exercises")
    with b2:
        if st.button("Copy previous day", key=f"exercise_copy_prev_{day_number}", use_container_width=True):
            copy_previous("exercise", day_number, EXERCISE_SLOTS, "Exercises")
    with b3:
        if st.button("Add preferred-time slot", key=f"exercise_add_slot_{day_number}", use_container_width=True):
            add_item("exercise", day_number, "Preferred Time")
            st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

with supplement_tab:
    st.markdown("<div class='hm-box'>", unsafe_allow_html=True)
    st.markdown("<div class='hm-title'>Supplement Regime · Day 1 to Day 7</div><div class='hm-sub'>Supplement, Time, Dosage/Frequency and Instruction stay constant.</div>", unsafe_allow_html=True)
    active_supps = list_active_member_supplements(member_options.get(selected_member, {}).get("id", "")) if member_options else []
    supp_options = ["— Select supplement —"] + [f"{r.get('id')} — {clean(r.get('supplement_name')) or 'Supplement'} · {clean(r.get('dosage'))} · {clean(r.get('frequency'))}" for r in active_supps]
    if not active_supps:
        st.info("No active member supplements found. Mock-up still shows the override structure below.")
    day_number = day_selector("supplement", start_date)
    st.markdown(f"#### {day_label(start_date, day_number)}")
    for slot in SUPPLEMENT_SLOTS:
        st.markdown(f"<div class='hm-slot'>{slot}</div>", unsafe_allow_html=True)
        for item_index in range(1, get_count("supplement", day_number, slot) + 1):
            st.markdown("<div class='hm-head'>Supplement · Time · Dosage/Frequency · Instruction</div>", unsafe_allow_html=True)
            supp_col, time_col, dose_col, instr_col = st.columns([0.36, 0.16, 0.24, 0.24], gap="small")
            with supp_col:
                st.selectbox("Supplement", supp_options, key=f"supp_{day_number}_{slot}_supplement_{item_index}", label_visibility="collapsed")
            with time_col:
                st.time_input("Time", value=dt.time(8, 0), key=f"supp_{day_number}_{slot}_time_{item_index}", label_visibility="collapsed")
            with dose_col:
                d1, d2 = st.columns(2, gap="small")
                with d1:
                    st.text_input("Dosage", placeholder="400 mg", key=f"supp_{day_number}_{slot}_dose_{item_index}", label_visibility="collapsed")
                with d2:
                    st.selectbox("Frequency", FREQUENCY_OPTIONS, key=f"supp_{day_number}_{slot}_freq_{item_index}", label_visibility="collapsed")
            with instr_col:
                st.text_input("Instruction", placeholder="With food / after dinner", key=f"supp_{day_number}_{slot}_instruction_{item_index}", label_visibility="collapsed")
        if st.button("Add supplement item", key=f"supp_{day_number}_{slot}_add_item", use_container_width=True):
            add_item("supplement", day_number, slot)
            st.rerun()
    b1, b2, b3 = st.columns(3)
    with b1:
        if st.button("Copy active regimen", key=f"supp_copy_active_{day_number}", use_container_width=True):
            st.info("Active-regimen copy is active for mock-up review. Full data copy will be implemented in the functional sprint.")
    with b2:
        if st.button("Copy Day 1 to all days", key=f"supp_copy_all_{day_number}", use_container_width=True):
            copy_day_1_all("supplement", SUPPLEMENT_SLOTS, "Supplements")
    with b3:
        if st.button("Copy previous day", key=f"supp_copy_prev_{day_number}", use_container_width=True):
            copy_previous("supplement", day_number, SUPPLEMENT_SLOTS, "Supplements")
    st.markdown("</div>", unsafe_allow_html=True)

with preview_tab:
    st.markdown("<div class='hm-box'>", unsafe_allow_html=True)
    st.markdown("<div class='hm-title'>Preview & End-to-End Flow Review</div><div class='hm-sub'>Objective: freeze the data contract before implementation so Admin, Web Member and Flutter Member use the same weekly recommendation profile.</div>", unsafe_allow_html=True)
    st.markdown("<div class='hm-preview'><b>This is not a member-facing screen.</b><br>It confirms what will be saved, what will be published, and how the same active weekly cycle will be consumed by Web Today’s Journey and Flutter My Recommendations.</div>", unsafe_allow_html=True)
    st.markdown(f"""
<div class='hm-preview'>
<b>Recommendation Profile:</b> {profile_name}<br>
<b>Clone Source:</b> {clone_from}<br>
<b>Assigned Member:</b> {selected_member if member_options else 'NA'}<br>
<b>Start Date:</b> {start_date.isoformat()}<br>
<b>Cycle:</b> Weekly cyclical until replaced or stopped<br>
<b>Profile Tags:</b> {region} · {age_band} · {diet_type} · {', '.join(health_concern) if health_concern else 'No concern selected'}
</div>
""", unsafe_allow_html=True)
    st.code("""recommendation_profile
  profile_id, profile_name, clone_from_profile_id, version, tags
weekly_meal_structure
  day_1 ... day_7
  fixed_slots + flexible_add_on_slots
  meal_items: recipe, portion, instruction
weekly_exercise_regime
  day_1 ... day_7
  workout_items: exercise, time, intensity, instruction
weekly_supplement_regime
  day_1 ... day_7
  supplement_items: supplement, time, dosage, frequency, instruction
member_consumption
  My Recommendations = full active weekly profile
  Today’s Journey = calculated current day slice from active cycle""", language="text")
    st.checkbox("Admin can create/clone Recommendation Profile without replacing old profile", key="mock_check_1")
    st.checkbox("Meal structure captures fixed meals and flexible timed in-between items", key="mock_check_2")
    st.checkbox("Exercise regime uses exercise/time/intensity/instruction and supports multiple workout items", key="mock_check_3")
    st.checkbox("Supplement regime uses supplement/time/dosage/frequency/instruction with override", key="mock_check_4")
    st.checkbox("Published snapshot can feed both Web Today’s Journey and Flutter My Recommendations", key="mock_check_5")
    st.checkbox("No data loss between admin, web member and Flutter member contracts", key="mock_check_6")
    st.markdown("</div>", unsafe_allow_html=True)

render_page_nav("Recommendation Profile Builder Mock-up", back_page="pages/10_Admin_Dashboard.py", dashboard_page="pages/10_Admin_Dashboard.py", show_evaluation=False, show_dashboard=True, location="bottom")
render_back_to_top()
