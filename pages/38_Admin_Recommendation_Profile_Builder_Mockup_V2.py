import datetime as dt
import re

import streamlit as st

from components.guards import require_admin
from components.recommendation_profile_store import (
    check_profile_builder_store,
    list_draft_profiles,
    list_profile_sources,
    load_member_options,
    load_profile,
    load_profile_builder_sources,
    save_draft_profile,
)
from components.ui_common import (
    apply_luxe_theme,
    inject_global_styles,
    render_back_to_top,
    render_page_nav,
    utility_logout_bar,
)

APP_BUILD_VERSION = "v100.30"
APP_BUILD_LABEL = "Profile Builder V2 Row-Based Regime"
SCHEDULE_SCHEMA_VERSION = "h9a7g_v100_30"

MEAL_SLOTS = [
    "Wake-up / Early Morning",
    "Breakfast",
    "Mid-morning Snack",
    "Lunch",
    "Evening Snack / Tea",
    "Dinner",
    "Bedtime",
]
EXERCISE_TIME_OF_DAY = ["Morning", "Afternoon", "Evening", "Night / As advised"]
SUPPLEMENT_TIMELINE = [
    "Before Breakfast",
    "After Breakfast",
    "Before Lunch",
    "After Lunch",
    "Before Dinner",
    "After Dinner",
    "Before Bed",
]
EXERCISE_ROW_SLOT = "Exercise Regime"
SUPPLEMENT_ROW_SLOT = "Supplement Regime"
SLOTS_BY_KIND = {
    "meal": MEAL_SLOTS,
    "exercise": [EXERCISE_ROW_SLOT],
    "supplement": [SUPPLEMENT_ROW_SLOT],
}

SECTIONS = [
    "Profile Setup",
    "Meal Structure",
    "Exercise Regime",
    "Supplement Regime",
    "Preview & End-to-End Flow",
]
NAV_LABELS = {
    "Profile Setup": "Profile Setup",
    "Meal Structure": "Meal Structure",
    "Exercise Regime": "Exercise Regime",
    "Supplement Regime": "Supplement Regime",
    "Preview & End-to-End Flow": "Preview & Flow",
}

SELECT_AGE = "-- Select age band --"
SELECT_DIET = "-- Select diet type --"
SELECT_INTENSITY = "-- Select intensity --"
SELECT_RECIPE = "-- Select recipe --"
SELECT_EXERCISE = "-- Select exercise --"
SELECT_SUPPLEMENT = "-- Select supplement --"
SELECT_DRAFT = "-- Select saved draft --"
SELECT_MEMBER = "Select member"

PROFILE_DEFAULTS = {
    "id": "",
    "profile_name": "",
    "clone_from": "New profile",
    "change_note": "",
    "status": "Draft",
    "region": "",
    "age_band": SELECT_AGE,
    "concerns": [],
    "diet_type": SELECT_DIET,
    "member": SELECT_MEMBER,
    "note": "",
    "start_date": dt.date.today(),
}


def safe_key(value: object) -> str:
    return re.sub(r"[^A-Za-z0-9]+", "_", str(value or "")).strip("_") or "blank"


def clear_schedule_state(force: bool = False) -> None:
    if not force and st.session_state.get("pb_schedule_schema_version") == SCHEDULE_SCHEMA_VERSION:
        return
    stale_prefixes = (
        "pbw_meal_",
        "pbw_exercise_",
        "pbw_supplement_",
        "add_meal_",
        "add_exercise_",
        "add_supplement_",
    )
    stale_keys = {
        "pb_items",
        "pb_row_counts",
        "pb_unsupported_items",
        "v4_meal_day",
        "v4_exercise_day",
        "v4_supp_day",
        "v4_preview_day",
    }
    for key in list(st.session_state.keys()):
        if key in stale_keys or str(key).startswith(stale_prefixes):
            st.session_state.pop(key, None)
    st.session_state["pb_schedule_schema_version"] = SCHEDULE_SCHEMA_VERSION
    st.session_state["v4_active_section"] = "Profile Setup"


def encode_dosage_frequency(frequency, dosage) -> str:
    frequency_value = int(frequency or 0)
    dosage_value = str(dosage or "").strip()
    if not frequency_value and not dosage_value:
        return ""
    return f"Frequency: {frequency_value}; Dosage: {dosage_value}"


def parse_dosage_frequency(value) -> tuple[int, str]:
    raw = str(value or "").strip()
    if not raw:
        return 0, ""
    match = re.match(r"^Frequency:\s*(\d+)\s*;\s*Dosage:\s*(.*)$", raw)
    if match:
        return int(match.group(1) or 0), (match.group(2) or "").strip()
    return 0, raw


def parse_timeline(value) -> list[str]:
    raw = str(value or "").strip()
    if not raw:
        return []
    parts = [part.strip() for part in raw.split(",") if part.strip()]
    return [part for part in parts if part in SUPPLEMENT_TIMELINE]


st.set_page_config(
    page_title="Recommendation Profile Builder V2",
    page_icon="💚",
    layout="wide",
    initial_sidebar_state="collapsed",
)
inject_global_styles()
apply_luxe_theme()
require_admin()
utility_logout_bar()
clear_schedule_state()

st.markdown(
    f"""
    <div class='hero-shell'>
      <div class='hm-pb-brand-row'>
        <span class='hm-pb-brand'>HealthyMe</span>
        <span class='hm-pb-version'>{APP_BUILD_VERSION} · {APP_BUILD_LABEL}</span>
      </div>
      <div class='hero-kicker'>Admin recommendations</div>
      <div class='hero-title'>Recommendation Profile Builder V2</div>
      <div class='hero-subtitle'>Default Profile Builder with row-based Exercise and Supplement Regime inputs.</div>
      <div><span class='meta-pill'>Guided wellness workflow</span></div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
<style>
.hm-pb-brand-row{display:flex;align-items:baseline;gap:.55rem;flex-wrap:wrap;margin-bottom:.35rem;}
.hm-pb-brand{color:#064E3B;font-size:.82rem;font-weight:950;letter-spacing:.02em;text-transform:uppercase;}
.hm-pb-version{color:#72551A;font-size:.72rem;font-weight:900;background:#F5E7C8;border-radius:999px;padding:.22rem .55rem;}
.hm-title{color:#064E3B;font-size:1.04rem;font-weight:950;margin:0 0 .25rem}.hm-sub{color:#64748B;font-size:.82rem;font-weight:720;margin:0 0 .7rem}
.hm-section-nav{margin:.35rem 0 .55rem 0;}.hm-section-rule{height:1px;background:linear-gradient(90deg,transparent,rgba(216,168,78,.8),transparent);margin:.3rem 0 .72rem 0;}
.hm-section-nav [data-testid="stButton"]>button{min-height:2.7rem!important;border-radius:15px!important;font-weight:930!important;border:1.15px solid rgba(216,180,98,.72)!important;background:#fff!important;color:#064E3B!important;box-shadow:0 4px 10px rgba(15,23,42,.035)!important;white-space:normal!important;line-height:1.15!important;padding:.55rem .5rem!important;}
.hm-section-nav [data-testid="stButton"]>button[kind="primary"]{background:linear-gradient(135deg,#FFF3D6,#FFFFFF)!important;border:1.5px solid #B89345!important;color:#064E3B!important;box-shadow:0 8px 18px rgba(15,23,42,.08)!important;}
.hm-readiness-strip{border-radius:15px;padding:.62rem .78rem;margin:.25rem 0 1rem 0;font-size:.84rem;font-weight:780;line-height:1.35;box-shadow:0 5px 12px rgba(15,23,42,.035)}.hm-readiness-strip b{color:#064E3B!important;}
.hm-ready-ok{background:#ECFDF5;border:1px solid #A7F3D0;color:#065F46;}.hm-ready-warn{background:#FFF7ED;border:1px solid #FED7AA;color:#9A3412;}
.hm-store-box{border:1px solid #E3C98E;background:#FFFDF8;border-radius:16px;padding:.85rem .9rem;margin:.35rem 0 1rem;box-shadow:0 6px 14px rgba(15,23,42,.035)}
.hm-load-label{font-size:.86rem;font-weight:760;color:#334155;margin:0 0 .28rem .05rem;}.hm-slot{font-size:.78rem;color:#72551A;font-weight:880;margin:.75rem 0 .25rem}
.hm-preview{border:1px dashed #D8A84E;background:#FFF9EC;border-radius:16px;padding:.75rem .85rem;margin:.35rem 0;color:#475569;font-size:.83rem;font-weight:740;line-height:1.45}
.hm-count-grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:.65rem;margin:.55rem 0 1rem}.hm-count-card{background:#fff;border:1px solid #E3C98E;border-radius:15px;padding:.7rem .8rem}.hm-count-card b{display:block;color:#064E3B;font-size:.95rem}.hm-count-card span{color:#64748B;font-size:.78rem;font-weight:780}
.hm-pill{display:inline-block;border-radius:999px;padding:.13rem .5rem;margin:.15rem .2rem .15rem 0;font-size:.7rem;font-weight:950}.hm-ok{background:#ECFDF5;color:#047857;border:1px solid #A7F3D0}.hm-pending{background:#FFF7ED;color:#B45309;border:1px solid #FED7AA}.hm-error{background:#FEF2F2;color:#B91C1C;border:1px solid #FECACA}.hm-info{background:#EFF6FF;color:#1D4ED8;border:1px solid #BFDBFE}
@media(max-width:900px){.hm-count-grid{grid-template-columns:1fr}.hm-section-nav [data-testid="stButton"]>button{min-height:2.45rem!important;}}
</style>
""",
    unsafe_allow_html=True,
)


@st.cache_data(ttl=180, show_spinner=False)
def cached_store_status():
    return check_profile_builder_store()


@st.cache_data(ttl=180, show_spinner=False)
def cached_sources():
    return load_profile_builder_sources()


@st.cache_data(ttl=180, show_spinner=False)
def cached_members():
    return load_member_options()


@st.cache_data(ttl=90, show_spinner=False)
def cached_drafts():
    return list_draft_profiles()


@st.cache_data(ttl=180, show_spinner=False)
def cached_profile_sources():
    return list_profile_sources()


def clear_pb_cache():
    cached_store_status.clear()
    cached_sources.clear()
    cached_members.clear()
    cached_drafts.clear()
    cached_profile_sources.clear()


STORE_STATUS = cached_store_status()
SOURCES, SOURCE_MESSAGE = cached_sources()


def with_select(options, placeholder):
    values = []
    for value in list(options or []):
        value = str(value).strip()
        if value and not value.startswith("-- Select") and value != placeholder:
            values.append(value)
    return [placeholder] + values


RECIPES = with_select(SOURCES.get("recipe", []), SELECT_RECIPE)
EXERCISES = with_select(SOURCES.get("exercise", []), SELECT_EXERCISE)
SUPPLEMENTS = with_select(SOURCES.get("supplement", []), SELECT_SUPPLEMENT)
AGE_BANDS = with_select(SOURCES.get("age_band", []), SELECT_AGE)
HEALTH_CONCERNS = list(SOURCES.get("health_concern", []))
DIET_TYPES = with_select(SOURCES.get("diet_type", []), SELECT_DIET)
INTENSITY_OPTIONS = [SELECT_INTENSITY, "Low", "Moderate", "High", "As tolerated"]


def ensure_state():
    st.session_state.setdefault("pb_profile", dict(PROFILE_DEFAULTS))
    st.session_state.setdefault("pb_items", {})
    st.session_state.setdefault("pb_row_counts", {})
    st.session_state.setdefault("pb_unsupported_items", [])
    st.session_state.setdefault("v4_active_section", "Profile Setup")


def is_select(value):
    value = str(value or "").strip()
    return not value or value.startswith("-- Select") or value == SELECT_MEMBER


def clean_choice(value):
    value = str(value or "").strip()
    return "" if is_select(value) else value


def display_choice(value):
    return clean_choice(value) or "NA"


def ensure_options(options, selected=None):
    values = list(options or [])
    if isinstance(selected, list):
        for item in selected:
            if item and item not in values:
                values.append(item)
    elif selected and selected not in values:
        values.append(selected)
    return values


def clean_date(value):
    if isinstance(value, dt.date):
        return value
    try:
        return dt.date.fromisoformat(str(value)[:10])
    except Exception:
        return dt.date.today()


def set_section(section_name):
    st.session_state["v4_active_section"] = section_name


def profile_widget_key(field):
    return f"pbw_profile_{field}"


def sync_profile_field(field):
    st.session_state["pb_profile"][field] = st.session_state.get(profile_widget_key(field), PROFILE_DEFAULTS.get(field, ""))


def sync_profile_all():
    for field in PROFILE_DEFAULTS:
        key = profile_widget_key(field)
        if key in st.session_state:
            st.session_state["pb_profile"][field] = st.session_state[key]


def item_key(kind, day, slot, idx, field):
    return f"{kind}|{day}|{slot}|{idx}|{field}"


def item_widget_key(kind, day, slot, idx, field):
    return f"pbw_{kind}_{day}_{safe_key(slot)}_{idx}_{field}"


def item_value(kind, day, slot, idx, field, default=""):
    return st.session_state["pb_items"].get(item_key(kind, day, slot, idx, field), default)


def sync_item_field(kind, day, slot, idx, field):
    key = item_widget_key(kind, day, slot, idx, field)
    st.session_state["pb_items"][item_key(kind, day, slot, idx, field)] = st.session_state.get(key, "")


def row_count(kind, day, slot):
    key = f"{kind}|{day}|{slot}"
    st.session_state["pb_row_counts"].setdefault(key, 1)
    return int(st.session_state["pb_row_counts"][key])


def add_row(kind, day, slot):
    key = f"{kind}|{day}|{slot}"
    st.session_state["pb_row_counts"][key] = row_count(kind, day, slot) + 1


def set_widget_default(widget_key, value):
    if widget_key not in st.session_state:
        st.session_state[widget_key] = value


def reset_new_draft():
    for key in list(st.session_state.keys()):
        if str(key).startswith("pbw_"):
            st.session_state.pop(key, None)
    st.session_state["pb_profile"] = dict(PROFILE_DEFAULTS)
    st.session_state["pb_items"] = {}
    st.session_state["pb_row_counts"] = {}
    st.session_state["pb_unsupported_items"] = []
    st.session_state["v4_active_section"] = "Profile Setup"
    st.session_state["pb_schedule_schema_version"] = SCHEDULE_SCHEMA_VERSION


def day_label(day):
    start = st.session_state["pb_profile"].get("start_date", dt.date.today())
    return f"Day {day} - {(start + dt.timedelta(days=day - 1)).strftime('%a, %d %b')}"


def day_picker(key):
    st.session_state.setdefault(key, 1)
    for row in ([1, 2, 3, 4], [5, 6, 7]):
        cols = st.columns(len(row), gap="small")
        for col, day in zip(cols, row):
            with col:
                st.button(
                    day_label(day),
                    key=f"{key}_{day}",
                    type=("primary" if st.session_state[key] == day else "secondary"),
                    use_container_width=True,
                    on_click=lambda d=day: st.session_state.update({key: d}),
                )
    return st.session_state[key]


def item_row(kind, day, slot):
    for idx in range(row_count(kind, day, slot)):
        if kind == "meal":
            fields = [("recipe", "Recipe", RECIPES, SELECT_RECIPE, "select"), ("portion", "Portion", None, "", "text"), ("instruction", "Instruction", None, "", "text")]
            cols = st.columns([0.44, 0.20, 0.36])
        elif kind == "exercise":
            fields = [
                ("exercise", "Exercise", EXERCISES, SELECT_EXERCISE, "select"),
                ("time_of_day", "Time of Day", EXERCISE_TIME_OF_DAY, "Morning", "select"),
                ("intensity", "Intensity", INTENSITY_OPTIONS, SELECT_INTENSITY, "select"),
                ("instruction", "Instruction", None, "", "text"),
            ]
            cols = st.columns([0.30, 0.22, 0.18, 0.30])
        else:
            fields = [
                ("supplement", "Supplement", SUPPLEMENTS, SELECT_SUPPLEMENT, "select"),
                ("frequency", "Frequency", None, 0, "number"),
                ("timeline", "Timeline", SUPPLEMENT_TIMELINE, [], "multiselect"),
                ("dose", "Dosage", None, "", "text"),
                ("instruction", "Instruction", None, "", "text"),
            ]
            cols = st.columns([0.24, 0.14, 0.26, 0.16, 0.20])

        for col, (field, label, options, default, field_type) in zip(cols, fields):
            key = item_widget_key(kind, day, slot, idx, field)
            value = item_value(kind, day, slot, idx, field, default)
            set_widget_default(key, value)
            if field_type == "select":
                col.selectbox(label, ensure_options(options, st.session_state[key]), key=key, on_change=sync_item_field, args=(kind, day, slot, idx, field))
            elif field_type == "multiselect":
                selected = st.session_state[key] if isinstance(st.session_state[key], list) else parse_timeline(st.session_state[key])
                st.session_state[key] = selected
                col.multiselect(label, options, key=key, on_change=sync_item_field, args=(kind, day, slot, idx, field))
            elif field_type == "number":
                try:
                    number_value = int(st.session_state[key] or 0)
                except Exception:
                    number_value = 0
                st.session_state[key] = number_value
                col.number_input(label, min_value=0, max_value=7, step=1, key=key, on_change=sync_item_field, args=(kind, day, slot, idx, field))
            else:
                col.text_input(label, key=key, on_change=sync_item_field, args=(kind, day, slot, idx, field))

        if kind == "supplement":
            frequency_value = int(st.session_state.get(item_widget_key(kind, day, slot, idx, "frequency"), 0) or 0)
            timeline_value = st.session_state.get(item_widget_key(kind, day, slot, idx, "timeline"), []) or []
            if frequency_value and len(timeline_value) != frequency_value:
                st.caption(f"Timeline validation: Frequency is {frequency_value}, so select exactly {frequency_value} timeline option(s).")

    label = {"meal": "Add food item", "exercise": "Add workout item", "supplement": "Add supplement item"}[kind]
    if st.button(label, key=f"add_{kind}_{day}_{safe_key(slot)}", use_container_width=True):
        add_row(kind, day, slot)
        st.rerun()


def collect_items(include_unsupported=True):
    rows = []
    for kind, slots in SLOTS_BY_KIND.items():
        for day in range(1, 8):
            for slot in slots:
                for idx in range(row_count(kind, day, slot)):
                    if kind == "meal":
                        row = {"item_type": kind, "day_number": day, "slot_name": slot, "item_order": idx + 1, "reference_label": clean_choice(item_value(kind, day, slot, idx, "recipe")), "portion": item_value(kind, day, slot, idx, "portion"), "instruction": item_value(kind, day, slot, idx, "instruction")}
                    elif kind == "exercise":
                        exercise = clean_choice(item_value(kind, day, slot, idx, "exercise"))
                        intensity = clean_choice(item_value(kind, day, slot, idx, "intensity"))
                        instruction = item_value(kind, day, slot, idx, "instruction")
                        time_of_day = item_value(kind, day, slot, idx, "time_of_day", "Morning")
                        row = {"item_type": kind, "day_number": day, "slot_name": slot, "item_order": idx + 1, "reference_label": exercise, "scheduled_time": time_of_day if any([exercise, intensity, instruction]) else "", "intensity": intensity, "instruction": instruction}
                    else:
                        supplement = clean_choice(item_value(kind, day, slot, idx, "supplement"))
                        frequency = int(item_value(kind, day, slot, idx, "frequency", 0) or 0)
                        timeline = item_value(kind, day, slot, idx, "timeline", []) or []
                        dosage = item_value(kind, day, slot, idx, "dose")
                        instruction = item_value(kind, day, slot, idx, "instruction")
                        timeline_text = ", ".join(timeline) if isinstance(timeline, list) else str(timeline or "")
                        row = {"item_type": kind, "day_number": day, "slot_name": slot, "item_order": idx + 1, "reference_label": supplement, "scheduled_time": timeline_text if any([supplement, frequency, dosage, instruction]) else "", "dosage_frequency": encode_dosage_frequency(frequency, dosage), "instruction": instruction}
                    rows.append(row)
    if include_unsupported:
        rows.extend(st.session_state.get("pb_unsupported_items", []))
    return rows


def item_has_content(row):
    return any(str(row.get(field, "")).strip() for field in ("reference_label", "portion", "instruction", "intensity", "dosage_frequency", "scheduled_time"))


def active_rows(rows=None):
    return [row for row in (rows if rows is not None else collect_items()) if item_has_content(row)]


def validation_summary(rows=None):
    sync_profile_all()
    profile = st.session_state["pb_profile"]
    rows = active_rows(rows)
    counts = {
        "meal": len([row for row in rows if row.get("item_type") == "meal"]),
        "exercise": len([row for row in rows if row.get("item_type") == "exercise"]),
        "supplement": len([row for row in rows if row.get("item_type") == "supplement"]),
    }
    errors = []
    guidance = []
    for row in rows:
        if row.get("item_type") == "supplement":
            frequency, _ = parse_dosage_frequency(row.get("dosage_frequency"))
            timeline_count = len(parse_timeline(row.get("scheduled_time")))
            if frequency and timeline_count != frequency:
                guidance.append(f"Supplement timeline validation: one row has frequency {frequency} but {timeline_count} timeline selection(s).")
    if not str(profile.get("profile_name", "")).strip():
        errors.append("Profile Name is required before saving a draft.")
    if is_select(profile.get("age_band")):
        guidance.append("Select Age Band before final publish readiness.")
    if is_select(profile.get("diet_type")):
        guidance.append("Select Diet Type before final publish readiness.")
    if is_select(profile.get("member")):
        guidance.append("Assign a member before publish. Draft save can continue without member assignment.")
    if counts["meal"] == 0:
        guidance.append("Add at least one Meal Structure row before publish readiness.")
    if counts["exercise"] == 0:
        guidance.append("Add at least one Exercise Regime row before publish readiness.")
    if counts["supplement"] == 0:
        guidance.append("Add at least one Supplement Regime row before publish readiness.")
    return {"errors": errors, "guidance": guidance, "counts": counts, "rows": rows}


def render_validation_box(summary, heading="Validation"):
    counts = summary["counts"]
    if summary["errors"]:
        status_class = "hm-error"
        status = "Draft save needs attention"
    elif summary["guidance"]:
        status_class = "hm-pending"
        status = "Draft can be saved; publish readiness pending"
    else:
        status_class = "hm-ok"
        status = "Draft is complete for preview"
    st.markdown(f"""
<div class='hm-preview'>
<b>{heading}</b><br>
<span class='hm-pill {status_class}'>{status}</span>
<div class='hm-count-grid'>
  <div class='hm-count-card'><b>{counts['meal']}</b><span>Meal rows</span></div>
  <div class='hm-count-card'><b>{counts['exercise']}</b><span>Exercise rows</span></div>
  <div class='hm-count-card'><b>{counts['supplement']}</b><span>Supplement rows</span></div>
  <div class='hm-count-card'><b>{len(summary['rows'])}</b><span>Total rows</span></div>
</div>
</div>
""", unsafe_allow_html=True)
    if summary["errors"]:
        st.error(" ".join(summary["errors"]))
    if summary["guidance"]:
        st.warning(" ".join(summary["guidance"]))


def preview_table(rows, selected_day):
    table = []
    for row in rows:
        if int(row.get("day_number") or 0) != selected_day:
            continue
        if row.get("item_type") == "exercise":
            table.append({
                "Type": "Exercise",
                "Day": row.get("day_number"),
                "Exercise": row.get("reference_label") or "NA",
                "Time of Day": row.get("scheduled_time") or "NA",
                "Intensity": row.get("intensity") or "NA",
                "Supplement": "NA",
                "Frequency": "NA",
                "Timeline": "NA",
                "Dosage": "NA",
                "Instruction": row.get("instruction") or "NA",
            })
        elif row.get("item_type") == "supplement":
            frequency, dosage = parse_dosage_frequency(row.get("dosage_frequency"))
            table.append({
                "Type": "Supplement",
                "Day": row.get("day_number"),
                "Exercise": "NA",
                "Time of Day": "NA",
                "Intensity": "NA",
                "Supplement": row.get("reference_label") or "NA",
                "Frequency": frequency or "NA",
                "Timeline": row.get("scheduled_time") or "NA",
                "Dosage": dosage or "NA",
                "Instruction": row.get("instruction") or "NA",
            })
        else:
            table.append({
                "Type": "Meal",
                "Day": row.get("day_number"),
                "Exercise": "NA",
                "Time of Day": row.get("slot_name") or "NA",
                "Intensity": "NA",
                "Supplement": row.get("reference_label") or "NA",
                "Frequency": "NA",
                "Timeline": "NA",
                "Dosage": row.get("portion") or "NA",
                "Instruction": row.get("instruction") or "NA",
            })
    return table


def apply_profile_to_session(profile, items):
    reset_new_draft()
    st.session_state["pb_profile"] = {
        "id": profile.get("id", ""),
        "profile_name": profile.get("profile_name", ""),
        "clone_from": profile.get("clone_source_label") or "New profile",
        "change_note": profile.get("change_note") or "",
        "status": "Draft",
        "region": profile.get("region") or "",
        "age_band": profile.get("age_band") or SELECT_AGE,
        "concerns": list(profile.get("health_concerns") or []),
        "diet_type": profile.get("diet_type") or SELECT_DIET,
        "member": profile.get("assigned_member_label") or SELECT_MEMBER,
        "note": profile.get("profile_note") or "",
        "start_date": clean_date(profile.get("start_date")),
    }
    unsupported = []
    for row in items:
        kind = row.get("item_type")
        day = int(row.get("day_number") or 0)
        idx = int(row.get("item_order") or 1) - 1
        if kind == "exercise":
            slot = EXERCISE_ROW_SLOT
            st.session_state["pb_row_counts"][f"{kind}|{day}|{slot}"] = max(row_count(kind, day, slot), idx + 1)
            values = {"exercise": row.get("reference_label") or SELECT_EXERCISE, "time_of_day": row.get("scheduled_time") or "Morning", "intensity": row.get("intensity") or SELECT_INTENSITY, "instruction": row.get("instruction") or ""}
        elif kind == "supplement":
            slot = SUPPLEMENT_ROW_SLOT
            frequency, dosage = parse_dosage_frequency(row.get("dosage_frequency"))
            st.session_state["pb_row_counts"][f"{kind}|{day}|{slot}"] = max(row_count(kind, day, slot), idx + 1)
            values = {"supplement": row.get("reference_label") or SELECT_SUPPLEMENT, "frequency": frequency, "timeline": parse_timeline(row.get("scheduled_time")), "dose": dosage, "instruction": row.get("instruction") or ""}
        elif kind == "meal":
            slot = str(row.get("slot_name") or "").strip()
            if slot not in MEAL_SLOTS or day < 1 or day > 7:
                unsupported.append(row)
                continue
            st.session_state["pb_row_counts"][f"{kind}|{day}|{slot}"] = max(row_count(kind, day, slot), idx + 1)
            values = {"recipe": row.get("reference_label") or SELECT_RECIPE, "portion": row.get("portion") or "", "instruction": row.get("instruction") or ""}
        else:
            unsupported.append(row)
            continue
        for field, value in values.items():
            st.session_state["pb_items"][item_key(kind, day, slot, idx, field)] = value
    st.session_state["pb_unsupported_items"] = unsupported


def current_profile_payload(member_label_to_id, clone_label_to_id):
    sync_profile_all()
    profile = st.session_state["pb_profile"]
    member_label = profile.get("member", SELECT_MEMBER)
    start_date = profile.get("start_date", dt.date.today())
    return {
        "id": profile.get("id", ""),
        "profile_name": profile.get("profile_name", ""),
        "region": profile.get("region", ""),
        "age_band": clean_choice(profile.get("age_band", "")),
        "diet_type": clean_choice(profile.get("diet_type", "")),
        "health_concerns": profile.get("concerns", []),
        "profile_note": profile.get("note", ""),
        "change_note": profile.get("change_note", ""),
        "cycle_rule": "Weekly cyclical until replaced or stopped",
        "assigned_member_id": member_label_to_id.get(member_label, "") if not is_select(member_label) else "",
        "assigned_member_label": member_label if not is_select(member_label) else "",
        "start_date": start_date.isoformat() if isinstance(start_date, dt.date) else str(start_date or ""),
        "clone_source_profile_id": clone_label_to_id.get(profile.get("clone_from", ""), ""),
        "clone_source_label": profile.get("clone_from", "New profile"),
        "created_by_user_id": st.session_state.get("user_id", ""),
        "created_by_email": st.session_state.get("user_email", ""),
    }


ensure_state()

st.markdown("<div class='hm-section-nav'>", unsafe_allow_html=True)
nav_cols = st.columns([1, 1, 1, 1, 0.9], gap="small")
for col, section_name in zip(nav_cols, SECTIONS):
    with col:
        st.button(NAV_LABELS[section_name], key=f"v2_nav_{safe_key(section_name)}", type=("primary" if st.session_state["v4_active_section"] == section_name else "secondary"), use_container_width=True, on_click=set_section, args=(section_name,))
st.markdown("</div>", unsafe_allow_html=True)
st.markdown("<div class='hm-section-rule'></div>", unsafe_allow_html=True)

if STORE_STATUS.get("ok"):
    st.markdown("<div class='hm-readiness-strip hm-ready-ok'><b>Draft store is ready.</b> Default V2 now uses row-based Exercise and Supplement Regime fields.</div>", unsafe_allow_html=True)
else:
    st.markdown(f"<div class='hm-readiness-strip hm-ready-warn'><b>Draft store is not ready.</b> {STORE_STATUS.get('message', 'Run the Sprint 1 SQL script, then refresh this page.')}</div>", unsafe_allow_html=True)
    if st.button("Refresh Backend Status", use_container_width=True):
        clear_pb_cache()
        st.rerun()

if st.session_state.get("pb_unsupported_items"):
    st.warning("Some loaded rows use older unsupported slot names. They are preserved for save/load review but not silently mapped into the new row-based structure.")

section = st.session_state["v4_active_section"]

if section == "Profile Setup":
    member_options, member_message = cached_members()
    member_label_to_id = {row["label"]: row["id"] for row in member_options}
    if SELECT_MEMBER not in member_label_to_id:
        member_label_to_id = {SELECT_MEMBER: "", **member_label_to_id}
    ok_sources, source_profiles, _ = cached_profile_sources()
    clone_options = ["New profile"]
    clone_label_to_id = {"New profile": ""}
    if ok_sources and source_profiles:
        for source_profile in source_profiles:
            label = f"{source_profile.get('profile_name', 'Untitled')} [{source_profile.get('status', 'draft')}]"
            clone_options.append(label)
            clone_label_to_id[label] = source_profile.get("id", "")

    profile = st.session_state["pb_profile"]
    profile["clone_from"] = profile.get("clone_from") if profile.get("clone_from") in clone_options else "New profile"
    profile["member"] = profile.get("member") if profile.get("member") in member_label_to_id else SELECT_MEMBER

    st.markdown("<div class='hm-title'>Recommendation Profile Setup</div><div class='hm-sub'>Reusable profile with clone-from-existing, draft save/load and validation review.</div>", unsafe_allow_html=True)
    st.markdown("<div class='hm-store-box'>", unsafe_allow_html=True)
    st.caption(f"Dropdown source: {SOURCE_MESSAGE} Member source: {member_message}")
    ok_drafts, drafts, draft_msg = cached_drafts()
    draft_label_to_id = {SELECT_DRAFT: ""}
    if ok_drafts:
        for draft in drafts:
            draft_label_to_id[f"{draft.get('profile_name', 'Untitled draft')} · {str(draft.get('updated_at', ''))[:16]}"] = draft.get("id", "")

    st.markdown("<div class='hm-load-label'>Load saved draft</div>", unsafe_allow_html=True)
    load_cols = st.columns([0.58, 0.21, 0.21], gap="medium")
    selected_draft_label = load_cols[0].selectbox("Load saved draft", list(draft_label_to_id.keys()), key="v2_load_draft_choice", label_visibility="collapsed")
    if load_cols[1].button("Load Draft", use_container_width=True, disabled=not bool(draft_label_to_id.get(selected_draft_label))):
        ok, profile_payload, item_payload, message = load_profile(draft_label_to_id.get(selected_draft_label, ""))
        if ok:
            apply_profile_to_session(profile_payload, item_payload)
            st.session_state["v4_profile_action_message"] = message
            st.rerun()
        else:
            st.error(message)
    if load_cols[2].button("New Draft", use_container_width=True):
        reset_new_draft()
        st.session_state["v4_profile_action_message"] = "New blank draft started."
        st.rerun()
    profile_action_message = st.session_state.pop("v4_profile_action_message", "")
    if profile_action_message:
        st.success(profile_action_message)
    if not ok_drafts and STORE_STATUS.get("ok"):
        st.caption(draft_msg)
    if profile.get("id"):
        st.caption(f"Current draft id: {profile.get('id')}")
    st.markdown("</div>", unsafe_allow_html=True)

    for field in PROFILE_DEFAULTS:
        set_widget_default(profile_widget_key(field), profile.get(field, PROFILE_DEFAULTS[field]))

    c1, c2 = st.columns(2, gap="large")
    with c1:
        st.text_input("Profile Name", key=profile_widget_key("profile_name"), on_change=sync_profile_field, args=("profile_name",))
        st.markdown("<div class='hm-load-label'>Clone From Existing Profile</div>", unsafe_allow_html=True)
        clone_cols = st.columns([0.68, 0.32], gap="small")
        selected_clone = clone_cols[0].selectbox("Clone From Existing Profile", ensure_options(clone_options, profile.get("clone_from")), key=profile_widget_key("clone_from"), label_visibility="collapsed", on_change=sync_profile_field, args=("clone_from",))
        if clone_cols[1].button("Clone Selected", use_container_width=True, disabled=not bool(clone_label_to_id.get(selected_clone))):
            ok, profile_payload, item_payload, message = load_profile(clone_label_to_id.get(selected_clone, ""))
            if ok:
                source_name = profile_payload.get("profile_name", "Selected profile")
                apply_profile_to_session(profile_payload, item_payload)
                st.session_state["pb_profile"]["id"] = ""
                st.session_state["pb_profile"]["profile_name"] = f"Copy of {source_name}"
                st.session_state["pb_profile"]["clone_from"] = selected_clone
                st.session_state["v4_clone_action_message"] = f"Cloned {source_name} into a new unsaved draft. Review, edit and save."
                st.rerun()
            else:
                st.error(message)
        clone_msg = st.session_state.pop("v4_clone_action_message", "")
        if clone_msg:
            st.success(clone_msg)
        st.text_input("Change Note", key=profile_widget_key("change_note"), on_change=sync_profile_field, args=("change_note",))
        st.text_input("Profile Status", value="Draft", disabled=True)

    with c2:
        st.text_input("Region / Food Culture", key=profile_widget_key("region"), on_change=sync_profile_field, args=("region",))
        st.selectbox("Age Band", ensure_options(AGE_BANDS, profile.get("age_band")), key=profile_widget_key("age_band"), on_change=sync_profile_field, args=("age_band",))
        st.multiselect("Health Concerns", ensure_options(HEALTH_CONCERNS, profile.get("concerns")), key=profile_widget_key("concerns"), on_change=sync_profile_field, args=("concerns",))
        st.selectbox("Diet Type", ensure_options(DIET_TYPES, profile.get("diet_type")), key=profile_widget_key("diet_type"), on_change=sync_profile_field, args=("diet_type",))

    a1, a2 = st.columns(2, gap="large")
    with a1:
        st.selectbox("Example Member Assignment", list(member_label_to_id.keys()), key=profile_widget_key("member"), on_change=sync_profile_field, args=("member",))
        st.text_area("Profile-level Nutritionist Note", height=150, key=profile_widget_key("note"), on_change=sync_profile_field, args=("note",))
    with a2:
        st.date_input("Plan Start Date", key=profile_widget_key("start_date"), on_change=sync_profile_field, args=("start_date",))
        st.text_input("Cycle Rule", value="Weekly cyclical until replaced or stopped", disabled=True)
        st.text_input("Implementation Status", value="Default V2 row-based regime. Additional B4 page removed.", disabled=True)

    save_clicked = st.button("Save Draft Profile", type="primary", use_container_width=True, disabled=not STORE_STATUS.get("ok"))
    save_feedback = st.container()
    if save_clicked:
        rows_for_save = collect_items()
        summary_for_save = validation_summary(rows_for_save)
        if summary_for_save["errors"]:
            save_feedback.error(" ".join(summary_for_save["errors"]))
        else:
            ok, profile_id, message = save_draft_profile(current_profile_payload(member_label_to_id, clone_label_to_id), rows_for_save)
            if ok:
                st.session_state["pb_profile"]["id"] = profile_id
                cached_drafts.clear()
                cached_profile_sources.clear()
                save_feedback.success(message)
                if summary_for_save["guidance"]:
                    save_feedback.warning("Draft saved. Publish readiness still needs: " + " ".join(summary_for_save["guidance"]))
            else:
                save_feedback.error(message)

    render_validation_box(validation_summary(), "Draft Validation")

elif section == "Meal Structure":
    day = day_picker("v4_meal_day")
    for slot in MEAL_SLOTS:
        st.markdown(f"<div class='hm-slot'>{slot}</div>", unsafe_allow_html=True)
        item_row("meal", day, slot)
    x, y = st.columns(2)
    x.button("Copy Day 1 to all days", key=f"v2_meal_copy_all_{day}", use_container_width=True)
    y.button("Copy previous day", key=f"v2_meal_copy_prev_{day}", use_container_width=True)

elif section == "Exercise Regime":
    day = day_picker("v4_exercise_day")
    st.markdown("<div class='hm-title'>Exercise Regime</div><div class='hm-sub'>Fields: Exercise | Time of Day | Intensity | Instruction</div>", unsafe_allow_html=True)
    for slot in SLOTS_BY_KIND["exercise"]:
        for _ in [slot]:
            item_row("exercise", day, slot)
    x, y = st.columns(2)
    x.button("Copy Day 1 to all days", key=f"v2_ex_copy_all_{day}", use_container_width=True)
    y.button("Copy previous day", key=f"v2_ex_copy_prev_{day}", use_container_width=True)

elif section == "Supplement Regime":
    day = day_picker("v4_supp_day")
    st.markdown("<div class='hm-title'>Supplement Regime</div><div class='hm-sub'>Fields: Supplement | Frequency | Timeline | Dosage | Instruction. Timeline count is validated against Frequency.</div>", unsafe_allow_html=True)
    for slot in SLOTS_BY_KIND["supplement"]:
        for _ in [slot]:
            item_row("supplement", day, slot)
    x, y, z = st.columns(3)
    x.button("Copy active regimen", key=f"v2_supp_active_{day}", use_container_width=True)
    y.button("Copy Day 1 to all days", key=f"v2_supp_all_{day}", use_container_width=True)
    z.button("Copy previous day", key=f"v2_supp_prev_{day}", use_container_width=True)

else:
    sync_profile_all()
    all_rows = collect_items()
    summary = validation_summary(all_rows)
    profile = st.session_state["pb_profile"]
    plan_start = profile.get("start_date", dt.date.today())
    concerns = profile.get("concerns", [])
    st.markdown("<div class='hm-title'>Preview & End-to-End Flow Review</div><div class='hm-sub'>Preview reads from the current durable draft buffer and saved draft data. Publish and member consumption remain disabled.</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='hm-preview'><b>Profile Summary</b><br><b>Draft ID:</b> {profile.get('id') or 'Not saved yet'}<br><b>Profile:</b> {profile.get('profile_name') or 'Not entered yet'}<br><b>Status:</b> Draft<br><b>Assigned Member:</b> {display_choice(profile.get('member'))}<br><b>Start Date:</b> {plan_start.isoformat() if isinstance(plan_start, dt.date) else plan_start}<br><b>Tags:</b> {profile.get('region') or 'NA'} - {display_choice(profile.get('age_band'))} - {display_choice(profile.get('diet_type'))} - {', '.join(concerns) if concerns else 'No health concern selected'}<br><b>Profile Note:</b> {profile.get('note') or 'NA'}</div>", unsafe_allow_html=True)
    render_validation_box(summary, "Preview Validation")
    selected_preview_day = st.selectbox("Preview Day", list(range(1, 8)), format_func=lambda day: day_label(day), key="v4_preview_day")
    rows_for_day = preview_table(summary["rows"], selected_preview_day)
    if rows_for_day:
        st.dataframe(rows_for_day, use_container_width=True, hide_index=True)
    else:
        st.info("No recommendation rows have been added for this day yet.")
    st.markdown("<div class='hm-preview'><b>Publish Readiness Checklist</b><br>This checklist remains admin-side. Publish, activate and member-facing flows are deliberately disabled in this sprint.</div>", unsafe_allow_html=True)

render_page_nav(
    "Recommendation Profile Builder",
    back_page="pages/10_Admin_Dashboard.py",
    dashboard_page="pages/10_Admin_Dashboard.py",
    show_evaluation=False,
    show_dashboard=True,
    location="bottom",
)
render_back_to_top()
