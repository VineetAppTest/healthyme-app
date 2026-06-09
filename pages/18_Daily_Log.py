import streamlit as st
import html
import re
from datetime import date, time
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
        margin-top: .2rem;
        margin-bottom: .1rem;
        font-size: 1.05rem;
        font-weight: 850;
        color: #064E3B;
    }
    .hm-snack-helper {
        margin-top: .45rem;
        color: #7C8A96;
        font-size: .82rem;
        line-height: 1.2;
    }
    .hm-section-mini-gap {
        margin-top: .15rem;
        margin-bottom: .15rem;
    }
    .hm-full-day-helper {
        margin-top: -.1rem;
        margin-bottom: .35rem;
        color: #7C8A96;
        font-size: .81rem;
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

device_mode_v90a = get_device_mode_for_spike()
is_mobile_mode_v90a = device_mode_v90a == "mobile"
rendered_controls_v90a = "mobile test controls" if is_mobile_mode_v90a else "desktop controls"

st.markdown(f"""
<div class='hm-v90a-diagnostic'>
  <b>v90A Mobile Detection Spike</b><br>
  Device mode: <b>{device_mode_v90a}</b> &nbsp;|&nbsp;
  Rendered controls: <b>{rendered_controls_v90a}</b><br>
  Mobile test URL: add <code>?device=mobile</code>. Desktop default: no query parameter.
</div>
""", unsafe_allow_html=True)


st.markdown("""
<style>
.hm-v88-balanced-empty{min-height:.1rem!important;}
.hm-snack-helper-tight{margin-top:.05rem!important;font-size:.78rem!important;line-height:1.15!important;}
.hm-rsd-mobile-shell{margin-top:.15rem!important;}
.hm-rsd-mobile-card{border-top:1.15px solid #E5D2A9;padding:.52rem 0 .48rem 0;}
.hm-rsd-mobile-label{color:#36506A;font-size:.78rem;font-weight:850;line-height:1.15;padding:.10rem 0;}
.hm-rsd-mobile-value{color:#102A43;font-size:.84rem;line-height:1.25;padding:.10rem 0;}
.hm-rsd-mobile-card [data-testid="column"]{display:flex!important;align-items:flex-start!important;}
.hm-rsd-mobile-card .stButton > button{min-height:1.75rem!important;padding:.12rem .55rem!important;font-size:.74rem!important;}
@media (max-width:768px){
  .hm-v88-balanced-empty{display:none!important;}
  .hm-snack-helper-tight{margin-top:-.05rem!important;}
  .hm-rsd-mobile-label{font-size:.76rem!important;}
  .hm-rsd-mobile-value{font-size:.82rem!important;}
}
</style>
""", unsafe_allow_html=True)

auto_archive_expired_nutritionist_messages(user_id)

def meal_has_data(meal):
    return any((meal or {}).get(x) for x in ["time", "food", "portion_size", "mood_energy"])

def current_widget_payload(section_key, section_label):
    hour = st.session_state.get(f"{section_key}_time_h", "HH")
    minute = st.session_state.get(f"{section_key}_time_m", "MM")
    period = st.session_state.get(f"{section_key}_time_p", "AM/PM")
    if hour == "HH" and minute == "MM" and period == "AM/PM":
        time_value = ""
    elif hour != "HH" and minute != "MM" and period in ["AM", "PM"]:
        time_value = f"{hour}:{minute} {period}"
    else:
        time_value = "__PARTIAL__"
    return {
        "label": section_label,
        "time": time_value,
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


def get_device_mode_for_spike():
    """
    v90A controlled mobile-detection spike.

    Desktop remains default. Mobile branch activates only with:
    ?device=mobile
    """
    try:
        qp = st.query_params
        raw = qp.get("device", "desktop")
        if isinstance(raw, list):
            raw = raw[0] if raw else "desktop"
        raw = str(raw).strip().lower()
    except Exception:
        raw = "desktop"
    return "mobile" if raw == "mobile" else "desktop"

def to_time_input_value(value):
    raw = (value or "").strip().upper()
    m = re.match(r"^(0?[1-9]|1[0-2]):([0-5][0-9])\s*(AM|PM)$", raw)
    if not m:
        return None
    h = int(m.group(1))
    minute = int(m.group(2))
    period = m.group(3)
    if period == "AM":
        hour24 = 0 if h == 12 else h
    else:
        hour24 = 12 if h == 12 else h + 12
    return time(hour24, minute)

def from_time_input_value(value):
    if value is None:
        return ""
    hour24 = value.hour
    minute = value.minute
    period = "AM" if hour24 < 12 else "PM"
    h12 = hour24 % 12
    if h12 == 0:
        h12 = 12
    return f"{h12:02d}:{minute:02d} {period}"

def render_v90a_chip_selector(label, options, current_value, key_prefix, columns=4):
    st.markdown(f"<div class='hm-v90a-chip-label'>{label}</div>", unsafe_allow_html=True)
    selected = st.session_state.get(key_prefix, current_value)
    if selected not in options:
        selected = current_value if current_value in options else options[0]
    st.session_state[key_prefix] = selected

    for start in range(0, len(options), columns):
        cols = st.columns(columns)
        for col, option in zip(cols, options[start:start + columns]):
            button_label = str(option)
            safe_label = button_label.replace(" ", "_").replace("+", "plus").replace(".", "_")
            with col:
                if st.button(button_label, key=f"{key_prefix}_{safe_label}", use_container_width=True):
                    st.session_state[key_prefix] = option
                    st.rerun()
    return st.session_state.get(key_prefix, selected)


def split_12h_time_parts(value):
    raw = (value or "").strip().upper()
    m = re.match(r"^(0?[1-9]|1[0-2]):([0-5][0-9])\s*(AM|PM)$", raw)
    if not m:
        return ("HH", "MM", "AM/PM")
    return (f"{int(m.group(1)):02d}", m.group(2), m.group(3))

def parse_12h_time_to_minutes(value):
    raw = (value or "").strip().upper()
    m = re.match(r"^(0?[1-9]|1[0-2]):([0-5][0-9])\s*(AM|PM)$", raw)
    if not m:
        return None
    hour = int(m.group(1))
    minute = int(m.group(2))
    suffix = m.group(3)
    if suffix == "AM":
        hour = 0 if hour == 12 else hour
    else:
        hour = 12 if hour == 12 else hour + 12
    return hour * 60 + minute

def in_window(minutes, start, end):
    if minutes is None:
        return False
    if start <= end:
        return start <= minutes <= end
    return minutes >= start or minutes <= end

STANDARD_MEAL_WINDOWS = {
    "breakfast": ("6:00 AM to 11:00 AM", 6 * 60, 11 * 60),
    "lunch": ("12:00 PM to 3:00 PM", 12 * 60, 15 * 60),
    "evening_snacks": ("4:00 PM to 6:00 PM", 16 * 60, 18 * 60),
    "dinner": ("7:00 PM to 10:00 PM", 19 * 60, 22 * 60),
    "bedtime": ("11:00 PM to 12:00 AM", 23 * 60, 0),
}

def meal_window_key(section_key, section_label):
    key = str(section_key or "").lower()
    label = str(section_label or "").lower()
    if key.startswith("snacking_") or "snacking" in label:
        return "snacking"
    if "breakfast" in key or "breakfast" in label:
        return "breakfast"
    if "lunch" in key or "lunch" in label:
        return "lunch"
    if "evening" in key and "snack" in key:
        return "evening_snacks"
    if "evening" in label and "snack" in label:
        return "evening_snacks"
    if "dinner" in key or "dinner" in label:
        return "dinner"
    if "bedtime" in key or "bedtime" in label:
        return "bedtime"
    return "snacking"

def meal_time_guidance(section_key, section_label):
    window_key = meal_window_key(section_key, section_label)
    if window_key == "snacking":
        return "Enter time outside standard meal windows, e.g., 11:30 AM"
    return f"Enter time between {STANDARD_MEAL_WINDOWS[window_key][0]}"

def validate_meal_time(section_key, section_label, time_value):
    raw = (time_value or "").strip()
    if not raw:
        return True, ""
    minutes = parse_12h_time_to_minutes(raw)
    if minutes is None:
        return False, "Please complete meal timing using Hour, Minute, and AM/PM, for example 08:30 AM."
    window_key = meal_window_key(section_key, section_label)
    if window_key == "snacking":
        inside_standard = any(in_window(minutes, start, end) for _label, start, end in STANDARD_MEAL_WINDOWS.values())
        if inside_standard:
            return False, "Snacking time must be outside the standard meal windows."
        return True, ""
    label, start, end = STANDARD_MEAL_WINDOWS[window_key]
    if not in_window(minutes, start, end):
        return False, f"{section_label} time must be between {label}."
    return True, ""



# Fixed Daily Log meal structure.
st.markdown("<div class='hm-daily-date-shell'><div class='hm-daily-date-title'>Food journal date</div>", unsafe_allow_html=True)
log_date = st.date_input("Food journal date", value=date.today(), label_visibility="collapsed")
st.markdown("</div>", unsafe_allow_html=True)
existing = get_daily_food_journal_day(user_id, str(log_date))
existing_meals = existing.get("meals", {}) if existing else {}

normalised_meals = {}
snack_counter = 0
for k, v in (existing_meals or {}).items():
    if str(k).startswith("other_"):
        snack_counter += 1
        normalised_meals[f"snacking_{snack_counter}"] = dict(v or {}, label=f"Snacking {snack_counter}")
    else:
        normalised_meals[k] = v
existing_meals = normalised_meals

standard_sections = [
    ("breakfast", "Breakfast"),
    ("lunch", "Lunch"),
    ("evening_snacks", "Evening Snacks"),
    ("dinner", "Dinner"),
    ("bedtime", "Bedtime"),
]

existing_snack_nums = []
for key in existing_meals.keys():
    if key.startswith("snacking_"):
        try:
            existing_snack_nums.append(int(key.split("_")[1]))
        except Exception:
            pass

if "daily_log_snacking_count" not in st.session_state:
    st.session_state["daily_log_snacking_count"] = max(existing_snack_nums) if existing_snack_nums else 0
elif existing_snack_nums:
    st.session_state["daily_log_snacking_count"] = max(st.session_state.get("daily_log_snacking_count", 0), max(existing_snack_nums))

meal_sections = list(standard_sections)
for idx in range(1, st.session_state.get("daily_log_snacking_count", 0) + 1):
    meal_sections.append((f"snacking_{idx}", f"Snacking {idx}"))

if not meal_sections:
    st.warning("No meal sections are currently active. Please contact admin.")
    st.stop()

if "active_daily_meal_section" not in st.session_state or st.session_state["active_daily_meal_section"] not in [x[0] for x in meal_sections]:
    st.session_state["active_daily_meal_section"] = meal_sections[0][0]


card_start()
st.subheader("Meal sections")
st.markdown("<div class='hm-compact-section-note hm-section-mini-gap'>Tap a meal to open it. Save the current meal before moving to another section.</div>", unsafe_allow_html=True)

active_key = st.session_state["active_daily_meal_section"]
active_label = next((label for key, label in meal_sections if key == active_key), meal_sections[0][1])

# v88 balanced meal selector:
# Row 1: Breakfast / Lunch / Evening Snacks
# Row 2: Dinner / Bedtime
# Row 3: +Snacking action
# Row 4+: Snacking 1..n
def render_meal_section_button(key, label):
    saved = meal_has_data(existing_meals.get(key, {}))
    short_label = f"{'● ' if key == active_key else ''}{label}{' ✓' if saved else ''}"
    if st.button(short_label, key=f"section_btn_{key}", use_container_width=True):
        if key != active_key and is_dirty(existing_meals, active_key, active_label):
            st.warning(f"Please save the section ({active_label}) before moving to next section.")
        else:
            st.session_state["active_daily_meal_section"] = key
            st.rerun()

row1 = [("breakfast", "Breakfast"), ("lunch", "Lunch"), ("evening_snacks", "Evening Snacks")]
row1_cols = st.columns(3)
for col, (key, label) in zip(row1_cols, row1):
    with col:
        render_meal_section_button(key, label)

row2 = [("dinner", "Dinner"), ("bedtime", "Bedtime")]
row2_cols = st.columns(3)
for col, item in zip(row2_cols[:2], row2):
    with col:
        render_meal_section_button(item[0], item[1])
with row2_cols[2]:
    st.markdown("<div class='hm-v88-balanced-empty'></div>", unsafe_allow_html=True)

add_cols = st.columns([1.15, 1.85])
with add_cols[0]:
    if st.button("+ Snacking", use_container_width=True, help="Add another snacking time outside the standard meal windows."):
        if is_dirty(existing_meals, active_key, active_label):
            st.warning(f"Please save the section ({active_label}) before adding another Snacking section.")
        else:
            st.session_state["daily_log_snacking_count"] = st.session_state.get("daily_log_snacking_count", 0) + 1
            st.session_state["active_daily_meal_section"] = f"snacking_{st.session_state['daily_log_snacking_count']}"
            st.rerun()
with add_cols[1]:
    st.markdown("<div class='hm-snack-helper hm-snack-helper-tight'>Snacking is for entries outside standard meal windows.</div>", unsafe_allow_html=True)

snacking_sections = [(key, label) for key, label in meal_sections if key.startswith("snacking_")]
if snacking_sections:
    for start in range(0, len(snacking_sections), 3):
        snack_cols = st.columns(3)
        for col, item in zip(snack_cols, snacking_sections[start:start + 3]):
            with col:
                render_meal_section_button(item[0], item[1])

st.markdown(f"<div class='hm-meal-title'>{active_label}</div>", unsafe_allow_html=True)
prior = existing_meals.get(active_key, {}) if existing_meals else {}

time_guidance = meal_time_guidance(active_key, active_label)
pre_h, pre_m, pre_p = split_12h_time_parts(prior.get("time", ""))
st.session_state.setdefault(f"{active_key}_time_h", pre_h)
st.session_state.setdefault(f"{active_key}_time_m", pre_m)
st.session_state.setdefault(f"{active_key}_time_p", pre_p)
st.markdown("<div class='hm-compact-section-note'>Meal Timing</div>", unsafe_allow_html=True)
if is_mobile_mode_v90a:
    existing_time_value = to_time_input_value(prior.get("time", ""))
    fallback_time_value = existing_time_value or time(8, 0)
    selected_time_value = st.time_input(
        "Select Meal Timing",
        value=fallback_time_value,
        key=f"{active_key}_v90a_mobile_native_time",
    )
    native_time_text = from_time_input_value(selected_time_value)
    time_h, time_m, time_p = split_12h_time_parts(native_time_text)
    st.session_state[f"{active_key}_time_h"] = time_h
    st.session_state[f"{active_key}_time_m"] = time_m
    st.session_state[f"{active_key}_time_p"] = time_p
    st.markdown(f"<div class='hm-time-preview'>Selected: {native_time_text}</div>", unsafe_allow_html=True)
else:
    th, tm, tp = st.columns([1, 1, 1])
    with th:
        hour_options = ["HH"] + [f"{i:02d}" for i in range(1, 13)]
        current_h = st.session_state.get(f"{active_key}_time_h", pre_h)
        st.selectbox(
            "HH",
            hour_options,
            index=hour_options.index(current_h) if current_h in hour_options else 0,
            key=f"{active_key}_time_h",
            label_visibility="collapsed",
        )
    with tm:
        minute_options = ["MM"] + [f"{i:02d}" for i in range(0, 60)]
        current_m = st.session_state.get(f"{active_key}_time_m", pre_m)
        st.selectbox(
            "MM",
            minute_options,
            index=minute_options.index(current_m) if current_m in minute_options else 0,
            key=f"{active_key}_time_m",
            label_visibility="collapsed",
        )
    with tp:
        ampm_options = ["AM/PM", "AM", "PM"]
        current_p = st.session_state.get(f"{active_key}_time_p", pre_p)
        st.selectbox(
            "AM/PM",
            ampm_options,
            index=ampm_options.index(current_p) if current_p in ampm_options else 0,
            key=f"{active_key}_time_p",
            label_visibility="collapsed",
        )
st.markdown(f"<div class='hm-full-day-helper'>{time_guidance}</div>", unsafe_allow_html=True)

food = st.text_area("Food", value=prior.get("food", ""), key=f"{active_key}_food", placeholder=f"What did you have for {active_label.lower()}?", height=78)

c3, c4 = st.columns([1, 1])
with c3:
    portion = st.text_input("Portion Size", value=prior.get("portion_size", ""), key=f"{active_key}_portion", placeholder="Example: 1 bowl / 2 rotis / 250 ml")
with c4:
    mood = st.text_input("Mood / Energy", value=prior.get("mood_energy", ""), key=f"{active_key}_mood", placeholder="Example: fresh / heavy / energetic")

active_payload = current_widget_payload(active_key, active_label)
meal_dirty = is_dirty(existing_meals, active_key, active_label)
meal_time_valid, meal_time_error = validate_meal_time(active_key, active_label, active_payload.get("time", ""))
if active_payload.get("time") and not meal_time_valid:
    st.error(meal_time_error)

if st.button(f"Save {active_label}", use_container_width=True):
    if not meal_time_valid:
        st.error(meal_time_error)
    else:
        save_daily_food_journal_meal(user_id, str(log_date), active_key, active_payload)
        set_system_message(f"{active_label} saved for {log_date}.", "success")
        st.rerun()
if meal_dirty:
    st.warning(f"Unsaved changes in {active_label}.")
elif meal_has_data(prior):
    st.success(f"{active_label} saved.")
else:
    st.caption("No saved entry yet.")
card_end()

card_start()
st.subheader("Full-day details")
top_left, top_right = st.columns(2)
with top_left:
    water_options = ["Select"] + [
        "0 Litres",
        "0.5 Litres",
        "1 Litre",
        "1.5 Litres",
        "2 Litres",
        "2.5 Litres",
        "3 Litres",
        "3.5 Litres",
        "4 Litres",
        "4.5 Litres",
        "5 Litres",
        "5.5 Litres",
        "6 Litres",
        "6.5 Litres",
        "7 Litres",
        "7.5 Litres",
        "8 Litres",
        "8.5 Litres",
        "9 Litres",
        "9.5 Litres",
        "10 Litres",
    ]
    mobile_water_options = ["Select", "0 Litres", "0.5 Litres", "1 Litre", "1.5 Litres", "2 Litres", "2.5 Litres", "3 Litres", "3.5 Litres", "4 Litres", "4.5 Litres", "5+ Litres"]
    existing_water = existing.get("water_litres", "Select") or "Select"
    if is_mobile_mode_v90a:
        water_litres = render_v90a_chip_selector(
            "Water intake for the full day",
            mobile_water_options,
            existing_water if existing_water in mobile_water_options else "Select",
            "v90a_mobile_water_litres",
            columns=4,
        )
    else:
        water_litres = st.selectbox(
            "Water intake for the full day",
            water_options,
            index=water_options.index(existing_water) if existing_water in water_options else 0,
        )
with top_right:
    poop_options = ["Select", 0, 1, 2, 3, 4, 5, 6]
    existing_poop_rounds = existing.get("poop_rounds", "Select")
    if existing_poop_rounds in ("", None):
        existing_poop_rounds = "Select"
    if str(existing_poop_rounds).isdigit():
        existing_poop_rounds = int(existing_poop_rounds)
    if is_mobile_mode_v90a:
        poop_rounds = render_v90a_chip_selector(
            "Poop rounds",
            poop_options,
            existing_poop_rounds if existing_poop_rounds in poop_options else "Select",
            "v90a_mobile_poop_rounds",
            columns=4,
        )
    else:
        poop_rounds = st.selectbox(
            "Poop rounds",
            poop_options,
            index=poop_options.index(existing_poop_rounds) if existing_poop_rounds in poop_options else 0,
        )

poop_timings = []
existing_timings = existing.get("poop_timings", []) or []
active_poop_count = int(poop_rounds) if poop_rounds != "Select" else 0
st.markdown("<div class='hm-full-day-helper hm-full-day-helper-tight'>Record poop timings.</div>", unsafe_allow_html=True)
st.markdown("<div class='hm-poop-timing-grid-anchor'></div>", unsafe_allow_html=True)
for row_start in range(0, 6, 3):
    timing_cols = st.columns(3)
    for col_offset in range(3):
        idx = row_start + col_offset
        timing_no = idx + 1
        is_active = timing_no <= active_poop_count
        default_timing = existing_timings[idx] if idx < len(existing_timings) else ""
        with timing_cols[col_offset]:
            value = st.text_input(
                f"Poop Timing {timing_no}",
                value=default_timing if is_active else "",
                key=f"poop_timing_{timing_no}",
                placeholder="Enter the Poop Time" if is_active else "Not active",
                disabled=not is_active,
            )
            poop_timings.append(value if is_active else "")

feel_col, phys_col = st.columns([1.0, 1.0])
with feel_col:
    feeling_after_poop = st.text_input(
        "Feeling after poop",
        value=existing.get("feeling_after_poop", ""),
        placeholder="Example: relieved / constipated / bloated / loose stool / incomplete",
    )
with phys_col:
    physical_activity = st.text_area(
        "Physical activity - time of day and duration",
        value=existing.get("physical_activity", ""),
        placeholder="Example: Walk 30 mins at 7 AM / strength training 1 PM - 2 PM",
        height=96,
    )

poop = ""
day_notes = st.text_area(
    "Overall notes for the day",
    value=existing.get("notes", ""),
    placeholder="Any cravings, bloating, missed meals, late meals, etc.",
    height=90,
)

c_save_1, c_save_2 = st.columns(2)
with c_save_1:
    if st.button("Save Day Details Only", use_container_width=True):
        save_daily_food_journal_day_details(user_id, str(log_date), physical_activity.strip(), poop, day_notes.strip(), water_litres, poop_rounds, poop_timings, feeling_after_poop.strip())
        set_system_message("Day details saved.", "success")
        st.rerun()
with c_save_2:
    if st.button("Save Full-Day Journal", use_container_width=True):
        if not meal_time_valid:
            st.error(meal_time_error)
            st.stop()
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
    st.markdown("<div class='hm-rsd-mobile-shell'>", unsafe_allow_html=True)

    for day in days[:14]:
        day_date = day.get("date", "")
        meal_summary = []
        for _k, meal in (day.get("meals", {}) or {}).items():
            if meal.get("food"):
                meal_summary.append(f"{meal.get('label','')}: {meal.get('food','')}")
        meal_display_text = " | ".join(meal_summary) if meal_summary else "—"

        latest_note = get_latest_daily_log_note_for_date(user_id, day_date)
        latest_note_text = "—"
        has_notes = False
        if latest_note:
            has_notes = True
            latest_note_text = f"{format_local_ts(latest_note.get('ts',''))} — {latest_note.get('note','')}"

        with st.container():
            st.markdown("<div class='hm-rsd-mobile-card'>", unsafe_allow_html=True)
            rows = [
                ("Date", day_date or "—"),
                ("Meal type and food", meal_display_text),
                ("Water", day.get('water_litres') or '—'),
                ("Notes", day.get('notes') or '—'),
                ("Nutritionist Note", latest_note_text),
            ]
            for label, value in rows:
                lc, vc = st.columns([1.0, 2.2])
                lc.markdown(f"<div class='hm-rsd-mobile-label'>{label}</div>", unsafe_allow_html=True)
                vc.markdown(f"<div class='hm-rsd-mobile-value'>{value}</div>", unsafe_allow_html=True)

            action_lc, action_vc = st.columns([1.0, 2.2])
            action_lc.markdown("<div class='hm-rsd-mobile-label'>Action</div>", unsafe_allow_html=True)
            selected_date = st.session_state.get("selected_daily_note_history_date")
            button_label = "Hide history" if selected_date == day_date else "View history"
            with action_vc:
                if st.button(button_label, key=f"rsd_mobile_history_{day_date}", disabled=not has_notes):
                    if selected_date == day_date:
                        st.session_state["selected_daily_note_history_date"] = None
                    else:
                        st.session_state["selected_daily_note_history_date"] = day_date
                    st.rerun()

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