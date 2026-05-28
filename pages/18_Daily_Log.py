import streamlit as st
import html
from datetime import date, time
from components.guards import require_member
from components.ui_common import inject_global_styles, apply_luxe_theme, topbar, card_start, card_end, utility_logout_bar, format_local_ts, render_back_to_top, compact_topbar

def render_context_selector_header(title, items, note=""):
    """Page-local fallback so Daily Log pages do not crash if shared UI helper is stale on deployment."""
    chips = "".join([f"<div class='hm-context-chip'><span>{label}</span><b>{value}</b></div>" for label, value in items])
    note_html = f"<div class='hm-context-note'>{note}</div>" if note else ""
    st.markdown(
        f"""
        <div class='hm-context-card'>
          <div class='hm-context-title'>{title}</div>
          <div class='hm-context-grid'>{chips}</div>
          {note_html}
        </div>
        """,
        unsafe_allow_html=True,
    )
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

    /* v76J: Member Daily Log premium card styling is enforced only on the Food Journal Date section. */
    /* Style only the Streamlit container that contains this marker. */
    div[data-testid="stVerticalBlockBorderWrapper"]:has(.hm-food-date-marker),
    div[data-testid="stVerticalBlock"]:has(.hm-food-date-marker) {
      background:linear-gradient(180deg,#FFFFFF 0%,#FFFBF4 100%) !important;
      border:1.5px solid #E7D8BE !important;
      border-radius:18px !important;
      box-shadow:0 8px 22px rgba(25,36,31,.055) !important;
      padding:.74rem .9rem .9rem .9rem !important;
      margin:.35rem 0 .65rem 0 !important;
    }
    .hm-food-date-title {
      font-size:1.03rem;
      font-weight:900;
      color:#064E3B;
      margin-bottom:.42rem;
      letter-spacing:-.01em;
    }
    div[data-testid="stVerticalBlockBorderWrapper"]:has(.hm-food-date-marker) div[data-testid="stDateInput"] input,
    div[data-testid="stVerticalBlock"]:has(.hm-food-date-marker) div[data-testid="stDateInput"] input{
      background:#FFFFFF!important;
      border:1.4px solid #E7D8BE!important;
      min-height:2.65rem!important;
      font-weight:760!important;
      color:#063F32!important;
      border-radius:12px!important;
    }
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
    return any(str((meal or {}).get(x, "")).strip() for x in ["time", "food", "portion_size", "mood_energy"])


def display_date(d):
    try:
        return d.strftime("%d/%m/%Y") if hasattr(d, "strftime") else date.fromisoformat(str(d)).strftime("%d/%m/%Y")
    except Exception:
        return str(d or "")

def time_options():
    vals = [""]
    for h in range(24):
        for m in (0, 15, 30, 45):
            hour12 = h % 12 or 12
            ampm = "AM" if h < 12 else "PM"
            vals.append(f"{hour12:02d}.{m:02d} {ampm}")
    return vals

def normalise_time_value(value):
    value = str(value or "").strip().replace(":", ".")
    opts = time_options()
    if value in opts:
        return value
    return ""

def meal_display(label, meal):
    tm = str((meal or {}).get("time", "")).strip()
    food = str((meal or {}).get("food", "")).strip()
    if tm and food:
        return f"{label}: {tm}: {food}"
    if food:
        return f"{label}: {food}"
    return ""

def day_detail_has_data(water_litres, physical_activity, poop_rounds, poop_timings, feeling_after_poop, day_notes):
    return any([
        water_litres and water_litres != "Select",
        str(physical_activity or "").strip(),
        poop_rounds is not None and str(poop_rounds) != "Select",
        any(str(x or "").strip() for x in (poop_timings or [])),
        str(feeling_after_poop or "").strip(),
        str(day_notes or "").strip(),
    ])

def journal_has_any_data(meals, water_litres, physical_activity, poop_rounds, poop_timings, feeling_after_poop, day_notes):
    return any(meal_has_data(m) for m in (meals or {}).values()) or day_detail_has_data(water_litres, physical_activity, poop_rounds, poop_timings, feeling_after_poop, day_notes)

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

with st.container(border=True):
    st.markdown("<div class='hm-food-date-marker'></div>", unsafe_allow_html=True)
    st.markdown("<div class='hm-food-date-title'>📅 Food Journal Date</div>", unsafe_allow_html=True)
    log_date = st.date_input("Food journal date", value=date.today(), format="DD/MM/YYYY", label_visibility="collapsed")
st.markdown(f"<div class='hm-context-note'>Food Journal Date: <b>{display_date(log_date)}</b></div>", unsafe_allow_html=True)
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

preferred_order = ["breakfast", "lunch", "evening_snack", "dinner", "bedtime"]
section_lookup = {k: v for k, v in base_sections}
meal_sections = [(k, section_lookup[k]) for k in preferred_order if k in section_lookup]
meal_sections += [(k, v) for k, v in base_sections if k not in preferred_order and k != "other"]
for idx in range(1, st.session_state.get("daily_log_other_count", 1) + 1):
    meal_sections.append((f"other_{idx}", "Snacking" if idx == 1 else f"Snacking {idx - 1}"))

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
    if st.button("+ Snacking", use_container_width=True, help="Add another snacking/eating time such as Snacking 1, Snacking 2, etc."):
        if is_dirty(existing_meals, active_key, active_label):
            st.warning(f"Please save the section ({active_label}) before adding another Snacking section.")
        else:
            st.session_state["daily_log_other_count"] = st.session_state.get("daily_log_other_count", 1) + 1
            st.session_state["active_daily_meal_section"] = f"other_{st.session_state['daily_log_other_count']}"
            st.rerun()
with add_cols[1]:
    st.caption("Use Snacking for eating times beyond the standard meals.")

st.markdown(f"<div class='hm-meal-title'>{active_label}</div>", unsafe_allow_html=True)
prior = existing_meals.get(active_key, {}) if existing_meals else {}

time_values = time_options()
time_default = normalise_time_value(prior.get("time", ""))
time_index = time_values.index(time_default) if time_default in time_values else 0
time_text = st.selectbox("Time", time_values, index=time_index, key=f"{active_key}_time", format_func=lambda x: "Select time" if x == "" else x)

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
        if not meal_has_data(active_payload):
            st.error("Please enter at least one detail for this meal before saving.")
        else:
            save_daily_food_journal_meal(user_id, str(log_date), active_key, active_payload)
            set_system_message(f"{active_label} saved for {display_date(log_date)}.", "success")
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
left_col, right_col = st.columns([1, 1])
with left_col:
    water_litres = st.selectbox("Water intake for the full day", water_options, index=water_index)
    physical_activity = st.text_area(
        "Physical activity - time of day and duration",
        value=existing.get("physical_activity", ""),
        placeholder="Example: Walk 30 mins at 07.00 AM / strength training 01.00 PM - 02.00 PM",
        height=96,
    )

with right_col:
    poop_options = ["Select", 0] + list(range(1, 10))
    existing_poop_rounds = existing.get("poop_rounds", "Select")
    if existing_poop_rounds in (None, "", "Select"):
        existing_poop_rounds = "Select"
    elif str(existing_poop_rounds).isdigit():
        existing_poop_rounds = int(existing_poop_rounds)
    poop_widget_key = f"poop_rounds_{user_id}_{str(log_date)}"
    if poop_widget_key not in st.session_state:
        st.session_state[poop_widget_key] = existing_poop_rounds
    poop_rounds = st.selectbox("Poop rounds", poop_options, key=poop_widget_key)
    feeling_after_poop = st.text_area(
        "Feeling after poop",
        value=existing.get("feeling_after_poop", ""),
        placeholder="Example: relieved / constipated / bloated / loose stool / incomplete",
        height=96,
    )

st.caption("All 9 poop timing slots remain visible. Select 0 to keep all inactive; selecting 1-9 activates the matching number of slots.")
poop_timings = []
existing_timings = existing.get("poop_timings", []) or []
timing_values = time_options()
enabled_count = int(poop_rounds) if str(poop_rounds).isdigit() else 0
for idx in range(9):
    default_timing = existing_timings[idx] if idx < len(existing_timings) else ""
    default_timing = normalise_time_value(default_timing)
    timing_index = timing_values.index(default_timing) if default_timing in timing_values else 0
    val = st.selectbox(
        f"Poop Timing {idx + 1}",
        timing_values,
        index=timing_index,
        key=f"poop_timing_{user_id}_{str(log_date)}_{idx + 1}",
        disabled=(idx >= enabled_count),
        format_func=lambda x: "Not active" if x == "" else x,
    )
    if idx < enabled_count:
        poop_timings.append(val)
poop = ""
day_notes = st.text_area("Overall notes for the day", value=existing.get("notes", ""), placeholder="Any cravings, bloating, missed meals, late meals, etc.", height=85)

c_save_1, c_save_2 = st.columns(2)
with c_save_1:
    if st.button("Save Day Details Only", use_container_width=True):
        if not day_detail_has_data(water_litres, physical_activity, poop_rounds, poop_timings, feeling_after_poop, day_notes):
            st.error("Please enter at least one full-day detail before saving.")
        else:
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
                (f"{poop_rounds} round(s)" if str(poop_rounds).isdigit() and int(poop_rounds) > 0 else "")
                + (f" at {', '.join([x.strip() for x in poop_timings if x.strip()])}" if str(poop_rounds).isdigit() and int(poop_rounds) > 0 and any(x.strip() for x in poop_timings) else "")
                + (f" / {feeling_after_poop.strip()}" if feeling_after_poop.strip() else "")
            ),
            "notes": day_notes.strip(),
            "water_litres": water_litres,
        }
        if not journal_has_any_data(merged_meals, water_litres, physical_activity, poop_rounds, poop_timings, feeling_after_poop, day_notes):
            st.error("Please enter at least one journal detail before saving.")
        else:
            save_daily_food_journal_day(user_id, str(log_date), payload)
            set_system_message("Full-day food journal saved.", "success")
            st.rerun()
card_end()

card_start()
st.markdown("""
<div class='hm-compact-section-head'>
  <div class='hm-compact-section-title'>Recent saved days</div>
  <div class='hm-compact-section-note'>View your recently saved day entries and the latest note from your nutritionist.</div>
</div>
""", unsafe_allow_html=True)
days = get_daily_food_journal_days(user_id)
if not days:
    st.info("No food journal days saved yet.")
else:
    st.markdown("<div class='hm-rsd-native-shell'>", unsafe_allow_html=True)

    h1, h2, h3, h4, h5, h6 = st.columns([1.05, 1.75, .9, .9, 2.05, .85])
    h1.markdown("**Date**")
    h2.markdown("**Meal type and food**")
    h3.markdown("**Water**")
    h4.markdown("**Notes**")
    h5.markdown("**Nutritionist Notes**")
    h6.markdown("**Action**")
    st.markdown("<div class='hm-rsd-native-divider'></div>", unsafe_allow_html=True)

    for day in days[:14]:
        day_date = day.get("date", "")
        meal_summary = []
        meal_items = list((day.get("meals", {}) or {}).items())
        def _meal_sort_key(item):
            key, _meal = item
            if key in preferred_order:
                return (preferred_order.index(key), 0)
            if str(key).startswith("other_"):
                try:
                    return (len(preferred_order), int(str(key).split("_")[1]))
                except Exception:
                    return (len(preferred_order), 999)
            return (len(preferred_order) + 1, str(key))
        for _k, meal in sorted(meal_items, key=_meal_sort_key):
            if meal.get("food"):
                label = meal.get('label','')
                meal_summary.append(meal_display(label, meal))
        meal_display_text = " | ".join(meal_summary) if meal_summary else "—"

        latest_note = get_latest_daily_log_note_for_date(user_id, day_date)
        latest_note_text = "—"
        has_notes = False
        if latest_note:
            has_notes = True
            latest_note_text = f"{format_local_ts(latest_note.get('ts',''))} — {latest_note.get('note','')}"

        with st.container():
            c1, c2, c3, c4, c5, c6 = st.columns([1.05, 1.75, .9, .9, 2.05, .85])
            c1.markdown(f"<div class='hm-rsd-native-date'>{display_date(day_date) if day_date else '—'}</div>", unsafe_allow_html=True)
            c2.markdown(f"<div class='hm-rsd-native-meals'>{meal_display_text}</div>", unsafe_allow_html=True)
            c3.markdown(f"<div class='hm-rsd-native-cell'>{day.get('water_litres') or '—'}</div>", unsafe_allow_html=True)
            c4.markdown(f"<div class='hm-rsd-native-cell'>{day.get('notes') or '—'}</div>", unsafe_allow_html=True)
            c5.markdown(f"<div class='hm-rsd-native-note'>{latest_note_text}</div>", unsafe_allow_html=True)

            selected_date = st.session_state.get("selected_daily_note_history_date")
            button_label = "Hide history" if selected_date == day_date else "View history"
            with c6:
                if st.button(button_label, key=f"rsd_native_history_{day_date}", disabled=not has_notes):
                    if selected_date == day_date:
                        st.session_state["selected_daily_note_history_date"] = None
                    else:
                        st.session_state["selected_daily_note_history_date"] = day_date
                    st.rerun()

            st.markdown("<div class='hm-rsd-native-divider'></div>", unsafe_allow_html=True)

            if st.session_state.get("selected_daily_note_history_date") == day_date:
                note_history = get_daily_log_notes_by_date(user_id, day_date, limit=20)
                if note_history:
                    st.markdown(f"#### Nutritionist note history for {day_date}")
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

    st.markdown("</div>", unsafe_allow_html=True)
card_end()


# Reference moved to bottom, with more aesthetic and compact expander.
SAMPLE_ROWS = [
    {"Time": "10:00 - 10:30 AM", "Meal Type": "Breakfast", "Food": "Boiled eggs / omelet / moong dal chilla / poha", "Portion Size": "2 eggs / 2 chilla / 1 bowl poha", "Mood/Energy": "Fresh", "Activity": "1 PM - 2 PM", "Poop": "2-3 times / felt relieved", "Notes": "Mention exact items."},
    {"Time": "2:30 - 2:45 PM", "Meal Type": "Lunch", "Food": "Dal + rice / roti + salad + curd + sabzi", "Portion Size": "100 ml rice + 100 ml dal", "Mood/Energy": "Energetic", "Activity": "", "Poop": "", "Notes": ""},
    {"Time": "5:00 - 5:30 PM", "Meal Type": "Evening Snack", "Food": "Half cup tea with snack", "Portion Size": "", "Mood/Energy": "Okay", "Activity": "", "Poop": "", "Notes": ""},
    {"Time": "7:30 - 8:00 PM", "Meal Type": "Dinner", "Food": "Soup / light dinner", "Portion Size": "1 big bowl", "Mood/Energy": "Energetic", "Activity": "", "Poop": "", "Notes": ""},
]

st.markdown("""
<div class='hm-reference-shell'>
  <div class='hm-reference-row'>
    <div>
      <div class='hm-reference-title'>Reference format from sample journal</div>
      <div class='hm-compact-section-note'>Use only when needed.</div>
    </div>
  </div>
""", unsafe_allow_html=True)
if "show_daily_reference_sample" not in st.session_state:
    st.session_state["show_daily_reference_sample"] = False
if st.button("Show / Hide sample journal format", use_container_width=True):
    st.session_state["show_daily_reference_sample"] = not st.session_state["show_daily_reference_sample"]
if st.session_state["show_daily_reference_sample"]:
    st.dataframe(SAMPLE_ROWS, use_container_width=True, hide_index=True)
st.markdown("</div>", unsafe_allow_html=True)

if st.button("Back to Home", use_container_width=True):
    st.switch_page("pages/02_Member_Home.py")
