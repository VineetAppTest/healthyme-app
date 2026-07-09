import datetime as dt
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
from components.ui_common import inject_global_styles, apply_luxe_theme, utility_logout_bar, render_page_nav, render_back_to_top

APP_BUILD_VERSION = "v100.20"
APP_BUILD_LABEL = "Profile Builder Cross-section Save Hotfix"

st.set_page_config(page_title="Recommendation Profile Builder Sprint 1", page_icon="💚", layout="wide", initial_sidebar_state="collapsed")
inject_global_styles()
apply_luxe_theme()
require_admin()
utility_logout_bar()

st.markdown(
    f"""
    <div class='hero-shell'>
      <div class='hm-pb-brand-row'>
        <span class='hm-pb-brand'>HealthyMe</span>
        <span class='hm-pb-version'>{APP_BUILD_VERSION} · {APP_BUILD_LABEL}</span>
      </div>
      <div class='hero-kicker'>Admin recommendations</div>
      <div class='hero-title'>Recommendation Profile Builder Sprint 1</div>
      <div class='hero-subtitle'>Backend foundation with safe draft save/load. Publish and member-facing flows are intentionally disabled in this sprint.</div>
      <div><span class='meta-pill'>Guided wellness workflow</span></div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown("""
<style>
.hm-pb-brand-row{display:flex;align-items:baseline;gap:.55rem;flex-wrap:wrap;margin-bottom:.35rem;}
.hm-pb-brand{color:#064E3B;font-size:.82rem;font-weight:950;letter-spacing:.02em;text-transform:uppercase;}
.hm-pb-version{color:#72551A;font-size:.72rem;font-weight:900;background:#F5E7C8;border-radius:999px;padding:.22rem .55rem;}
.hm-title{color:#064E3B;font-size:1.04rem;font-weight:950;margin:0 0 .25rem}.hm-sub{color:#64748B;font-size:.82rem;font-weight:720;margin:0 0 .7rem}
.hm-section-nav{margin:.35rem 0 .55rem 0;}.hm-section-rule{height:1px;background:linear-gradient(90deg,transparent,rgba(216,168,78,.8),transparent);margin:.3rem 0 .72rem 0;}
.hm-section-nav [data-testid="stButton"]>button{min-height:2.7rem!important;border-radius:15px!important;font-weight:930!important;border:1.15px solid rgba(216,180,98,.72)!important;background:#fff!important;color:#064E3B!important;box-shadow:0 4px 10px rgba(15,23,42,.035)!important;white-space:normal!important;line-height:1.15!important;padding:.55rem .5rem!important;}
.hm-section-nav [data-testid="stButton"]>button[kind="primary"]{background:linear-gradient(135deg,#FFF3D6,#FFFFFF)!important;border:1.5px solid #B89345!important;color:#064E3B!important;box-shadow:0 8px 18px rgba(15,23,42,.08)!important;}
.hm-section-nav [data-testid="stButton"]>button[kind="primary"] *{color:#064E3B!important;}
.hm-readiness-strip{border-radius:15px;padding:.62rem .78rem;margin:.25rem 0 1rem 0;font-size:.84rem;font-weight:780;line-height:1.35;box-shadow:0 5px 12px rgba(15,23,42,.035)}.hm-readiness-strip b{color:#064E3B!important;}
.hm-ready-ok{background:#ECFDF5;border:1px solid #A7F3D0;color:#065F46;}.hm-ready-warn{background:#FFF7ED;border:1px solid #FED7AA;color:#9A3412;}
.hm-store-box{border:1px solid #E3C98E;background:#FFFDF8;border-radius:16px;padding:.85rem .9rem;margin:.35rem 0 1rem;box-shadow:0 6px 14px rgba(15,23,42,.035)}
.hm-load-label{font-size:.86rem;font-weight:760;color:#334155;margin:0 0 .28rem .05rem;}.hm-slot{font-size:.78rem;color:#72551A;font-weight:880;margin:.75rem 0 .25rem}
.hm-day{border:1px solid #E3C98E;background:white;border-radius:16px;padding:.7rem .8rem;margin:.45rem 0 .85rem}.hm-preview{border:1px dashed #D8A84E;background:#FFF9EC;border-radius:16px;padding:.75rem .85rem;margin:.35rem 0;color:#475569;font-size:.83rem;font-weight:740;line-height:1.45}
.hm-readiness{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:.55rem;margin:.55rem 0 0}.hm-readiness-item{background:#fff;border:1px solid #E3C98E;border-radius:14px;padding:.58rem .68rem;line-height:1.35}
.hm-pill{display:inline-block;border-radius:999px;padding:.13rem .5rem;margin:.15rem .2rem .15rem 0;font-size:.7rem;font-weight:950}.hm-ok{background:#ECFDF5;color:#047857;border:1px solid #A7F3D0}.hm-pending{background:#FFF7ED;color:#B45309;border:1px solid #FED7AA}.hm-info{background:#EFF6FF;color:#1D4ED8;border:1px solid #BFDBFE}
@media(max-width:900px){.hm-readiness{grid-template-columns:1fr}.hm-section-nav [data-testid="stButton"]>button{min-height:2.45rem!important;}}
</style>
""", unsafe_allow_html=True)

MEAL_SLOTS = ["Wake-up / Early Morning", "Breakfast", "Mid-morning Snack", "Lunch", "Evening Snack / Tea", "Dinner", "Bedtime"]
EXERCISE_SLOTS = ["Morning", "Evening", "Preferred Time"]
SUPPLEMENT_SLOTS = ["Morning", "Afternoon", "Evening", "Before Bed", "Preferred Time"]
SECTIONS = ["Profile Setup", "Meal Structure", "Exercise Regime", "Supplement Regime", "Preview & End-to-End Flow"]
NAV_LABELS = {"Profile Setup": "Profile Setup", "Meal Structure": "Meal Structure", "Exercise Regime": "Exercise Regime", "Supplement Regime": "Supplement Regime", "Preview & End-to-End Flow": "Preview & Flow"}
SELECT_AGE = "-- Select age band --"
SELECT_DIET = "-- Select diet type --"
SELECT_INTENSITY = "-- Select intensity --"

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
    cached_store_status.clear(); cached_sources.clear(); cached_members.clear(); cached_drafts.clear(); cached_profile_sources.clear()

STORE_STATUS = cached_store_status()
SOURCES, SOURCE_MESSAGE = cached_sources()

def with_select(options, placeholder):
    clean = []
    for value in list(options or []):
        value = str(value).strip()
        if not value or value.startswith("-- Select") or value == placeholder:
            continue
        clean.append(value)
    return [placeholder] + clean

RECIPES = with_select(SOURCES.get("recipe", []), "-- Select recipe --")
EXERCISES = with_select(SOURCES.get("exercise", []), "-- Select exercise --")
SUPPLEMENTS = with_select(SOURCES.get("supplement", []), "-- Select supplement --")
AGE_BANDS = with_select(SOURCES.get("age_band", []), SELECT_AGE)
HEALTH_CONCERNS = list(SOURCES.get("health_concern", []))
DIET_TYPES = with_select(SOURCES.get("diet_type", []), SELECT_DIET)
INTENSITY_OPTIONS = [SELECT_INTENSITY, "Low", "Moderate", "High", "As tolerated"]

PROFILE_DEFAULTS = {"id": "", "profile_name": "", "clone_from": "New profile", "change_note": "", "status": "Draft", "region": "", "age_band": SELECT_AGE, "concerns": [], "diet_type": SELECT_DIET, "member": "Select member", "note": "", "start_date": dt.date.today()}


def ensure_state():
    st.session_state.setdefault("pb_profile", dict(PROFILE_DEFAULTS))
    st.session_state.setdefault("pb_items", {})
    st.session_state.setdefault("pb_row_counts", {})
    st.session_state.setdefault("v4_active_section", "Profile Setup")


def is_select(value):
    value = str(value or "").strip()
    return not value or value.startswith("-- Select") or value == "Select member"


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
    return f"pbw_{kind}_{day}_{slot}_{idx}_{field}"


def item_value(kind, day, slot, idx, field, default=""):
    return st.session_state["pb_items"].get(item_key(kind, day, slot, idx, field), default)


def sync_item_field(kind, day, slot, idx, field):
    key = item_widget_key(kind, day, slot, idx, field)
    st.session_state["pb_items"][item_key(kind, day, slot, idx, field)] = st.session_state.get(key, "")


def sync_visible_item_widgets():
    for key, value in list(st.session_state.items()):
        if not str(key).startswith("pbw_") or str(key).startswith("pbw_profile_"):
            continue
        parts = str(key)[4:].rsplit("_", 4)
        if len(parts) == 5:
            kind, day, slot, idx, field = parts
            st.session_state["pb_items"][item_key(kind, int(day), slot, int(idx), field)] = value


def row_count(kind, day, slot):
    key = f"{kind}|{day}|{slot}"
    st.session_state["pb_row_counts"].setdefault(key, 1)
    return int(st.session_state["pb_row_counts"][key])


def add_row(kind, day, slot):
    key = f"{kind}|{day}|{slot}"
    st.session_state["pb_row_counts"][key] = row_count(kind, day, slot) + 1


def reset_new_draft():
    for key in list(st.session_state.keys()):
        if str(key).startswith("pbw_"):
            st.session_state.pop(key, None)
    st.session_state["pb_profile"] = dict(PROFILE_DEFAULTS)
    st.session_state["pb_items"] = {}
    st.session_state["pb_row_counts"] = {}
    st.session_state["v4_active_section"] = "Profile Setup"


def day_label(day):
    start = st.session_state["pb_profile"].get("start_date", dt.date.today())
    return f"Day {day} - {(start + dt.timedelta(days=day-1)).strftime('%a, %d %b')}"


def day_picker(key):
    st.session_state.setdefault(key, 1)
    st.markdown("<div class='hm-day'><b>Select day to edit</b><br><span style='color:#64748B;font-size:.8rem;font-weight:720;'>Row 1: Day 1 to Day 4. Row 2: Day 5 to Day 7.</span></div>", unsafe_allow_html=True)
    for row in ([1, 2, 3, 4], [5, 6, 7]):
        cols = st.columns(len(row), gap="small")
        for col, day in zip(cols, row):
            with col:
                st.button(day_label(day), key=f"{key}_{day}", type=("primary" if st.session_state[key] == day else "secondary"), use_container_width=True, on_click=lambda d=day: st.session_state.update({key: d}))
    return st.session_state[key]


def set_widget_default(widget_key, value):
    if widget_key not in st.session_state:
        st.session_state[widget_key] = value


def item_row(kind, day, slot):
    for idx in range(row_count(kind, day, slot)):
        if kind == "meal":
            fields = [("recipe", "Recipe", RECIPES, "-- Select recipe --", "select"), ("portion", "Portion", None, "", "text"), ("instruction", "Instruction", None, "", "text")]
            cols = st.columns([.44, .20, .36])
        elif kind == "exercise":
            fields = [("exercise", "Exercise", EXERCISES, "-- Select exercise --", "select"), ("time", "Time", None, "", "text"), ("intensity", "Intensity", INTENSITY_OPTIONS, SELECT_INTENSITY, "select"), ("instruction", "Instruction", None, "", "text")]
            cols = st.columns([.40, .18, .18, .24])
        else:
            fields = [("supplement", "Supplement", SUPPLEMENTS, "-- Select supplement --", "select"), ("time", "Time", None, "", "text"), ("dose", "Dosage/Frequency", None, "", "text"), ("instruction", "Instruction", None, "", "text")]
            cols = st.columns([.36, .16, .24, .24])
        for col, (field, label, options, default, field_type) in zip(cols, fields):
            key = item_widget_key(kind, day, slot, idx, field)
            set_widget_default(key, item_value(kind, day, slot, idx, field, default))
            if field_type == "select":
                col.selectbox(label, ensure_options(options, st.session_state[key]), key=key, on_change=sync_item_field, args=(kind, day, slot, idx, field))
            else:
                placeholder = "HH:MM" if field == "time" else None
                col.text_input(label, key=key, placeholder=placeholder, on_change=sync_item_field, args=(kind, day, slot, idx, field))
    label = {"meal": "Add food item", "exercise": "Add workout item", "supplement": "Add supplement item"}[kind]
    if st.button(label, key=f"add_{kind}_{day}_{slot}", use_container_width=True):
        sync_visible_item_widgets()
        add_row(kind, day, slot)
        st.rerun()


def collect_items():
    sync_visible_item_widgets()
    rows = []
    for kind, slots in (("meal", MEAL_SLOTS), ("exercise", EXERCISE_SLOTS), ("supplement", SUPPLEMENT_SLOTS)):
        for day in range(1, 8):
            for slot in slots:
                for idx in range(row_count(kind, day, slot)):
                    if kind == "meal":
                        rows.append({"item_type": "meal", "day_number": day, "slot_name": slot, "item_order": idx + 1, "reference_label": clean_choice(item_value(kind, day, slot, idx, "recipe")), "portion": item_value(kind, day, slot, idx, "portion"), "instruction": item_value(kind, day, slot, idx, "instruction")})
                    elif kind == "exercise":
                        rows.append({"item_type": "exercise", "day_number": day, "slot_name": slot, "item_order": idx + 1, "reference_label": clean_choice(item_value(kind, day, slot, idx, "exercise")), "scheduled_time": item_value(kind, day, slot, idx, "time"), "intensity": clean_choice(item_value(kind, day, slot, idx, "intensity")), "instruction": item_value(kind, day, slot, idx, "instruction")})
                    else:
                        rows.append({"item_type": "supplement", "day_number": day, "slot_name": slot, "item_order": idx + 1, "reference_label": clean_choice(item_value(kind, day, slot, idx, "supplement")), "scheduled_time": item_value(kind, day, slot, idx, "time"), "dosage_frequency": item_value(kind, day, slot, idx, "dose"), "instruction": item_value(kind, day, slot, idx, "instruction")})
    return rows


def apply_profile_to_session(profile, items):
    reset_new_draft()
    st.session_state["pb_profile"] = {"id": profile.get("id", ""), "profile_name": profile.get("profile_name", ""), "clone_from": profile.get("clone_source_label") or "New profile", "change_note": profile.get("change_note") or "", "status": "Draft", "region": profile.get("region") or "", "age_band": profile.get("age_band") or SELECT_AGE, "concerns": list(profile.get("health_concerns") or []), "diet_type": profile.get("diet_type") or SELECT_DIET, "member": profile.get("assigned_member_label") or "Select member", "note": profile.get("profile_note") or "", "start_date": clean_date(profile.get("start_date"))}
    for row in items:
        kind = row.get("item_type")
        day = int(row.get("day_number") or 0)
        slot = row.get("slot_name") or ""
        idx = int(row.get("item_order") or 1) - 1
        if kind not in {"meal", "exercise", "supplement"} or not slot:
            continue
        st.session_state["pb_row_counts"][f"{kind}|{day}|{slot}"] = max(row_count(kind, day, slot), idx + 1)
        if kind == "meal":
            values = {"recipe": row.get("reference_label") or "-- Select recipe --", "portion": row.get("portion") or "", "instruction": row.get("instruction") or ""}
        elif kind == "exercise":
            values = {"exercise": row.get("reference_label") or "-- Select exercise --", "time": row.get("scheduled_time") or "", "intensity": row.get("intensity") or SELECT_INTENSITY, "instruction": row.get("instruction") or ""}
        else:
            values = {"supplement": row.get("reference_label") or "-- Select supplement --", "time": row.get("scheduled_time") or "", "dose": row.get("dosage_frequency") or "", "instruction": row.get("instruction") or ""}
        for field, value in values.items():
            st.session_state["pb_items"][item_key(kind, day, slot, idx, field)] = value


def current_profile_payload(member_label_to_id, clone_label_to_id):
    sync_profile_all()
    p = st.session_state["pb_profile"]
    member_label = p.get("member", "Select member")
    start_date = p.get("start_date", dt.date.today())
    return {"id": p.get("id", ""), "profile_name": p.get("profile_name", ""), "region": p.get("region", ""), "age_band": clean_choice(p.get("age_band", "")), "diet_type": clean_choice(p.get("diet_type", "")), "health_concerns": p.get("concerns", []), "profile_note": p.get("note", ""), "change_note": p.get("change_note", ""), "cycle_rule": "Weekly cyclical until replaced or stopped", "assigned_member_id": member_label_to_id.get(member_label, "") if not is_select(member_label) else "", "assigned_member_label": member_label if not is_select(member_label) else "", "start_date": start_date.isoformat() if isinstance(start_date, dt.date) else str(start_date or ""), "clone_source_profile_id": clone_label_to_id.get(p.get("clone_from", ""), ""), "clone_source_label": p.get("clone_from", "New profile"), "created_by_user_id": st.session_state.get("user_id", ""), "created_by_email": st.session_state.get("user_email", "")}

ensure_state()

st.markdown("<div class='hm-section-nav'>", unsafe_allow_html=True)
nav_cols = st.columns([1, 1, 1, 1, .9], gap="small")
for col, section_name in zip(nav_cols, SECTIONS):
    with col:
        st.button(NAV_LABELS[section_name], key=f"v4_nav_{section_name}", type=("primary" if st.session_state["v4_active_section"] == section_name else "secondary"), use_container_width=True, on_click=set_section, args=(section_name,))
st.markdown("</div>", unsafe_allow_html=True)
st.markdown("<div class='hm-section-rule'></div>", unsafe_allow_html=True)

if STORE_STATUS.get("ok"):
    st.markdown("<div class='hm-readiness-strip hm-ready-ok'><b>Sprint 1 draft store is ready.</b> Draft save/load is enabled.</div>", unsafe_allow_html=True)
else:
    st.markdown(f"<div class='hm-readiness-strip hm-ready-warn'><b>Sprint 1 draft store is not ready.</b> {STORE_STATUS.get('message', 'Run the Sprint 1 SQL script, then refresh this page.')}</div>", unsafe_allow_html=True)
    if st.button("Refresh Backend Status", use_container_width=True):
        clear_pb_cache(); st.rerun()

flash = st.session_state.pop("v4_flash_success", "")
if flash:
    st.success(flash)

section = st.session_state["v4_active_section"]

if section == "Profile Setup":
    member_options, member_message = cached_members()
    member_label_to_id = {row["label"]: row["id"] for row in member_options}
    ok_sources, source_profiles, _ = cached_profile_sources()
    clone_options = ["New profile"]
    clone_label_to_id = {"New profile": ""}
    if ok_sources and source_profiles:
        for p in source_profiles:
            label = f"{p.get('profile_name', 'Untitled')} [{p.get('status', 'draft')}]"
            clone_options.append(label); clone_label_to_id[label] = p.get("id", "")
    p = st.session_state["pb_profile"]
    p["clone_from"] = p.get("clone_from") if p.get("clone_from") in clone_options else "New profile"
    p["member"] = p.get("member") if p.get("member") in member_label_to_id else "Select member"

    st.markdown("<div class='hm-title'>Recommendation Profile Setup</div><div class='hm-sub'>Reusable profile with cloning, categorisation, member assignment and cycle context.</div>", unsafe_allow_html=True)
    st.markdown("<div class='hm-store-box'>", unsafe_allow_html=True)
    st.caption(f"Dropdown source: {SOURCE_MESSAGE} Member source: {member_message}")
    ok_drafts, drafts, draft_msg = cached_drafts()
    draft_label_to_id = {"-- Select saved draft --": ""}
    if ok_drafts:
        for d in drafts:
            draft_label_to_id[f"{d.get('profile_name', 'Untitled draft')} · {str(d.get('updated_at', ''))[:16]}"] = d.get("id", "")
    st.markdown("<div class='hm-load-label'>Load saved draft</div>", unsafe_allow_html=True)
    load_cols = st.columns([.58, .21, .21], gap="medium")
    selected_draft_label = load_cols[0].selectbox("Load saved draft", list(draft_label_to_id.keys()), key="v4_load_draft_choice", label_visibility="collapsed")
    if load_cols[1].button("Load Draft", use_container_width=True, disabled=not bool(draft_label_to_id.get(selected_draft_label))):
        ok, profile_payload, item_payload, message = load_profile(draft_label_to_id.get(selected_draft_label, ""))
        if ok:
            apply_profile_to_session(profile_payload, item_payload)
            st.session_state["v4_flash_success"] = message
            st.rerun()
        st.error(message)
    if load_cols[2].button("New Draft", use_container_width=True):
        reset_new_draft()
        st.session_state["v4_flash_success"] = "New blank draft started."
        st.rerun()
    if not ok_drafts and STORE_STATUS.get("ok"):
        st.caption(draft_msg)
    if p.get("id"):
        st.caption(f"Current draft id: {p.get('id')}")
    st.markdown("</div>", unsafe_allow_html=True)

    for field in PROFILE_DEFAULTS:
        set_widget_default(profile_widget_key(field), p.get(field, PROFILE_DEFAULTS[field]))

    c1, c2 = st.columns(2, gap="large")
    with c1:
        st.text_input("Profile Name", key=profile_widget_key("profile_name"), on_change=sync_profile_field, args=("profile_name",))
        st.selectbox("Clone From Existing Profile", ensure_options(clone_options, p.get("clone_from")), key=profile_widget_key("clone_from"), on_change=sync_profile_field, args=("clone_from",))
        st.text_input("Change Note", key=profile_widget_key("change_note"), on_change=sync_profile_field, args=("change_note",))
        st.text_input("Profile Status", value="Draft", disabled=True)
    with c2:
        st.text_input("Region / Food Culture", key=profile_widget_key("region"), on_change=sync_profile_field, args=("region",))
        st.selectbox("Age Band", ensure_options(AGE_BANDS, p.get("age_band")), key=profile_widget_key("age_band"), on_change=sync_profile_field, args=("age_band",))
        st.multiselect("Health Concerns", ensure_options(HEALTH_CONCERNS, p.get("concerns")), key=profile_widget_key("concerns"), on_change=sync_profile_field, args=("concerns",))
        st.selectbox("Diet Type", ensure_options(DIET_TYPES, p.get("diet_type")), key=profile_widget_key("diet_type"), on_change=sync_profile_field, args=("diet_type",))
    a1, a2 = st.columns(2, gap="large")
    with a1:
        st.selectbox("Example Member Assignment", list(member_label_to_id.keys()), key=profile_widget_key("member"), on_change=sync_profile_field, args=("member",))
        st.text_area("Profile-level Nutritionist Note", height=150, key=profile_widget_key("note"), on_change=sync_profile_field, args=("note",))
    with a2:
        st.date_input("Plan Start Date", key=profile_widget_key("start_date"), on_change=sync_profile_field, args=("start_date",))
        st.text_input("Cycle Rule", value="Weekly cyclical until replaced or stopped", disabled=True)
        st.text_input("Implementation Status", value="Sprint 1: draft save/load only. Publish not enabled.", disabled=True)
    if st.button("Save Draft Profile", type="primary", use_container_width=True, disabled=not STORE_STATUS.get("ok")):
        ok, profile_id, message = save_draft_profile(current_profile_payload(member_label_to_id, clone_label_to_id), collect_items())
        if ok:
            st.session_state["pb_profile"]["id"] = profile_id
            cached_drafts.clear(); cached_profile_sources.clear()
            st.session_state["v4_flash_success"] = message
            st.rerun()
        st.error(message)

elif section == "Meal Structure":
    day = day_picker("v4_meal_day")
    for slot in MEAL_SLOTS:
        st.markdown(f"<div class='hm-slot'>{slot}</div>", unsafe_allow_html=True)
        item_row("meal", day, slot)
    x, y = st.columns(2)
    x.button("Copy Day 1 to all days", key=f"v4_meal_copy_all_{day}", use_container_width=True)
    y.button("Copy previous day", key=f"v4_meal_copy_prev_{day}", use_container_width=True)

elif section == "Exercise Regime":
    day = day_picker("v4_exercise_day")
    for slot in EXERCISE_SLOTS:
        st.markdown(f"<div class='hm-slot'>{slot}</div>", unsafe_allow_html=True)
        item_row("exercise", day, slot)
    x, y, z = st.columns(3)
    x.button("Copy Day 1 to all days", key=f"v4_ex_copy_all_{day}", use_container_width=True)
    y.button("Copy previous day", key=f"v4_ex_copy_prev_{day}", use_container_width=True)
    z.button("Add preferred-time slot", key=f"v4_ex_add_pref_{day}", use_container_width=True)

elif section == "Supplement Regime":
    day = day_picker("v4_supp_day")
    for slot in SUPPLEMENT_SLOTS:
        st.markdown(f"<div class='hm-slot'>{slot}</div>", unsafe_allow_html=True)
        item_row("supplement", day, slot)
    x, y, z = st.columns(3)
    x.button("Copy active regimen", key=f"v4_supp_active_{day}", use_container_width=True)
    y.button("Copy Day 1 to all days", key=f"v4_supp_all_{day}", use_container_width=True)
    z.button("Copy previous day", key=f"v4_supp_prev_{day}", use_container_width=True)

else:
    sync_profile_all()
    p = st.session_state["pb_profile"]
    assigned_member = p.get("member", "Select member")
    member_ready = assigned_member != "Select member"
    member_pill = "hm-ok" if member_ready else "hm-pending"
    member_status = "Complete" if member_ready else "Pending"
    plan_start = p.get("start_date", dt.date.today())
    concerns = p.get("concerns", [])
    st.markdown("<div class='hm-title'>Preview & End-to-End Flow Review</div><div class='hm-sub'>Sprint 1 is draft-only. Publish and member consumption remain disabled.</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='hm-preview'><b>Profile Summary</b><br><b>Draft ID:</b> {p.get('id') or 'Not saved yet'}<br><b>Profile:</b> {p.get('profile_name') or 'Not entered yet'}<br><b>Status:</b> Draft<br><b>Assigned Member:</b> {display_choice(assigned_member)}<br><b>Start Date:</b> {plan_start.isoformat() if isinstance(plan_start, dt.date) else plan_start}<br><b>Tags:</b> {p.get('region') or 'NA'} - {display_choice(p.get('age_band'))} - {display_choice(p.get('diet_type'))} - {', '.join(concerns) if concerns else 'No health concern selected'}<br><b>Profile Note:</b> {p.get('note') or 'NA'}</div>", unsafe_allow_html=True)
    st.markdown(f"""
<div class='hm-preview'>
<b>Publish Readiness Checklist</b><br>
This checklist remains admin-side as the final gate before publish. In Sprint 1, it is informational only.
<div class='hm-readiness'>
  <div class='hm-readiness-item'><span class='hm-pill hm-info'>Sprint 1</span><br><b>Draft save/load enabled</b><br>Publish and member consumption are deliberately not enabled yet.</div>
  <div class='hm-readiness-item'><span class='hm-pill {member_pill}'>{member_status}</span><br><b>Member assigned</b><br>Publishing must stay blocked until a member is selected.</div>
  <div class='hm-readiness-item'><span class='hm-pill hm-info'>Future Sprint</span><br><b>Publish disabled</b><br>Active profile replacement is not part of Sprint 1.</div>
  <div class='hm-readiness-item'><span class='hm-pill hm-ok'>Safe</span><br><b>Member side untouched</b><br>No My Recommendations or Today's Journey wiring yet.</div>
</div>
</div>
""", unsafe_allow_html=True)

render_page_nav("Recommendation Profile Builder", back_page="pages/10_Admin_Dashboard.py", dashboard_page="pages/10_Admin_Dashboard.py", show_evaluation=False, show_dashboard=True, location="bottom")
render_back_to_top()
