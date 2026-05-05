import streamlit as st
from components.guards import require_member
from components.ui_common import inject_global_styles, apply_luxe_theme, topbar, card_start, card_end, utility_logout_bar
from components.db import save_daily_log, get_daily_logs
from components.flash import set_system_message, render_system_message

st.set_page_config(page_title="Daily Log", page_icon="💚", layout="wide", initial_sidebar_state="collapsed")
inject_global_styles(); apply_luxe_theme(); require_member(); utility_logout_bar()

user_id = st.session_state["user_id"]
topbar("Daily Log", "Track food, water, sleep, and exercise.", "Member tracker")
render_system_message()

card_start()
food_log = st.text_area("Food log")
water = st.number_input("Water intake (ml)", min_value=0, step=100)
sleep = st.number_input("Sleep hours", min_value=0.0, max_value=14.0, step=0.5)
exercise_done = st.selectbox("Exercise done?", ["Select", "Yes", "No"])
exercise_notes = st.text_area("Exercise / wellness notes")

if st.button("Save Daily Log", type="primary"):
    if not food_log.strip() and water == 0 and sleep == 0 and exercise_done == "Select" and not exercise_notes.strip():
        set_system_message("Please enter at least one daily log detail before saving.", "error")
        st.rerun()
    else:
        save_daily_log(user_id, {
            "food_log": food_log,
            "water_ml": water,
            "sleep_hours": sleep,
            "exercise_done": exercise_done,
            "exercise_notes": exercise_notes,
        })
        set_system_message("Daily log saved successfully.", "success")
        st.rerun()
card_end()

card_start()
st.subheader("Recent Logs")
logs = get_daily_logs(user_id)
if not logs:
    st.info("No daily logs saved yet.")
else:
    for item in reversed(logs[-10:]):
        st.markdown(f"**{item.get('timestamp','')}**")
        st.write(f"Food: {item.get('food_log','')}")
        st.write(f"Water: {item.get('water_ml','')} ml | Sleep: {item.get('sleep_hours','')} hrs | Exercise: {item.get('exercise_done','')}")
        if item.get("exercise_notes"):
            st.write(f"Notes: {item.get('exercise_notes')}")
        st.divider()
card_end()

if st.button("Back to Home"):
    st.switch_page("pages/02_Member_Home.py")