import streamlit as st
import html
from datetime import date
from components.guards import require_member
from components.ui_common import inject_global_styles, apply_luxe_theme, topbar, card_start, card_end, utility_logout_bar, format_local_ts, render_back_to_top, compact_topbar
from components.db import (
    save_daily_food_journal_day,
    save_daily_food_journal_meal,
    save_daily_food_journal_day_details,
    get_daily_food_journal_day,
    get_daily_food_journal_days,
    get_daily_log_supervision_notes,
    get_meal_type_repository,
    ensure_other_meal_section,
    get_member_archived_messages,
    auto_archive_expired_nutritionist_messages,
    get_daily_log_notes_by_date,
    get_latest_daily_log_note_for_date,
)
from components.flash import set_system_message, render_system_message

st.set_page_config(page_title="Daily Food Journal", page_icon="💚", layout="wide", initial_sidebar_state="collapsed")
inject_global_styles(); apply_luxe_theme(); require_member(); utility_logout_bar(); render_back_to_top()

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
compact_topbar("Daily Food Journal", "Save meals progressively through the day, or complete the full day together.", "Member tracker")
render_system_message()
auto_archive_expired_nutritionist_messages(user_id)

def meal_has_data(meal):
    return any((meal or {}).get(x) for x in ["time", "food", "portion_size", "mood_energy"])

def current_widget_payload(section_key, section_label):
    return {
        "label": section_label,
        "time": st.session_state.get(f"{section_key}_time", "").strip(),
        "food": st.session_state.get(f"{section_key}_food", "").strip(),
                "portion_size": st.session_state.get(f"{section_key}_portion", "").strip(),
        "mood_energy": st.session_state.get(f"{section_key}_mood", "").strip(),
    }

def saved_payload_for(existing_meals, section_key, section_label):
    prior = existing_meals.get(section_key, {}) if existing_meals else {}
    return {
        "label": prior.get("label", section_label),
        "time": prior.get("time", ""),
        "food": prior.get("food", ""),
                "portion_size": prior.get("portion_size", ""),
        "mood_energy": prior.get("mood_energy", ""),
    }

def is_dirty(existing_meals, section_key, section_label):
    if f"{section_key}_food" not in st.session_state:
        return False
    cur = current_widget_payload(section_key, section_label)
    saved = saved_payload_for(existing_meals, section_key, section_label)
    return any(cur.get(k, "") != saved.get(k, "") for k in ["time", "food", "portion_size", "mood_energy"])

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

time_text = st.text_input("Time", value=prior.get("time", ""), key=f"{active_key}_time", placeholder="Example: 10:00 - 10:30 AM")

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
water_options = ['Select', '0 Litres', '0.5 Litres', '1 Litre', '1.5 Litres', '2 Litres', '2.5 Litres', '3 Litres', '3.5 Litres', '4 Litres', '4.5 Litres', '5 Litres', '5.5 Litres', '6 Litres', '6.5 Litres', '7 Litres', '7.5 Litres', '8 Litres', '8.5 Litres', '9 Litres', '9.5 Litres', '10 Litres']
existing_water = existing.get("water_litres", "Select") or "Select"
water_index = water_options.index(existing_water) if existing_water in water_options else 0
water_litres = st.selectbox("Water intake for the full day", water_options, index=water_index)
left_col, right_col = st.columns(2)
with left_col:
    physical_activity = st.text_area(
        "Physical activity - time of day and duration",
        value=existing.get("physical_activity", ""),
        placeholder="Example: Walk 30 mins at 7 AM / strength training 1 PM - 2 PM",
        height=90,
    )
    feeling_after_poop = st.text_area(
        "Feeling after poop",
        value=existing.get("feeling_after_poop", ""),
        placeholder="Example: relieved / constipated / bloated / loose stool / incomplete",
        height=160,
    )

with right_col:
    poop_options = ["Select"] + list(range(1, 10))
    existing_poop_rounds = existing.get("poop_rounds", "Select") or "Select"
    if str(existing_poop_rounds).isdigit():
        existing_poop_rounds = int(existing_poop_rounds)
    poop_round_index = poop_options.index(existing_poop_rounds) if existing_poop_rounds in poop_options else 0
    poop_rounds = st.selectbox("Poop rounds", poop_options, index=poop_round_index)

    poop_timings = []
    existing_timings = existing.get("poop_timings", []) or []
    if poop_rounds != "Select":
        st.caption("Record timing for each poop round.")
        timing_cols = st.columns(3)
        for idx in range(int(poop_rounds)):
            default_timing = existing_timings[idx] if idx < len(existing_timings) else ""
            with timing_cols[idx % 3]:
                poop_timings.append(
                    st.text_input(
                        f"Poop timing {idx + 1}",
                        value=default_timing,
                        key=f"poop_timing_{idx + 1}",
                        placeholder="Example: 7:30 AM",
                    )
                )
poop = ""
day_notes = st.text_area("Overall notes for the day", value=existing.get("notes", ""), placeholder="Any cravings, bloating, missed meals, late meals, etc.", height=85)

c_save_1, c_save_2 = st.columns(2)
with c_save_1:
    if st.button("Save Day Details Only", use_container_width=True):
        save_daily_food_journal_day_details(user_id, str(log_date), physical_activity.strip(), poop, day_notes.strip(), water_litres, poop_rounds, poop_timings, feeling_after_poop.strip())
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
            "poop_rounds": poop_rounds,
            "poop_timings": [x.strip() for x in poop_timings],
            "feeling_after_poop": feeling_after_poop.strip(),
            "poop": (
                (f"{poop_rounds} round(s)" if poop_rounds != "Select" else "")
                + (f" at {', '.join([x.strip() for x in poop_timings if x.strip()])}" if poop_rounds != "Select" and any(x.strip() for x in poop_timings) else "")
                + (f" / {feeling_after_poop.strip()}" if feeling_after_poop.strip() else "")
            ),
            "notes": day_notes.strip(),
            "water_litres": water_litres,
        }
        save_daily_food_journal_day(user_id, str(log_date), payload)
        set_system_message("Full-day food journal saved.", "success")
        st.rerun()
card_end()

card_start()
st.subheader("Recent saved days")
st.markdown(
    "<div class='hm-table-note'>View your recently saved day entries and the latest note from your nutritionist.</div>",
    unsafe_allow_html=True,
)
days = get_daily_food_journal_days(user_id)
if not days:
    st.info("No food journal days saved yet.")
else:
    active_meal_count = len(MEAL_GROUPS) if "MEAL_GROUPS" in globals() else 0
    if active_meal_count <= 0:
        active_meal_count = 1

    st.markdown(
        """
        <div class='hm-rsd-card'>
          <div class='hm-rsd-header'>
            <div>Date</div>
            <div>Meals Logged</div>
            <div>Water</div>
            <div>Notes</div>
            <div>Nutritionist Notes</div>
            <div>Action</div>
          </div>
        """,
        unsafe_allow_html=True,
    )

    note_dates = []
    for day in days[:14]:
        day_date = day.get("date", "")
        meal_summary = []
        for _k, meal in (day.get("meals", {}) or {}).items():
            if meal.get("food"):
                meal_summary.append(f"{meal.get('label','')}: {meal.get('food','')}")
        meals_logged = len(meal_summary)
        meal_progress = f"{meals_logged}/{active_meal_count}"

        latest_note = get_latest_daily_log_note_for_date(user_id, day_date)
        latest_note_text = "—"
        has_notes = False
        if latest_note:
            has_notes = True
            note_dates.append(day_date)
            latest_note_text = f"{format_local_ts(latest_note.get('ts',''))} — {latest_note.get('note','')}"

        date_display = html.escape(str(day_date or "—"))
        meal_display = html.escape(meal_progress)
        water_display = html.escape(str(day.get("water_litres") or "—"))
        notes_display = html.escape(str(day.get("notes") or "—"))
        nutritionist_display = html.escape(latest_note_text)

        st.markdown(
            f"""
            <div class='hm-rsd-row'>
              <div class='hm-rsd-date'>{date_display}</div>
              <div><span class='hm-rsd-pill'>{meal_display}</span></div>
              <div>{water_display}</div>
              <div>{notes_display}</div>
              <div class='hm-rsd-note'>{nutritionist_display}</div>
              <div class='hm-rsd-action-slot'></div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        action_cols = st.columns([5, 1])
        with action_cols[1]:
            if st.button("View history", key=f"rsd_history_{day_date}", use_container_width=True, disabled=not has_notes):
                st.session_state["selected_daily_note_history_date"] = day_date

    st.markdown("</div>", unsafe_allow_html=True)

    selected_note_date = st.session_state.get("selected_daily_note_history_date")
    if selected_note_date:
        note_history = get_daily_log_notes_by_date(user_id, selected_note_date, limit=20)
        if note_history:
            st.markdown(f"#### Nutritionist note history for {selected_note_date}")
            for n in note_history:
                st.markdown(
                    f"""
                    <div class='info-banner'>
                      <b>{format_local_ts(n.get('ts',''))}</b><br>
                      <p>{n.get('note','')}</p>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
        else:
            st.info("No nutritionist notes found for the selected date.")
card_end()


# Reference moved to bottom, with more aesthetic and compact expander.
SAMPLE_ROWS = [
    {"Time": "10:00 - 10:30 AM", "Meal Type": "Breakfast", "Food": "Boiled eggs / omelet / moong dal chilla / poha", "Portion Size": "2 eggs / 2 chilla / 1 bowl poha", "Mood/Energy": "Fresh", "Activity": "1 PM - 2 PM", "Poop": "2-3 times / felt relieved", "Notes": "Mention exact items."},
    {"Time": "2:30 - 2:45 PM", "Meal Type": "Lunch", "Food": "Dal + rice / roti + salad + curd + sabzi", "Portion Size": "100 ml rice + 100 ml dal", "Mood/Energy": "Energetic", "Activity": "", "Poop": "", "Notes": ""},
    {"Time": "5:00 - 5:30 PM", "Meal Type": "Evening Snack", "Food": "Half cup tea with snack", "Portion Size": "", "Mood/Energy": "Okay", "Activity": "", "Poop": "", "Notes": ""},
    {"Time": "7:30 - 8:00 PM", "Meal Type": "Dinner", "Food": "Soup / light dinner", "Portion Size": "1 big bowl", "Mood/Energy": "Energetic", "Activity": "", "Poop": "", "Notes": ""},
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
