import streamlit as st
from datetime import date
from components.guards import require_member
from components.ui_common import inject_global_styles, apply_luxe_theme, topbar, card_start, card_end, utility_logout_bar
from components.db import (
    save_daily_food_journal_day,
    save_daily_food_journal_meal,
    save_daily_food_journal_day_details,
    get_daily_food_journal_day,
    get_daily_food_journal_days,
    get_daily_log_supervision_notes,
    get_meal_type_repository,
)
from components.flash import set_system_message, render_system_message

st.set_page_config(page_title="Daily Food Journal", page_icon="💚", layout="wide", initial_sidebar_state="collapsed")
inject_global_styles(); apply_luxe_theme(); require_member(); utility_logout_bar()

user_id = st.session_state["user_id"]
topbar("Daily Food Journal", "Fill the whole day at once or save each meal section progressively.", "Member tracker")
render_system_message()

meal_repo = get_meal_type_repository()
MEAL_GROUPS = [(r["key"], r["label"]) for r in meal_repo]

SAMPLE_ROWS = [
    {"Time": "10:00 - 10:30 AM", "Meal Type": "Breakfast", "Food": "Boiled eggs / omelet / moong dal chilla / poha", "Water": "", "Portion Size": "2 eggs / 2 chilla / 1 bowl poha", "Mood/Energy": "Fresh", "Activity": "1 PM - 2 PM", "Poop": "2-3 times / felt relieved", "Notes": "Mention exact items."},
    {"Time": "2:30 - 2:45 PM", "Meal Type": "Lunch", "Food": "Dal + rice / roti + salad + curd + sabzi", "Water": "", "Portion Size": "100 ml rice + 100 ml dal", "Mood/Energy": "Energetic", "Activity": "", "Poop": "", "Notes": ""},
    {"Time": "5:00 - 5:30 PM", "Meal Type": "Evening Snack", "Food": "Half cup tea with snack", "Water": "", "Portion Size": "", "Mood/Energy": "Okay", "Activity": "", "Poop": "", "Notes": ""},
    {"Time": "7:30 - 8:00 PM", "Meal Type": "Dinner", "Food": "Soup / light dinner", "Water": "", "Portion Size": "1 big bowl", "Mood/Energy": "Energetic", "Activity": "", "Poop": "", "Notes": ""},
]

with st.expander("Reference format from sample journal", expanded=False):
    st.caption("Use this as a guide. Actual meal sections are controlled by admin.")
    st.dataframe(SAMPLE_ROWS, use_container_width=True, hide_index=True)

if not MEAL_GROUPS:
    st.warning("No meal sections are currently active. Please contact admin.")
    st.stop()

log_date = st.date_input("Food journal date", value=date.today())
existing = get_daily_food_journal_day(user_id, str(log_date))
existing_meals = existing.get("meals", {}) if existing else {}

date_notes = get_daily_log_supervision_notes(user_id, limit=10, log_date=str(log_date))
if date_notes:
    card_start()
    st.subheader(f"Admin supervision notes for {log_date}")
    for n in date_notes:
        st.markdown(f"<div class='info-banner'><b>{n.get('ts','')}</b><br>{n.get('note','')}</div>", unsafe_allow_html=True)
    card_end()

card_start()
st.subheader("Food journal by meal")
st.caption("You can save one meal now and return later, or fill multiple meals and use Save Full-Day Journal.")

meals = {}
for key, label in MEAL_GROUPS:
    prior = existing_meals.get(key, {}) if existing_meals else {}
    meal_has_data = any(prior.get(x) for x in ["time", "food", "water", "portion_size", "mood_energy"])
    with st.expander(f"{label}{' ✓' if meal_has_data else ''}", expanded=not meal_has_data and label in ["Breakfast", "Lunch", "Dinner"]):
        c1, c2 = st.columns([1, 1])
        with c1:
            time_text = st.text_input("Time", value=prior.get("time", ""), key=f"{key}_time", placeholder="Example: 10:00 - 10:30 AM")
        with c2:
            water = st.text_input("Water", value=prior.get("water", ""), key=f"{key}_water", placeholder="Example: 250 ml / 2 glasses")
        food = st.text_area("Food", value=prior.get("food", ""), key=f"{key}_food", placeholder=f"What did you have for {label.lower()}?")
        c3, c4 = st.columns([1, 1])
        with c3:
            portion = st.text_input("Portion Size", value=prior.get("portion_size", ""), key=f"{key}_portion", placeholder="Example: 1 bowl / 2 rotis / 250 ml")
        with c4:
            mood = st.text_input("Mood / Energy", value=prior.get("mood_energy", ""), key=f"{key}_mood", placeholder="Example: fresh / heavy / energetic")

        meal_payload = {
            "label": label,
            "time": time_text.strip(),
            "food": food.strip(),
            "water": water.strip(),
            "portion_size": portion.strip(),
            "mood_energy": mood.strip(),
        }
        meals[key] = meal_payload

        if st.button(f"Save {label}", key=f"save_{key}", use_container_width=True):
            save_daily_food_journal_meal(user_id, str(log_date), key, meal_payload)
            set_system_message(f"{label} saved for {log_date}.", "success")
            st.rerun()

st.markdown("#### Full-day details")
d1, d2 = st.columns(2)
with d1:
    physical_activity = st.text_area(
        "Physical activity - time of day and duration",
        value=existing.get("physical_activity", ""),
        placeholder="Example: Walk 30 mins at 7 AM / strength training 1 PM - 2 PM",
    )
with d2:
    poop = st.text_area(
        "Poop rounds and feeling after poop",
        value=existing.get("poop", ""),
        placeholder="Example: 2 times, felt relieved / constipated / loose stool",
    )
day_notes = st.text_area("Overall notes for the day", value=existing.get("notes", ""), placeholder="Any cravings, bloating, missed meals, late meals, etc.")

c_save_1, c_save_2 = st.columns(2)
with c_save_1:
    if st.button("Save Day Details Only", use_container_width=True):
        save_daily_food_journal_day_details(user_id, str(log_date), physical_activity.strip(), poop.strip(), day_notes.strip())
        set_system_message("Day details saved.", "success")
        st.rerun()
with c_save_2:
    if st.button("Save Full-Day Journal", type="primary", use_container_width=True):
        filled = any(v.get("food") or v.get("water") or v.get("time") or v.get("portion_size") or v.get("mood_energy") for v in meals.values())
        if not filled and not physical_activity.strip() and not poop.strip() and not day_notes.strip():
            set_system_message("Please enter at least one detail before saving.", "error")
            st.rerun()
        payload = {
            "date": str(log_date),
            "meals": meals,
            "physical_activity": physical_activity.strip(),
            "poop": poop.strip(),
            "notes": day_notes.strip(),
        }
        save_daily_food_journal_day(user_id, str(log_date), payload)
        set_system_message("Full-day food journal saved.", "success")
        st.rerun()
card_end()

card_start()
st.subheader("Recent saved days")
days = get_daily_food_journal_days(user_id)
if not days:
    st.info("No food journal days saved yet.")
else:
    rows = []
    for day in days[:14]:
        meal_summary = []
        for _k, meal in (day.get("meals", {}) or {}).items():
            if meal.get("food"):
                meal_summary.append(f"{meal.get('label','')}: {meal.get('food','')}")
        rows.append({
            "Date": day.get("date", ""),
            "Meals Logged": len(meal_summary),
            "Food Summary": " | ".join(meal_summary[:4]),
            "Activity": day.get("physical_activity", ""),
            "Poop": day.get("poop", ""),
            "Notes": day.get("notes", ""),
        })
    st.dataframe(rows, use_container_width=True, hide_index=True)
card_end()

if st.button("Back to Home", use_container_width=True):
    st.switch_page("pages/02_Member_Home.py")
