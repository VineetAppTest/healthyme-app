import streamlit as st
from datetime import date, time
from components.guards import require_member
from components.ui_common import inject_global_styles, apply_luxe_theme, topbar, card_start, card_end, utility_logout_bar, render_build_text_v12
from components.db import save_daily_food_journal_entry, get_daily_logs, get_daily_log_supervision_notes
from components.flash import set_system_message, render_system_message

st.set_page_config(page_title="Daily Food Journal", page_icon="💚", layout="wide", initial_sidebar_state="collapsed")
inject_global_styles(); apply_luxe_theme(); require_member(); utility_logout_bar()

user_id = st.session_state["user_id"]
topbar("Daily Food Journal", "Track meals, water, mood, activity, bowel movement and notes in the client-approved format.", "Member tracker")
render_system_message()

SAMPLE_ROWS = [
    {
        "time": "10:00 - 10:30 AM",
        "meal_type": "Breakfast",
        "food": "Boiled eggs / omelet / moong dal chilla / poha",
        "water": "",
        "portion_size": "2 eggs / 2 chilla / 1 bowl poha",
        "mood_energy": "Fresh",
        "physical_activity": "1 PM - 2 PM",
        "poop": "2-3 times / felt relieved",
        "notes": "Mention exact items and water intake where applicable.",
    },
    {
        "time": "2:30 - 2:45 PM",
        "meal_type": "Lunch",
        "food": "Dal + rice / roti + salad + curd + sabzi",
        "water": "",
        "portion_size": "100 ml rice + 100 ml dal",
        "mood_energy": "Energetic",
        "physical_activity": "",
        "poop": "",
        "notes": "",
    },
    {
        "time": "5:00 - 5:30 PM",
        "meal_type": "Evening Snack",
        "food": "Half cup tea with snack",
        "water": "",
        "portion_size": "",
        "mood_energy": "Okay",
        "physical_activity": "",
        "poop": "",
        "notes": "",
    },
    {
        "time": "7:30 - 8:00 PM",
        "meal_type": "Dinner",
        "food": "Soup / light dinner",
        "water": "",
        "portion_size": "1 big bowl",
        "mood_energy": "Energetic",
        "physical_activity": "",
        "poop": "",
        "notes": "",
    },
]

with st.expander("Reference format from sample journal", expanded=False):
    st.caption("Use this as a guide. Enter your actual values below.")
    st.dataframe(SAMPLE_ROWS, use_container_width=True, hide_index=True)

notes = get_daily_log_supervision_notes(user_id, limit=5)
if notes:
    card_start()
    st.subheader("Admin supervision notes")
    for n in notes:
        st.markdown(
            f"""
            <div class='info-banner'>
              <b>{n.get('ts','')}</b><br>
              {n.get('note','')}
            </div>
            """,
            unsafe_allow_html=True,
        )
    card_end()

card_start()
st.subheader("Add food journal entry")
st.caption("Laptop-friendly and mobile-friendly structured entry based on the provided Food Journal format.")

c1, c2, c3 = st.columns([1, 1, 1])
with c1:
    log_date = st.date_input("Date", value=date.today())
with c2:
    time_text = st.text_input("Time", placeholder="Example: 10:00 - 10:30 AM")
with c3:
    meal_type = st.selectbox("Meal Type", ["Select", "Early Morning", "Breakfast", "Mid Morning", "Lunch", "Evening Snack", "Dinner", "Bedtime", "Other"])

food = st.text_area("Food", placeholder="Example: Boiled egg with toast and tea")
c4, c5 = st.columns(2)
with c4:
    water = st.text_input("Water", placeholder="Example: 2 ltr / coconut water / juice")
with c5:
    portion_size = st.text_input("Portion Size", placeholder="Example: 1 bowl / 250 ml / 2 eggs")

c6, c7 = st.columns(2)
with c6:
    mood_energy = st.text_input("Mood / Energy", placeholder="Example: Normal / Fresh / Heavy / Full")
with c7:
    physical_activity = st.text_input("Physical activity - time and duration", placeholder="Example: Strength training 1 PM - 2 PM")

poop = st.text_input("Poop rounds and feeling after poop", placeholder="Example: Twice / felt relieved")
entry_notes = st.text_area("Notes", placeholder="Anything specific for admin to review")

if st.button("Save Food Journal Entry", type="primary", use_container_width=True):
    if meal_type == "Select" and not food.strip() and not water.strip() and not physical_activity.strip() and not poop.strip():
        set_system_message("Please enter at least one food journal detail before saving.", "error")
        st.rerun()
    else:
        save_daily_food_journal_entry(user_id, {
            "date": str(log_date),
            "time": time_text.strip(),
            "meal_type": "" if meal_type == "Select" else meal_type,
            "food": food.strip(),
            "water": water.strip(),
            "portion_size": portion_size.strip(),
            "mood_energy": mood_energy.strip(),
            "physical_activity": physical_activity.strip(),
            "poop": poop.strip(),
            "notes": entry_notes.strip(),
        })
        set_system_message("Food journal entry saved.", "success")
        st.rerun()
card_end()

card_start()
st.subheader("Recent food journal entries")
logs = get_daily_logs(user_id)
food_logs = [x for x in logs if x.get("log_type") == "food_journal" or any(k in x for k in ["meal_type", "food", "portion_size", "mood_energy", "physical_activity", "poop"])]
if not food_logs:
    st.info("No food journal entries saved yet.")
else:
    display_rows = []
    for item in reversed(food_logs[-20:]):
        display_rows.append({
            "Date": item.get("date", ""),
            "Time": item.get("time", item.get("timestamp", "")),
            "Meal Type": item.get("meal_type", ""),
            "Food": item.get("food", item.get("food_log", "")),
            "Water": item.get("water", item.get("water_ml", "")),
            "Portion Size": item.get("portion_size", ""),
            "Mood/Energy": item.get("mood_energy", ""),
            "Physical Activity": item.get("physical_activity", item.get("exercise_notes", "")),
            "Poop": item.get("poop", ""),
            "Notes": item.get("notes", ""),
        })
    st.dataframe(display_rows, use_container_width=True, hide_index=True)
card_end()

if st.button("Back to Home", use_container_width=True):
    st.switch_page("pages/02_Member_Home.py")
