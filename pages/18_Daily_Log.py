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
    ensure_other_meal_section,
)
from components.flash import set_system_message, render_system_message

st.set_page_config(page_title="Daily Food Journal", page_icon="💚", layout="wide", initial_sidebar_state="collapsed")
inject_global_styles(); apply_luxe_theme(); require_member(); utility_logout_bar()

st.markdown(
    """
    <style>
    .hm-compact-section-note {
        margin: .15rem 0 .45rem 0;
        color: #64748B;
        font-size: .82rem;
        line-height: 1.25;
    }
    .hm-meal-title {
        margin-top: .25rem;
        margin-bottom: .15rem;
        font-size: 1.08rem;
        font-weight: 850;
        color: #064E3B;
    }
    .hm-reference-shell {
        border: 1px solid #E7D8BE;
        border-radius: 18px;
        padding: .75rem .85rem;
        background: #FFFDF8;
        margin-top: .75rem;
    }
    .hm-reference-title {
        font-size: .92rem;
        font-weight: 850;
        color: #064E3B;
        margin-bottom: .15rem;
    }
    div[data-testid="stVerticalBlock"] > div:has(.hm-meal-title) {
        gap: .2rem !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

user_id = st.session_state["user_id"]
topbar("Daily Food Journal", "Save meals progressively through the day, or complete the full day together.", "Member tracker")
render_system_message()

def meal_has_data(meal):
    return any((meal or {}).get(x) for x in ["time", "food", "water", "portion_size", "mood_energy"])

def current_widget_payload(section_key, section_label):
    return {
        "label": section_label,
        "time": st.session_state.get(f"{section_key}_time", "").strip(),
        "food": st.session_state.get(f"{section_key}_food", "").strip(),
        "water": st.session_state.get(f"{section_key}_water", "").strip(),
        "portion_size": st.session_state.get(f"{section_key}_portion", "").strip(),
        "mood_energy": st.session_state.get(f"{section_key}_mood", "").strip(),
    }

def saved_payload_for(existing_meals, section_key, section_label):
    prior = existing_meals.get(section_key, {}) if existing_meals else {}
    return {
        "label": prior.get("label", section_label),
        "time": prior.get("time", ""),
        "food": prior.get("food", ""),
        "water": prior.get("water", ""),
        "portion_size": prior.get("portion_size", ""),
        "mood_energy": prior.get("mood_energy", ""),
    }

def is_dirty(existing_meals, section_key, section_label):
    if f"{section_key}_food" not in st.session_state:
        return False
    cur = current_widget_payload(section_key, section_label)
    saved = saved_payload_for(existing_meals, section_key, section_label)
    return any(cur.get(k, "") != saved.get(k, "") for k in ["time", "food", "water", "portion_size", "mood_energy"])

# Make sure Other exists even for old repositories.
ensure_other_meal_section()
meal_repo = get_meal_type_repository()

base_sections = [(r["key"], r["label"]) for r in meal_repo if r.get("key") != "other"]
other_enabled = True

if "daily_log_other_count" not in st.session_state:
    st.session_state["daily_log_other_count"] = 1

log_date = st.date_input("Food journal date", value=date.today())
existing = get_daily_food_journal_day(user_id, str(log_date))
existing_meals = existing.get("meals", {}) if existing else {}

existing_other_nums = []
for key in existing_meals.keys():
    if key.startswith("other_"):
        try:
            existing_other_nums.append(int(key.split("_")[1]))
        except Exception:
            pass
if existing_other_nums:
    st.session_state["daily_log_other_count"] = max(st.session_state.get("daily_log_other_count", 1), max(existing_other_nums))

meal_sections = list(base_sections)
for idx in range(1, st.session_state.get("daily_log_other_count", 1) + 1):
    meal_sections.append((f"other_{idx}", f"Other {idx}"))

if not meal_sections:
    st.warning("No meal sections are currently active. Please contact admin.")
    st.stop()

if "active_daily_meal_section" not in st.session_state or st.session_state["active_daily_meal_section"] not in [x[0] for x in meal_sections]:
    st.session_state["active_daily_meal_section"] = meal_sections[0][0]

date_notes = get_daily_log_supervision_notes(user_id, limit=10, log_date=str(log_date))
if date_notes:
    card_start()
    st.subheader(f"Admin supervision notes for {log_date}")
    for n in date_notes:
        st.markdown(f"<div class='info-banner'><b>{n.get('ts','')}</b><br>{n.get('note','')}</div>", unsafe_allow_html=True)
    card_end()

card_start()
st.subheader("Meal sections")
st.markdown("<div class='hm-compact-section-note'>Tap a meal to open it. Save the current meal before moving to another section.</div>", unsafe_allow_html=True)

active_key = st.session_state["active_daily_meal_section"]
active_label = next((label for key, label in meal_sections if key == active_key), meal_sections[0][1])

# Compact meal selector with reduced header/footer space.
max_cols = 4 if len(meal_sections) >= 4 else len(meal_sections)
cols = st.columns(max_cols)
for idx, (key, label) in enumerate(meal_sections):
    with cols[idx % max_cols]:
        saved = meal_has_data(existing_meals.get(key, {}))
        short_label = f"{'● ' if key == active_key else ''}{label}{' ✓' if saved else ''}"
        if st.button(short_label, key=f"section_btn_{key}", use_container_width=True):
            if key != active_key and is_dirty(existing_meals, active_key, active_label):
                st.warning(f"Please save the section ({active_label}) before moving to next section.")
            else:
                st.session_state["active_daily_meal_section"] = key
                st.rerun()

# Other is now very visible directly below the buttons.
add_cols = st.columns([1, 2])
with add_cols[0]:
    if st.button("+ Other", use_container_width=True, help="Add another undefined eating time such as Other 2, Other 3, etc."):
        if is_dirty(existing_meals, active_key, active_label):
            st.warning(f"Please save the section ({active_label}) before adding another Other section.")
        else:
            st.session_state["daily_log_other_count"] = st.session_state.get("daily_log_other_count", 1) + 1
            st.session_state["active_daily_meal_section"] = f"other_{st.session_state['daily_log_other_count']}"
            st.rerun()
with add_cols[1]:
    st.caption("Use Other for undefined eating times beyond the standard meals.")

st.markdown(f"<div class='hm-meal-title'>{active_label}</div>", unsafe_allow_html=True)
prior = existing_meals.get(active_key, {}) if existing_meals else {}

c1, c2 = st.columns([1, 1])
with c1:
    time_text = st.text_input("Time", value=prior.get("time", ""), key=f"{active_key}_time", placeholder="Example: 10:00 - 10:30 AM")
with c2:
    water = st.text_input("Water", value=prior.get("water", ""), key=f"{active_key}_water", placeholder="Example: 250 ml / 2 glasses")

food = st.text_area("Food", value=prior.get("food", ""), key=f"{active_key}_food", placeholder=f"What did you have for {active_label.lower()}?", height=85)

c3, c4 = st.columns([1, 1])
with c3:
    portion = st.text_input("Portion Size", value=prior.get("portion_size", ""), key=f"{active_key}_portion", placeholder="Example: 1 bowl / 2 rotis / 250 ml")
with c4:
    mood = st.text_input("Mood / Energy", value=prior.get("mood_energy", ""), key=f"{active_key}_mood", placeholder="Example: fresh / heavy / energetic")

active_payload = current_widget_payload(active_key, active_label)
meal_dirty = is_dirty(existing_meals, active_key, active_label)

c_save, c_status = st.columns([1, 1])
with c_save:
    if st.button(f"Save {active_label}", type="primary", use_container_width=True):
        save_daily_food_journal_meal(user_id, str(log_date), active_key, active_payload)
        set_system_message(f"{active_label} saved for {log_date}.", "success")
        st.rerun()
with c_status:
    if meal_dirty:
        st.warning(f"Unsaved changes in {active_label}.")
    elif meal_has_data(prior):
        st.success(f"{active_label} saved.")
    else:
        st.caption("No saved entry yet.")
card_end()

card_start()
st.subheader("Full-day details")
d1, d2 = st.columns(2)
with d1:
    physical_activity = st.text_area(
        "Physical activity - time of day and duration",
        value=existing.get("physical_activity", ""),
        placeholder="Example: Walk 30 mins at 7 AM / strength training 1 PM - 2 PM",
        height=90,
    )
with d2:
    poop = st.text_area(
        "Poop rounds and feeling after poop",
        value=existing.get("poop", ""),
        placeholder="Example: 2 times, felt relieved / constipated / loose stool",
        height=90,
    )
day_notes = st.text_area("Overall notes for the day", value=existing.get("notes", ""), placeholder="Any cravings, bloating, missed meals, late meals, etc.", height=85)

c_save_1, c_save_2 = st.columns(2)
with c_save_1:
    if st.button("Save Day Details Only", use_container_width=True):
        save_daily_food_journal_day_details(user_id, str(log_date), physical_activity.strip(), poop.strip(), day_notes.strip())
        set_system_message("Day details saved.", "success")
        st.rerun()
with c_save_2:
    if st.button("Save Full-Day Journal", type="primary", use_container_width=True):
        merged_meals = dict(existing_meals or {})
        merged_meals[active_key] = active_payload
        payload = {
            "date": str(log_date),
            "meals": merged_meals,
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

# Reference moved to bottom, with more aesthetic and compact expander.
SAMPLE_ROWS = [
    {"Time": "10:00 - 10:30 AM", "Meal Type": "Breakfast", "Food": "Boiled eggs / omelet / moong dal chilla / poha", "Water": "", "Portion Size": "2 eggs / 2 chilla / 1 bowl poha", "Mood/Energy": "Fresh", "Activity": "1 PM - 2 PM", "Poop": "2-3 times / felt relieved", "Notes": "Mention exact items."},
    {"Time": "2:30 - 2:45 PM", "Meal Type": "Lunch", "Food": "Dal + rice / roti + salad + curd + sabzi", "Water": "", "Portion Size": "100 ml rice + 100 ml dal", "Mood/Energy": "Energetic", "Activity": "", "Poop": "", "Notes": ""},
    {"Time": "5:00 - 5:30 PM", "Meal Type": "Evening Snack", "Food": "Half cup tea with snack", "Water": "", "Portion Size": "", "Mood/Energy": "Okay", "Activity": "", "Poop": "", "Notes": ""},
    {"Time": "7:30 - 8:00 PM", "Meal Type": "Dinner", "Food": "Soup / light dinner", "Water": "", "Portion Size": "1 big bowl", "Mood/Energy": "Energetic", "Activity": "", "Poop": "", "Notes": ""},
]

st.markdown("<div class='hm-reference-shell'><div class='hm-reference-title'>Reference format from sample journal</div><div class='hm-compact-section-note'>Use only when needed.</div>", unsafe_allow_html=True)
if "show_daily_reference_sample" not in st.session_state:
    st.session_state["show_daily_reference_sample"] = False
if st.button("Show / Hide sample journal format", use_container_width=True):
    st.session_state["show_daily_reference_sample"] = not st.session_state["show_daily_reference_sample"]
if st.session_state["show_daily_reference_sample"]:
    st.dataframe(SAMPLE_ROWS, use_container_width=True, hide_index=True)
st.markdown("</div>", unsafe_allow_html=True)

if st.button("Back to Home", use_container_width=True):
    st.switch_page("pages/02_Member_Home.py")
