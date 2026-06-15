import streamlit as st
import html
import re
import datetime
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


# --------------------------------------------------------------------
# v97: Other Fluids helpers
# --------------------------------------------------------------------
def normalise_other_fluids_v97(items):
    cleaned = []
    for item in (items or []):
        if not isinstance(item, dict):
            continue
        fluid_type = str(item.get("type", "") or "").strip()
        time_text = str(item.get("time", "") or "").strip()
        quantity = str(item.get("quantity", "") or "").strip()
        notes = str(item.get("notes", "") or "").strip()
        if fluid_type or time_text or quantity or notes:
            cleaned.append({
                "type": fluid_type,
                "time": time_text,
                "quantity": quantity,
                "notes": notes,
            })
    return cleaned

def other_fluids_summary_v97(items):
    rows = []
    for idx, item in enumerate(normalise_other_fluids_v97(items), start=1):
        bits = []
        if item.get("time"):
            bits.append(item.get("time"))
        if item.get("type"):
            bits.append(item.get("type"))
        if item.get("quantity"):
            bits.append(item.get("quantity"))
        if item.get("notes"):
            bits.append(item.get("notes"))
        if bits:
            rows.append(f"{idx}. " + " · ".join(bits))
    return " | ".join(rows) if rows else "—"


def parse_date_safe_v97_3(value):
    try:
        return datetime.date.fromisoformat(str(value))
    except Exception:
        return None


def parse_date_safe_v97_9(value):
    try:
        return datetime.date.fromisoformat(str(value))
    except Exception:
        return None


def parse_date_safe_v97_10(value):
    try:
        return datetime.date.fromisoformat(str(value))
    except Exception:
        return None


# --------------------------------------------------------------------
# v97.12: Daily Log timing helper repair
# --------------------------------------------------------------------
STANDARD_MEAL_WINDOWS = {
    "breakfast": ("6 AM to 11 AM", 6 * 60, 11 * 60 + 59),
    "lunch": ("12 PM to 3 PM", 12 * 60, 15 * 60 + 59),
    "evening_snacks": ("4 PM to 6 PM", 16 * 60, 18 * 60 + 59),
    "dinner": ("7 PM to 10 PM", 19 * 60, 22 * 60 + 59),
    "bedtime": ("11 PM to 12 AM", 23 * 60, 24 * 60 + 59),
}

def split_12h_time_parts(time_text):
    raw = str(time_text or "").strip().upper()
    match = re.match(r"^\s*(\d{1,2})\s*[:.]\s*(\d{2})\s*(AM|PM)\s*$", raw)
    if not match:
        return "HH", "MM", "AM/PM"
    hour = int(match.group(1))
    minute = int(match.group(2))
    period = match.group(3)
    if hour < 1 or hour > 12 or minute < 0 or minute > 59:
        return "HH", "MM", "AM/PM"
    return f"{hour:02d}", f"{minute:02d}", period

def parse_12h_time_to_minutes(time_text):
    hour, minute, period = split_12h_time_parts(time_text)
    if hour == "HH" or minute == "MM" or period == "AM/PM":
        return None
    h = int(hour)
    m = int(minute)
    if period == "AM":
        h24 = 0 if h == 12 else h
    else:
        h24 = 12 if h == 12 else h + 12
    return h24 * 60 + m

def meal_window_key_for_section(section_key, section_label=""):
    key = str(section_key or "").lower()
    label = str(section_label or "").lower()
    if key.startswith("snacking_") or "snacking" in label:
        return "snacking"
    if key in STANDARD_MEAL_WINDOWS:
        return key
    if "breakfast" in label:
        return "breakfast"
    if "lunch" in label:
        return "lunch"
    if "snack" in label:
        return "evening_snacks"
    if "dinner" in label:
        return "dinner"
    if "bed" in label:
        return "bedtime"
    return "snacking"

def meal_time_selector_options_v97_2(section_key):
    window_key = meal_window_key_for_section(section_key)
    if window_key == "breakfast":
        return ["HH"] + [f"{h:02d}" for h in range(6, 12)], ["AM/PM", "AM"]
    if window_key == "lunch":
        return ["HH", "12", "01", "02", "03"], ["AM/PM", "PM"]
    if window_key == "evening_snacks":
        return ["HH", "04", "05", "06"], ["AM/PM", "PM"]
    if window_key == "dinner":
        return ["HH", "07", "08", "09", "10"], ["AM/PM", "PM"]
    if window_key == "bedtime":
        return ["HH", "11", "12"], ["AM/PM", "PM", "AM"]
    return ["HH"] + [f"{h:02d}" for h in range(1, 13)], ["AM/PM", "AM", "PM"]

def meal_time_guidance(section_key, section_label=""):
    window_key = meal_window_key_for_section(section_key, section_label)
    if window_key == "snacking":
        return "Snacking time should be outside Breakfast, Lunch, Evening Snacks, Dinner and Bedtime windows."
    label, _start, _end = STANDARD_MEAL_WINDOWS.get(window_key, ("standard meal window", 0, 24 * 60))
    return f"Allowed timing: {label}."

def validate_meal_time_window(section_key, time_text):
    window_key = meal_window_key_for_section(section_key)
    minutes = parse_12h_time_to_minutes(time_text)
    if minutes is None:
        return True
    if window_key == "snacking":
        for _label, start, end in STANDARD_MEAL_WINDOWS.values():
            if start <= minutes <= end:
                return False
        return True
    _label, start, end = STANDARD_MEAL_WINDOWS.get(window_key, ("", 0, 24 * 60))
    return start <= minutes <= end

def validate_meal_time(section_key, section_label, time_text):
    if not time_text:
        return True, ""
    if validate_meal_time_window(section_key, time_text):
        return True, ""
    window_key = meal_window_key_for_section(section_key, section_label)
    if window_key == "snacking":
        return False, "Snacking time must be outside the standard meal windows."
    label, _start, _end = STANDARD_MEAL_WINDOWS.get(window_key, ("the allowed meal window", 0, 0))
    return False, f"{section_label} time must be between {label}."

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
    
/* --- v91 Mobile-only Stepper Input Controls --- */
.hm-v91-stepper-label{
  margin-top:.15rem!important;
  margin-bottom:.16rem!important;
}
.hm-v91-stepper-shell{
  margin:.02rem 0 .35rem 0!important;
}
.hm-v91-stepper-value{
  min-height:1.82rem;
  display:flex;
  align-items:center;
  justify-content:center;
  border:1.25px solid #D9C399;
  background:#FFFDF8;
  border-radius:12px;
  color:#064E3B;
  font-size:.92rem;
  font-weight:900;
  box-shadow:0 3px 10px rgba(15,23,42,.035);
  white-space:nowrap;
}
.hm-v91-stepper-shell button{
  min-height:1.82rem!important;
  height:1.82rem!important;
  padding:0!important;
  font-size:1.05rem!important;
  line-height:1!important;
  border-radius:12px!important;
}
@media (max-width:768px){
  .hm-v91-stepper-value{
    min-height:1.68rem!important;
    font-size:.86rem!important;
    border-radius:10px!important;
  }
  .hm-v91-stepper-shell button{
    min-height:1.68rem!important;
    height:1.68rem!important;
    font-size:1rem!important;
    border-radius:10px!important;
  }
}


/* --- v91.2 Mobile Time + Horizontal Stepper Fix --- */
.hm-v912-horizontal-stepper-anchor{
  margin-top:-.05rem!important;
}
.hm-v912-horizontal-stepper-anchor + div[data-testid="stHorizontalBlock"]{
  display:grid!important;
  grid-template-columns:minmax(2.2rem,.75fr) minmax(4.2rem,1.35fr) minmax(2.2rem,.75fr)!important;
  gap:.35rem!important;
  align-items:center!important;
}
.hm-v912-horizontal-stepper-anchor + div[data-testid="stHorizontalBlock"] > div[data-testid="column"]{
  width:100%!important;
  min-width:0!important;
  flex:unset!important;
}
.hm-v912-horizontal-stepper-anchor + div[data-testid="stHorizontalBlock"] button{
  min-height:1.72rem!important;
  height:1.72rem!important;
  padding:0!important;
  font-size:1rem!important;
  border-radius:10px!important;
}
.hm-v912-horizontal-stepper-anchor + div[data-testid="stHorizontalBlock"] .hm-v91-stepper-value{
  min-height:1.72rem!important;
  height:1.72rem!important;
  font-size:.86rem!important;
  border-radius:10px!important;
}
@media (max-width:768px){
  .hm-v912-horizontal-stepper-anchor + div[data-testid="stHorizontalBlock"]{
    display:grid!important;
    grid-template-columns:2.25rem minmax(3.9rem,1fr) 2.25rem!important;
    gap:.28rem!important;
  }
  .hm-v912-horizontal-stepper-anchor + div[data-testid="stHorizontalBlock"] > div[data-testid="column"]{
    width:100%!important;
    flex:unset!important;
    min-width:0!important;
  }
}


/* --- v91.3 Mobile Control Stability Fix --- */
.hm-v91-stepper-label{
  margin-top:.15rem!important;
  margin-bottom:.12rem!important;
}
@media (max-width:768px){
  div[data-testid="stNumberInput"] input{
    min-height:2rem!important;
    height:2rem!important;
    font-size:.92rem!important;
    font-weight:800!important;
    color:#064E3B!important;
  }
  div[data-testid="stNumberInput"] button{
    min-height:2rem!important;
    height:2rem!important;
  }
}


/* --- v92 Number Input Look & Feel --- */
@media (max-width:768px){
  div[data-testid="stNumberInput"]{
    margin-bottom:.45rem!important;
  }
  div[data-testid="stNumberInput"] input{
    background:#FFFDF8!important;
    border:1.4px solid #D9C399!important;
    border-radius:14px!important;
    color:#064E3B!important;
    font-size:1rem!important;
    font-weight:900!important;
    text-align:center!important;
    min-height:2.35rem!important;
    box-shadow:0 4px 14px rgba(15,23,42,.045)!important;
  }
  div[data-testid="stNumberInput"] button{
    background:#FFFDF8!important;
    border:1.2px solid #D9C399!important;
    color:#064E3B!important;
    min-height:2.35rem!important;
  }
}


/* --- v92.1 Mobile Time Active + Number Button Size Fix --- */
@media (max-width:768px){
  div[data-testid="stNumberInput"]{
    margin-top:.05rem!important;
    margin-bottom:.65rem!important;
  }
  div[data-testid="stNumberInput"] input{
    min-height:2.65rem!important;
    height:2.65rem!important;
    font-size:1.08rem!important;
    font-weight:900!important;
    text-align:center!important;
    color:#064E3B!important;
    -webkit-text-fill-color:#064E3B!important;
    background:#FFFFFF!important;
    border:1.6px solid #D4A63A!important;
    border-radius:14px!important;
  }
  div[data-testid="stNumberInput"] button{
    min-width:2.65rem!important;
    min-height:2.65rem!important;
    height:2.65rem!important;
    font-size:1.45rem!important;
    font-weight:900!important;
    color:#064E3B!important;
    background:#FFFDF8!important;
    border:1.4px solid #D4A63A!important;
    border-radius:14px!important;
  }
  div[data-testid="stNumberInput"] button svg{
    width:1.2rem!important;
    height:1.2rem!important;
    stroke-width:3!important;
  }
}


/* --- v92.2 Component Rollback + Number Input Stability --- */
@media (max-width:768px){
  div[data-testid="stNumberInput"]{
    margin-top:.05rem!important;
    margin-bottom:.65rem!important;
  }
  div[data-testid="stNumberInput"] input{
    min-height:2.65rem!important;
    height:2.65rem!important;
    font-size:1.08rem!important;
    font-weight:900!important;
    text-align:center!important;
    color:#064E3B!important;
    -webkit-text-fill-color:#064E3B!important;
    background:#FFFFFF!important;
    border:1.6px solid #D4A63A!important;
    border-radius:14px!important;
  }
  div[data-testid="stNumberInput"] button{
    min-width:2.65rem!important;
    min-height:2.65rem!important;
    height:2.65rem!important;
    font-size:1.45rem!important;
    font-weight:900!important;
    color:#064E3B!important;
    background:#FFFDF8!important;
    border:1.4px solid #D4A63A!important;
    border-radius:14px!important;
  }
}


/* --- v92.3 Input Styling Alignment --- */
.hm-compact-section-note{
  color:#064E3B!important;
  font-weight:850!important;
}
@media (max-width:768px){
  /* Match Meal Timing selectboxes to Water/Poop number input schema */
  div[data-testid="stSelectbox"]{
    margin-bottom:.4rem!important;
  }
  div[data-testid="stSelectbox"] [data-baseweb="select"] > div{
    min-height:2.65rem!important;
    height:2.65rem!important;
    background:#FFFFFF!important;
    border:1.6px solid #D4A63A!important;
    border-radius:14px!important;
    box-shadow:0 4px 14px rgba(15,23,42,.045)!important;
  }
  div[data-testid="stSelectbox"] [data-baseweb="select"] div{
    color:#064E3B!important;
    font-weight:900!important;
    font-size:1rem!important;
  }
  div[data-testid="stSelectbox"] svg{
    color:#064E3B!important;
    fill:#064E3B!important;
  }

  /* Keep Water/Poop number input aligned to same schema */
  div[data-testid="stNumberInput"]{
    margin-top:.05rem!important;
    margin-bottom:.65rem!important;
  }
  div[data-testid="stNumberInput"] input{
    min-height:2.65rem!important;
    height:2.65rem!important;
    font-size:1.08rem!important;
    font-weight:900!important;
    text-align:center!important;
    color:#064E3B!important;
    -webkit-text-fill-color:#064E3B!important;
    background:#FFFFFF!important;
    border:1.6px solid #D4A63A!important;
    border-radius:14px!important;
    box-shadow:0 4px 14px rgba(15,23,42,.045)!important;
  }
  div[data-testid="stNumberInput"] button{
    min-width:2.65rem!important;
    min-height:2.65rem!important;
    height:2.65rem!important;
    font-size:1.45rem!important;
    font-weight:900!important;
    color:#064E3B!important;
    background:#FFFDF8!important;
    border:1.4px solid #D4A63A!important;
    border-radius:14px!important;
  }

  .hm-full-day-helper,
  .hm-time-preview{
    color:#064E3B!important;
  }
}


/* --- v92.4 Input Format Schema Alignment --- */
.hm-schema-input-band{
  border:1.4px solid #E2C98F;
  background:linear-gradient(180deg,#FFFDF8 0%,#FFF9ED 100%);
  border-radius:16px;
  padding:.72rem .78rem .62rem .78rem;
  margin:.35rem 0 .75rem 0;
  box-shadow:0 6px 18px rgba(15,23,42,.045);
}
.hm-schema-input-label{
  color:#064E3B;
  font-size:.84rem;
  font-weight:900;
  line-height:1.15;
  margin:0 0 .4rem 0;
}
.hm-schema-input-band .hm-compact-section-note{
  color:#064E3B!important;
  font-weight:900!important;
  margin-bottom:.36rem!important;
}
.hm-schema-input-band div[data-testid="stSelectbox"],
.hm-schema-input-band div[data-testid="stNumberInput"]{
  margin-bottom:0!important;
}
.hm-schema-input-band div[data-testid="stSelectbox"] [data-baseweb="select"] > div{
  min-height:2.42rem!important;
  height:2.42rem!important;
  background:#FFFFFF!important;
  border:1.45px solid #D4A63A!important;
  border-radius:13px!important;
  box-shadow:0 3px 12px rgba(15,23,42,.04)!important;
}
.hm-schema-input-band div[data-testid="stSelectbox"] [data-baseweb="select"] div{
  color:#064E3B!important;
  font-weight:850!important;
  font-size:.92rem!important;
}
.hm-schema-input-band div[data-testid="stSelectbox"] svg{
  color:#064E3B!important;
  fill:#064E3B!important;
}
.hm-schema-input-band div[data-testid="stNumberInput"] input{
  min-height:2.42rem!important;
  height:2.42rem!important;
  background:#FFFFFF!important;
  border:1.45px solid #D4A63A!important;
  border-radius:13px!important;
  color:#064E3B!important;
  -webkit-text-fill-color:#064E3B!important;
  font-size:.98rem!important;
  font-weight:900!important;
  text-align:center!important;
  box-shadow:0 3px 12px rgba(15,23,42,.04)!important;
}
.hm-schema-input-band div[data-testid="stNumberInput"] button{
  min-height:2.42rem!important;
  height:2.42rem!important;
  min-width:2.42rem!important;
  background:#FFFDF8!important;
  border:1.35px solid #D4A63A!important;
  border-radius:13px!important;
  color:#064E3B!important;
}
.hm-schema-input-band div[data-testid="stNumberInput"] button svg{
  width:1.1rem!important;
  height:1.1rem!important;
  stroke-width:3!important;
}
.hm-schema-input-band .hm-full-day-helper{
  color:#6B7280!important;
  font-size:.78rem!important;
  line-height:1.2!important;
  margin-top:.35rem!important;
}
@media (max-width:768px){
  .hm-schema-input-band{
    padding:.62rem .64rem .58rem .64rem!important;
    border-radius:15px!important;
    margin:.28rem 0 .62rem 0!important;
  }
  .hm-schema-input-label{
    font-size:.8rem!important;
    margin-bottom:.32rem!important;
  }
  .hm-schema-input-band div[data-testid="stSelectbox"] [data-baseweb="select"] > div,
  .hm-schema-input-band div[data-testid="stNumberInput"] input,
  .hm-schema-input-band div[data-testid="stNumberInput"] button{
    min-height:2.28rem!important;
    height:2.28rem!important;
    border-radius:12px!important;
  }
  .hm-schema-input-band div[data-testid="stSelectbox"] [data-baseweb="select"] div{
    font-size:.86rem!important;
  }
  .hm-schema-input-band div[data-testid="stNumberInput"] input{
    font-size:.92rem!important;
  }
}


/* --- v92.5 Daily Log Input Schema Repair --- */
.hm-compact-section-note,
.hm-v90a-chip-label,
label[data-testid="stWidgetLabel"]{
  color:#064E3B!important;
  font-weight:850!important;
}
div[data-testid="stSelectbox"] [data-baseweb="select"] > div,
div[data-testid="stNumberInput"] input{
  background:#FFFFFF!important;
  border:1.45px solid #D4A63A!important;
  border-radius:13px!important;
  color:#064E3B!important;
  -webkit-text-fill-color:#064E3B!important;
  font-weight:850!important;
  min-height:2.42rem!important;
  height:2.42rem!important;
  box-shadow:0 3px 12px rgba(15,23,42,.04)!important;
}
div[data-testid="stSelectbox"] [data-baseweb="select"] div{
  color:#064E3B!important;
  font-weight:850!important;
}
div[data-testid="stSelectbox"] svg{
  color:#064E3B!important;
  fill:#064E3B!important;
}
div[data-testid="stNumberInput"] input{
  text-align:center!important;
  font-size:.98rem!important;
}
div[data-testid="stNumberInput"] button{
  min-height:2.42rem!important;
  height:2.42rem!important;
  min-width:2.42rem!important;
  background:#FFFDF8!important;
  border:1.35px solid #D4A63A!important;
  border-radius:13px!important;
  color:#064E3B!important;
}
div[data-testid="stNumberInput"] button svg{
  width:1.1rem!important;
  height:1.1rem!important;
  stroke-width:3!important;
}
div[data-testid="stTextArea"] textarea,
div[data-testid="stTextInput"] input{
  background:#F3F6FA!important;
  border:1.2px solid transparent!important;
  border-radius:10px!important;
  color:#102A43!important;
}
@media (max-width:768px){
  div[data-testid="stSelectbox"] [data-baseweb="select"] > div,
  div[data-testid="stNumberInput"] input,
  div[data-testid="stNumberInput"] button{
    min-height:2.28rem!important;
    height:2.28rem!important;
    border-radius:12px!important;
  }
  div[data-testid="stSelectbox"] [data-baseweb="select"] div{
    font-size:.86rem!important;
  }
  div[data-testid="stNumberInput"] input{
    font-size:.92rem!important;
  }
  div[data-testid="stTextArea"] textarea{
    min-height:5.2rem!important;
  }
}

</style>
    """,
    unsafe_allow_html=True,
)


# v97.10 consolidated Daily Log CSS placed before header to avoid top-gap
st.markdown("""
<style>
/* v97.10 Daily Log header-gap and recent-filter hard fix */
.block-container{padding-top:.55rem!important;}
.hero-shell.hm-compact-page-section,
.hero-shell{
  margin-bottom:.45rem!important;
}
.hm-v9710-date-wrap{
  margin:0 0 .45rem 0!important;
  padding:0!important;
}
.hm-v9710-date-left{
  display:flex;
  align-items:center;
  gap:.55rem;
  min-height:2.1rem;
  flex-wrap:wrap;
}
.hm-v9710-date-label{
  color:#064E3B;
  font-weight:950;
  font-size:1.12rem;
  line-height:1.05;
}
.hm-v9710-date-help{
  color:#64748B;
  font-size:.82rem;
  line-height:1.12;
}
.hm-v9710-date-wrap div[data-testid="stDateInput"] input{
  min-height:2.12rem!important;
  height:2.12rem!important;
  border-radius:12px!important;
  border:1.15px solid #DCC690!important;
  background:#F4F7FB!important;
}
/* Keep approved subtle dropdown style */
div[data-testid="stSelectbox"] [data-baseweb="select"] > div{
  background:#FFFDF8!important;
  border:1.15px solid #DCC690!important;
  border-radius:12px!important;
  min-height:2.28rem!important;
  height:2.28rem!important;
  box-shadow:0 2px 8px rgba(15,23,42,.025)!important;
}
div[data-testid="stSelectbox"] [data-baseweb="select"] div{
  color:#064E3B!important;
  font-weight:760!important;
  font-size:.88rem!important;
}
div[data-testid="stSelectbox"] svg{color:#0F766E!important;fill:#0F766E!important;}
div[data-testid="stTextInput"] input{min-height:2.28rem!important;height:2.28rem!important;border-radius:12px!important;}
/* Other fluids spacing retained */
.hm-v977-fluid-entry{padding:.48rem 0 .58rem 0;margin:.18rem 0 .42rem 0;}
.hm-v977-fluid-title{color:#064E3B;font-weight:950;font-size:.98rem;margin:.22rem 0 .48rem 0;}
.hm-v977-field-label{color:#334155;font-size:.82rem;font-weight:780;line-height:1.05;margin:0 0 .28rem 0;}
.hm-v977-row2{margin-top:.34rem;}
.hm-v979-recent-filter,.hm-v9710-recent-filter{
  border:1px solid #E2C98F;
  border-radius:14px;
  background:#FFFDF8;
  padding:.58rem .7rem .18rem .7rem;
  margin:.35rem 0 .72rem 0;
  box-shadow:0 4px 12px rgba(15,23,42,.025);
}
.hm-v979-recent-filter-title,.hm-v9710-recent-filter-title{color:#064E3B;font-weight:900;font-size:.9rem;margin-bottom:.32rem;}
@media (max-width:768px){
  .hero-shell{margin-bottom:.35rem!important;}
  .hm-v9710-date-left{align-items:flex-start!important;min-height:auto!important;gap:.28rem!important;}
  .hm-v9710-date-label{font-size:1.02rem!important;}
  .hm-v9710-date-help{font-size:.78rem!important;}
  div[data-testid="stSelectbox"] [data-baseweb="select"] > div,
  div[data-testid="stTextInput"] input,
  .hm-v9710-date-wrap div[data-testid="stDateInput"] input{min-height:2.18rem!important;height:2.18rem!important;}
}
</style>
""", unsafe_allow_html=True)

user_id = st.session_state["user_id"]

st.markdown("""
<style>
/* v97.12 hard reduction of header-to-date whitespace */
.hero-shell.hm-compact-page-section,
.hero-shell{
  margin-bottom:.10rem!important;
}
.hm-v9710-date-wrap,
.hm-v978-date-wrap{
  margin-top:-3.15rem!important;
  margin-bottom:.38rem!important;
  padding-top:0!important;
}
.hm-v9710-date-left,
.hm-v978-date-left{
  min-height:2.0rem!important;
  align-items:center!important;
}
.hm-v9710-date-label,
.hm-v978-date-label{
  font-size:1.14rem!important;
  line-height:1.05!important;
}
.hm-v9710-date-help,
.hm-v978-date-help{
  font-size:.82rem!important;
  line-height:1.1!important;
}
@media (max-width:768px){
  .hm-v9710-date-wrap,
  .hm-v978-date-wrap{
    margin-top:-2.0rem!important;
  }
}
</style>
""", unsafe_allow_html=True)

compact_topbar("Daily Food Journal", "Save meals progressively through the day, or complete the full day together.", "Member tracker")
render_system_message()

# Fixed Daily Log meal structure.
st.markdown("<div class='hm-v9710-date-wrap'>", unsafe_allow_html=True)
date_label_col, date_picker_col = st.columns([1.35, 1.65])
with date_label_col:
    st.markdown("<div class='hm-v9710-date-left'><div class='hm-v9710-date-label'>Food Journal Date</div><div class='hm-v9710-date-help'>Select the date for this food journal entry.</div></div>", unsafe_allow_html=True)
with date_picker_col:
    log_date = st.date_input("Food Journal Date", value=date.today(), label_visibility="collapsed")
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

# --------------------------------------------------------------------
# v97.11: Meal helper hotfix
# --------------------------------------------------------------------

def current_widget_payload(active_key, active_label):
    hour = st.session_state.get(f"{active_key}_time_h", "HH")
    minute = st.session_state.get(f"{active_key}_time_m", "MM")
    period = st.session_state.get(f"{active_key}_time_p", "AM/PM")
    meal_time = f"{hour}:{minute} {period}" if hour != "HH" and minute != "MM" and period in ["AM", "PM"] else ""
    return {
        "label": active_label,
        "time": meal_time,
        "food": st.session_state.get(f"{active_key}_food", ""),
        "portion_size": st.session_state.get(f"{active_key}_portion", ""),
        "mood_energy": st.session_state.get(f"{active_key}_mood", ""),
    }

def meal_has_data(meal):
    """Return True when a saved meal section contains any meaningful user entry."""
    if not isinstance(meal, dict):
        return False
    fields = ["time", "food", "portion_size", "mood_energy", "notes", "meal_type", "label"]
    for field in fields:
        value = meal.get(field)
        if value is not None and str(value).strip():
            return True
    return False

def is_dirty(existing_meals, active_key, active_label):
    """Detect unsaved changes in the active meal section without breaking page render."""
    try:
        existing = existing_meals.get(active_key, {}) if isinstance(existing_meals, dict) else {}
        current = current_widget_payload(active_key, active_label)
        if not meal_has_data(current) and not meal_has_data(existing):
            return False
        check_fields = ["time", "food", "portion_size", "mood_energy"]
        for field in check_fields:
            if str(current.get(field, "") or "").strip() != str(existing.get(field, "") or "").strip():
                return True
        return False
    except Exception:
        return False

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
meal_hour_options, meal_ampm_options = meal_time_selector_options_v97_2(active_key)
if is_mobile_mode_v90a:
    # v92.2: Custom component removed because it fails to load on Streamlit Cloud.
    # Use safe Streamlit-native 3-cell timing controls while keeping validation active.
    th, tm, tp = st.columns([1, 1, 1])
    with th:
        hour_options = meal_hour_options
        current_h = st.session_state.get(f"{active_key}_time_h", pre_h)
        if current_h not in hour_options:
            st.session_state[f"{active_key}_time_h"] = "HH"
            current_h = "HH"
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
        ampm_options = meal_ampm_options
        current_p = st.session_state.get(f"{active_key}_time_p", pre_p)
        if current_p not in ampm_options:
            st.session_state[f"{active_key}_time_p"] = "AM/PM"
            current_p = "AM/PM"
        st.selectbox(
            "AM/PM",
            ampm_options,
            index=ampm_options.index(current_p) if current_p in ampm_options else 0,
            key=f"{active_key}_time_p",
            label_visibility="collapsed",
        )
else:
    th, tm, tp = st.columns([1, 1, 1])
    with th:
        hour_options = meal_hour_options
        current_h = st.session_state.get(f"{active_key}_time_h", pre_h)
        if current_h not in hour_options:
            st.session_state[f"{active_key}_time_h"] = "HH"
            current_h = "HH"
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
        ampm_options = meal_ampm_options
        current_p = st.session_state.get(f"{active_key}_time_p", pre_p)
        if current_p not in ampm_options:
            st.session_state[f"{active_key}_time_p"] = "AM/PM"
            current_p = "AM/PM"
        st.selectbox(
            "AM/PM",
            ampm_options,
            index=ampm_options.index(current_p) if current_p in ampm_options else 0,
            key=f"{active_key}_time_p",
            label_visibility="collapsed",
        )
st.markdown(f"<div class='hm-full-day-helper'>{time_guidance}</div>", unsafe_allow_html=True)

selected_meal_time_for_validation = f"{st.session_state.get(f'{active_key}_time_h', 'HH')}:{st.session_state.get(f'{active_key}_time_m', 'MM')} {st.session_state.get(f'{active_key}_time_p', 'AM/PM')}"
if selected_meal_time_for_validation and "HH" not in selected_meal_time_for_validation and "MM" not in selected_meal_time_for_validation and "AM/PM" not in selected_meal_time_for_validation:
    if not validate_meal_time_window(active_key, selected_meal_time_for_validation):
        st.warning(f"{active_label} timing is outside the allowed window. {time_guidance}")


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
    existing_water = existing.get("water_litres", "Select") or "Select"
    if is_mobile_mode_v90a:
        water_value_map = {
            "Select": 0,
            "0 Litres": 0,
            "0.5 Litres": 0.5,
            "1 Litre": 1,
            "1.5 Litres": 1.5,
            "2 Litres": 2,
            "2.5 Litres": 2.5,
            "3 Litres": 3,
            "3.5 Litres": 3.5,
            "4 Litres": 4,
            "4.5 Litres": 4.5,
            "5 Litres": 5,
            "5.5 Litres": 5.5,
            "6 Litres": 6,
            "6.5 Litres": 6.5,
            "7 Litres": 7,
            "7.5 Litres": 7.5,
            "8 Litres": 8,
            "8.5 Litres": 8.5,
            "9 Litres": 9,
            "9.5 Litres": 9.5,
            "10 Litres": 10,
        }
        starting_water_value = water_value_map.get(existing_water, 0)
        selected_water_value = render_v91_stepper(
            "Water intake for the full day",
            starting_water_value,
            "v91_mobile_water_litres",
            0,
            10,
            0.5,
            " L",
            as_int=False,
        )
        water_litres = water_stepper_to_litres(selected_water_value)
    else:
        water_litres = st.selectbox(
            "Water intake for the full day",
            water_options,
            index=water_options.index(existing_water) if existing_water in water_options else 0,
        )
with top_right:
    existing_other_fluids = normalise_other_fluids_v97(existing.get("other_fluids", []) or [])
    default_other_count = min(max(len(existing_other_fluids), 0), 5)
    other_count_options = [0, 1, 2, 3, 4, 5]
    other_fluid_count_key = f"other_fluid_count_{log_date}"
    if other_fluid_count_key not in st.session_state:
        st.session_state[other_fluid_count_key] = default_other_count
    st.selectbox(
        "Other Fluids consumed outside standard meal window",
        other_count_options,
        index=other_count_options.index(st.session_state.get(other_fluid_count_key, default_other_count)) if st.session_state.get(other_fluid_count_key, default_other_count) in other_count_options else 0,
        key=other_fluid_count_key,
    )
    other_fluid_count = int(st.session_state.get(other_fluid_count_key, 0) or 0)



st.markdown("""
<style>
/* v97.7 Other Fluids no-border compact width fix */
.hm-v977-fluid-entry{
  padding:.48rem 0 .58rem 0;
  margin:.18rem 0 .42rem 0;
}
.hm-v977-fluid-title{
  color:#064E3B;
  font-weight:950;
  font-size:.98rem;
  margin:.22rem 0 .48rem 0;
}
.hm-v977-field-label{
  color:#334155;
  font-size:.82rem;
  font-weight:780;
  line-height:1.05;
  margin:0 0 .28rem 0;
}
.hm-v977-row2{
  margin-top:.34rem;
}
.hm-v977-fluid-entry div[data-testid="stSelectbox"],
.hm-v977-fluid-entry div[data-testid="stTextInput"]{
  margin-bottom:0!important;
}
.hm-v977-fluid-entry div[data-testid="stSelectbox"] [data-baseweb="select"] > div{
  background:#FFFDF8!important;
  border:1.15px solid #DCC690!important;
  border-radius:12px!important;
  min-height:2.28rem!important;
  height:2.28rem!important;
  box-shadow:0 2px 8px rgba(15,23,42,.025)!important;
}
.hm-v977-fluid-entry div[data-testid="stTextInput"] input{
  min-height:2.28rem!important;
  height:2.28rem!important;
  border-radius:12px!important;
}
@media (max-width:768px){
  .hm-v977-fluid-entry{
    padding:.36rem 0 .46rem 0!important;
  }
  .hm-v977-fluid-entry div[data-testid="stSelectbox"] [data-baseweb="select"] > div,
  .hm-v977-fluid-entry div[data-testid="stTextInput"] input{
    min-height:2.18rem!important;
    height:2.18rem!important;
  }
}
</style>
""", unsafe_allow_html=True)

# v97: Other Fluids outside standard meal windows
other_fluids = []
fluid_type_options = ["Select", "Herbal Tea", "Coconut Water", "Juice", "Cold Drink", "Tea / Coffee", "Buttermilk", "Other"]

for i in range(other_fluid_count):
    prior_fluid = existing_other_fluids[i] if i < len(existing_other_fluids) else {}
    pre_h, pre_m, pre_p = split_12h_time_parts(prior_fluid.get("time", ""))
    st.session_state.setdefault(f"other_fluid_h_{log_date}_{i}", pre_h)
    st.session_state.setdefault(f"other_fluid_m_{log_date}_{i}", pre_m)
    st.session_state.setdefault(f"other_fluid_p_{log_date}_{i}", pre_p)

    st.markdown("<div class='hm-v977-fluid-entry'>", unsafe_allow_html=True)
    st.markdown(f"<div class='hm-v977-fluid-title'>Other Fluid {i+1}</div>", unsafe_allow_html=True)

    # Row 1: Fluid type reduced materially; Meal Timing remains beside it.
    fluid_type_col, timing_col, empty_col = st.columns([0.72, 1.62, 0.50], gap="medium")

    with fluid_type_col:
        st.markdown("<div class='hm-v977-field-label'>Fluid type</div>", unsafe_allow_html=True)
        existing_type = prior_fluid.get("type", "Select") or "Select"
        fluid_type = st.selectbox(
            "Fluid type",
            fluid_type_options,
            index=fluid_type_options.index(existing_type) if existing_type in fluid_type_options else 0,
            key=f"other_fluid_type_{log_date}_{i}",
            label_visibility="collapsed",
        )

    with timing_col:
        st.markdown("<div class='hm-v977-field-label'>Meal Timing</div>", unsafe_allow_html=True)
        h_col, m_col, p_col = st.columns([0.55, 0.55, 0.90], gap="small")
        with h_col:
            hour_options = ["HH"] + [f"{n:02d}" for n in range(1, 13)]
            current_h = st.session_state.get(f"other_fluid_h_{log_date}_{i}", pre_h)
            st.selectbox(
                "HH",
                hour_options,
                index=hour_options.index(current_h) if current_h in hour_options else 0,
                key=f"other_fluid_h_{log_date}_{i}",
                label_visibility="collapsed",
            )
        with m_col:
            minute_options = ["MM"] + [f"{n:02d}" for n in range(0, 60)]
            current_m = st.session_state.get(f"other_fluid_m_{log_date}_{i}", pre_m)
            st.selectbox(
                "MM",
                minute_options,
                index=minute_options.index(current_m) if current_m in minute_options else 0,
                key=f"other_fluid_m_{log_date}_{i}",
                label_visibility="collapsed",
            )
        with p_col:
            ampm_options = ["AM/PM", "AM", "PM"]
            current_p = st.session_state.get(f"other_fluid_p_{log_date}_{i}", pre_p)
            st.selectbox(
                "AM/PM",
                ampm_options,
                index=ampm_options.index(current_p) if current_p in ampm_options else 0,
                key=f"other_fluid_p_{log_date}_{i}",
                label_visibility="collapsed",
            )

    # Row 2: Quantity and Notes together.
    st.markdown("<div class='hm-v977-row2'></div>", unsafe_allow_html=True)
    qty_col, notes_col = st.columns([0.72, 2.12], gap="medium")
    with qty_col:
        st.markdown("<div class='hm-v977-field-label'>Quantity</div>", unsafe_allow_html=True)
        fluid_qty = st.text_input(
            "Quantity",
            value=prior_fluid.get("quantity", ""),
            placeholder="Example: 200 ml",
            key=f"other_fluid_qty_{log_date}_{i}",
            label_visibility="collapsed",
        )
    with notes_col:
        st.markdown("<div class='hm-v977-field-label'>Notes</div>", unsafe_allow_html=True)
        fluid_notes = st.text_input(
            "Notes",
            value=prior_fluid.get("notes", ""),
            placeholder="Example: unsweetened / with sugar / packaged",
            key=f"other_fluid_notes_{log_date}_{i}",
            label_visibility="collapsed",
        )

    st.markdown("</div>", unsafe_allow_html=True)

    type_value = "" if fluid_type == "Select" else fluid_type
    hour_value = st.session_state.get(f"other_fluid_h_{log_date}_{i}", "HH")
    minute_value = st.session_state.get(f"other_fluid_m_{log_date}_{i}", "MM")
    period_value = st.session_state.get(f"other_fluid_p_{log_date}_{i}", "AM/PM")
    fluid_time = f"{hour_value}:{minute_value} {period_value}" if hour_value != "HH" and minute_value != "MM" and period_value in ["AM", "PM"] else ""
    if type_value or fluid_time.strip() or fluid_qty.strip() or fluid_notes.strip():
        other_fluids.append({
            "type": type_value,
            "time": fluid_time.strip(),
            "quantity": fluid_qty.strip(),
            "notes": fluid_notes.strip(),
        })

poop_options = ["Select", 0, 1, 2, 3, 4, 5, 6]
existing_poop_rounds = existing.get("poop_rounds", "Select")
if existing_poop_rounds in ("", None):
    existing_poop_rounds = "Select"
if str(existing_poop_rounds).isdigit():
    existing_poop_rounds = int(existing_poop_rounds)
if is_mobile_mode_v90a:
    starting_poop_rounds = existing_poop_rounds if isinstance(existing_poop_rounds, int) else 0
    poop_rounds = render_v91_stepper(
        "Poop rounds",
        starting_poop_rounds,
        "v91_mobile_poop_rounds",
        0,
        6,
        1,
        "",
        as_int=True,
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
    feeling_after_poop = st.text_area(
        "Feeling after poop",
        value=existing.get("feeling_after_poop", ""),
        placeholder="Example: relieved / constipated / bloated / loose stool / incomplete",
        height=88,
    )
with phys_col:
    physical_activity = st.text_area(
        "Physical activity - time of day and duration",
        value=existing.get("physical_activity", ""),
        placeholder="Example: Walk 30 mins at 7 AM / strength training 1 PM - 2 PM",
        height=88,
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
        save_daily_food_journal_day_details(user_id, str(log_date), physical_activity.strip(), poop, day_notes.strip(), water_litres, poop_rounds, poop_timings, feeling_after_poop.strip(), other_fluids)
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
            "other_fluids": other_fluids,
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

# v97.10 visible From / To filter for Recent Saved Days
recent_saved_dates_v97_10 = sorted([d for d in [parse_date_safe_v97_10(x.get("date")) for x in days] if d], reverse=True)
if recent_saved_dates_v97_10:
    st.markdown("<div class='hm-v9710-recent-filter'><div class='hm-v9710-recent-filter-title'>Filter Recent Saved Days</div>", unsafe_allow_html=True)
    rf1, rf2 = st.columns(2)
    with rf1:
        recent_from_v97_10 = st.date_input("From date", value=min(recent_saved_dates_v97_10), key="v97_10_recent_filter_from")
    with rf2:
        recent_to_v97_10 = st.date_input("To date", value=max(recent_saved_dates_v97_10), key="v97_10_recent_filter_to")
    st.markdown("</div>", unsafe_allow_html=True)
    days = [
        x for x in days
        if parse_date_safe_v97_10(x.get("date")) and recent_from_v97_10 <= parse_date_safe_v97_10(x.get("date")) <= recent_to_v97_10
    ]
else:
    # Keep the controls visible even if no saved rows exist yet.
    st.markdown("<div class='hm-v9710-recent-filter'><div class='hm-v9710-recent-filter-title'>Filter Recent Saved Days</div>", unsafe_allow_html=True)
    rf1, rf2 = st.columns(2)
    with rf1:
        st.date_input("From date", value=date.today(), key="v97_10_recent_filter_from_empty")
    with rf2:
        st.date_input("To date", value=date.today(), key="v97_10_recent_filter_to_empty")
    st.markdown("</div>", unsafe_allow_html=True)

if not days:
    st.info("No food journal days saved yet.")
else:



    # v97.11 From / To filter for Recent Saved Days
    available_saved_dates_v97_11 = sorted([d for d in [parse_date_safe_v97_10(x.get("date")) for x in days] if d], reverse=True)
    st.markdown("<div class='hm-v979-recent-filter'><div class='hm-v979-recent-filter-title'>Filter Recent Saved Days</div>", unsafe_allow_html=True)
    if available_saved_dates_v97_11:
        rf1, rf2 = st.columns(2)
        with rf1:
            recent_from_v97_11 = st.date_input("From date", value=min(available_saved_dates_v97_11), key="v97_11_recent_filter_from")
        with rf2:
            recent_to_v97_11 = st.date_input("To date", value=max(available_saved_dates_v97_11), key="v97_11_recent_filter_to")
        days = [
            x for x in days
            if parse_date_safe_v97_10(x.get("date")) and recent_from_v97_11 <= parse_date_safe_v97_10(x.get("date")) <= recent_to_v97_11
        ]
    else:
        rf1, rf2 = st.columns(2)
        with rf1:
            st.date_input("From date", value=date.today(), key="v97_11_recent_filter_from_empty")
        with rf2:
            st.date_input("To date", value=date.today(), key="v97_11_recent_filter_to_empty")
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div class='hm-rsd-mobile-shell'>", unsafe_allow_html=True)

    for day in days:
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
                ("Other Fluids", other_fluids_summary_v97(day.get("other_fluids", []))),
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
            card_end()


# Reference moved to bottom, with more aesthetic and compact expander.
SAMPLE_ROWS = [
    {"Time": "10:00 - 10:30 AM", "Meal Type": "Breakfast", "Food": "Boiled eggs / omelet / moong dal chilla / poha", "Portion Size": "2 eggs / 2 chilla / 1 bowl poha", "Mood/Energy": "Fresh", "Activity": "1 PM - 2 PM", "Poop": "2-3 times / felt relieved", "Notes": "Mention exact items."},
    {"Time": "2:30 - 2:45 PM", "Meal Type": "Lunch", "Food": "Dal + rice / roti + salad + curd + sabzi", "Portion Size": "100 ml rice + 100 ml dal", "Mood/Energy": "Energetic", "Activity": "", "Poop": "", "Notes": ""},
    {"Time": "5:00 - 5:30 PM", "Meal Type": "Evening Snack", "Food": "Half cup tea with snack", "Portion Size": "", "Mood/Energy": "Okay", "Activity": "", "Poop": "", "Notes": ""},
    {"Time": "7:30 - 8:00 PM", "Meal Type": "Dinner", "Food": "Soup / light dinner", "Portion Size": "1 big bowl", "Mood/Energy": "Energetic", "Activity": "", "Poop": "", "Notes": ""},
]

if "show_daily_reference_sample" not in st.session_state:
    st.session_state["show_daily_reference_sample"] = False
if st.button("Show / Hide sample journal format", use_container_width=True):
    st.session_state["show_daily_reference_sample"] = not st.session_state["show_daily_reference_sample"]
if st.session_state["show_daily_reference_sample"]:
    st.dataframe(SAMPLE_ROWS, use_container_width=True, hide_index=True)

if st.button("Back to Home", use_container_width=True):
    st.switch_page("pages/02_Member_Home.py")