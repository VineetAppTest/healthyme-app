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

APP_BUILD_VERSION = "v100.19"
APP_BUILD_LABEL = "Profile Builder Default Values Hotfix"

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
.hm-section-nav{margin:.35rem 0 .55rem 0;}
.hm-section-nav [data-testid="stButton"]>button{min-height:2.7rem!important;border-radius:15px!important;font-weight:930!important;border:1.15px solid rgba(216,180,98,.72)!important;background:#fff!important;color:#064E3B!important;box-shadow:0 4px 10px rgba(15,23,42,.035)!important;white-space:normal!important;overflow:visible!important;text-overflow:clip!important;line-height:1.15!important;padding:.55rem .5rem!important;}
.hm-section-nav [data-testid="stButton"]>button[kind="primary"]{background:linear-gradient(135deg,#FFF3D6,#FFFFFF)!important;border:1.5px solid #B89345!important;color:#064E3B!important;box-shadow:0 8px 18px rgba(15,23,42,.08)!important;}
.hm-section-nav [data-testid="stButton"]>button[kind="primary"] *{color:#064E3B!important;}
.hm-section-rule{height:1px;background:linear-gradient(90deg,transparent,rgba(216,168,78,.8),transparent);margin:.3rem 0 .72rem 0;}
.hm-readiness-strip{border-radius:15px;padding:.62rem .78rem;margin:.25rem 0 1rem 0;font-size:.84rem;font-weight:780;line-height:1.35;box-shadow:0 5px 12px rgba(15,23,42,.035)}
.hm-readiness-strip b{color:#064E3B!important;}.hm-ready-ok{background:#ECFDF5;border:1px solid #A7F3D0;color:#065F46;}.hm-ready-warn{background:#FFF7ED;border:1px solid #FED7AA;color:#9A3412;}
.hm-store-box{border:1px solid #E3C98E;background:#FFFDF8;border-radius:16px;padding:.85rem .9rem;margin:.35rem 0 1rem;box-shadow:0 6px 14px rgba(15,23,42,.035)}
.hm-load-label{font-size:.86rem;font-weight:760;color:#334155;margin:0 0 .28rem .05rem;}
.hm-slot{font-size:.78rem;color:#72551A;font-weight:880;margin:.75rem 0 .25rem}.hm-day{border:1px solid #E3C98E;background:white;border-radius:16px;padding:.7rem .8rem;margin:.45rem 0 .85rem}
.hm-preview{border:1px dashed #D8A84E;background:#FFF9EC;border-radius:16px;padding:.75rem .85rem;margin:.35rem 0;color:#475569;font-size:.83rem;font-weight:740;line-height:1.45}
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


def count(key):
    st.session_state.setdefault(key, 1)
    return st.session_state[key]


def set_section(section_name):
    st.session_state["v4_active_section"] = section_name


def init_defaults():
    st.session_state.setdefault("v4_profile_id", "")
    st.session_state.setdefault("v4_profile_name", "")
    st.session_state.setdefault("v4_clone_from", "New profile")
    st.session_state.setdefault("v4_change_note", "")
    st.session_state.setdefault("v4_profile_status", "Draft")
    st.session_state.setdefault("v4_region", "")
    st.session_state.setdefault("v4_age_band", SELECT_AGE)
    st.session_state.setdefault("v4_concerns", [])
    st.session_state.setdefault("v4_diet_type", SELECT_DIET)
    st.session_state.setdefault("v4_member", "Select member")
    st.session_state.setdefault("v4_note", "")
    st.session_state.setdefault("v4_start_date", dt.date.today())
    st.session_state.setdefault("v4_active_section", "Profile Setup")


def reset_new_draft():
    for key in list(st.session_state.keys()):
        if str(key).startswith("v4_") or str(key).startswith(("meal_", "exercise_", "supplement_")):
            st.session_state.pop(key, None)
    init_defaults()


def clear_item_state():
    for key in list(st.session_state.keys()):
        if str(key).startswith(("meal_", "exercise_", "supplement_")):
            st.session_state.pop(key, None)


def day_label(day):
    start = st.session_state.get("v4_start_date", dt.date.today())
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


def item_row(kind, day, slot):
    key = f"{kind}_{day}_{slot}"
    for idx in range(count(key)):
        if kind == "meal":
            a, b, c = st.columns([.44, .20, .36])
            a.selectbox("Recipe", ensure_options(RECIPES, st.session_state.get(f"{key}_recipe_{idx}")), key=f"{key}_recipe_{idx}")
            b.text_input("Portion", key=f"{key}_portion_{idx}")
            c.text_input("Instruction", key=f"{key}_instruction_{idx}")
        elif kind == "exercise":
            a, b, c, d = st.columns([.40, .18, .18, .24])
            a.selectbox("Exercise", ensure_options(EXERCISES, st.session_state.get(f"{key}_exercise_{idx}")), key=f"{key}_exercise_{idx}")
            b.text_input("Time", key=f"{key}_time_{idx}", placeholder="HH:MM")
            c.selectbox("Intensity", ensure_options(INTENSITY_OPTIONS, st.session_state.get(f"{key}_intensity_{idx}")), key=f"{key}_intensity_{idx}")
            d.text_input("Instruction", key=f"{key}_instruction_{idx}")
        else:
            a, b, c, d = st.columns([.36, .16, .24, .24])
            a.selectbox("Supplement", ensure_options(SUPPLEMENTS, st.session_state.get(f"{key}_supplement_{idx}")), key=f"{key}_supplement_{idx}")
            b.text_input("Time", key=f"{key}_time_{idx}", placeholder="HH:MM")
            c.text_input("Dosage/Frequency", key=f"{key}_dose_{idx}")
            d.text_input("Instruction", key=f"{key}_instruction_{idx}")
    label = {"meal": "Add food item", "exercise": "Add workout item", "supplement": "Add supplement item"}[kind]
    if st.button(label, key=f"add_{key}", use_container_width=True):
        st.session_state[key] = count(key) + 1
        st.rerun()


def collect_items():
    rows = []
    for kind, slots in (("meal", MEAL_SLOTS), ("exercise", EXERCISE_SLOTS), ("supplement", SUPPLEMENT_SLOTS)):
        for day in range(1, 8):
            for slot in slots:
                key = f"{kind}_{day}_{slot}"
                for idx in range(int(st.session_state.get(key, 0) or 0)):
                    if kind == "meal":
                        rows.append({"item_type": "meal", "day_number": day, "slot_name": slot, "item_order": idx + 1, "reference_label": clean_choice(st.session_state.get(f"{key}_recipe_{idx}", "")), "portion": st.session_state.get(f"{key}_portion_{idx}", ""), "instruction": st.session_state.get(f"{key}_instruction_{idx}", "")})
                    elif kind == "exercise":
                        rows.append({"item_type": "exercise", "day_number": day, "slot_name": slot, "item_order": idx + 1, "reference_label": clean_choice(st.session_state.get(f"{key}_exercise_{idx}", "")), "scheduled_time": st.session_state.get(f"{key}_time_{idx}", ""), "intensity": clean_choice(st.session_state.get(f"{key}_intensity_{idx}", "")), "instruction": st.session_state.get(f"{key}_instruction_{idx}", "")})
                    else:
                        rows.append({"item_type": "supplement", "day_number": day, "slot_name": slot, "item_order": idx + 1, "reference_label": clean_choice(st.session_state.get(f"{key}_supplement_{idx}", "")), "scheduled_time": st.session_state.get(f"{key}_time_{idx}", ""), "dosage_frequency": st.session_state.get(f"{key}_dose_{idx}", ""), "instruction": st.session_state.get(f"{key}_instruction_{idx}", "")})
    return rows


def apply_profile_to_session(profile, items):
    st.session_state["v4_profile_id"] = profile.get("id", "")
    st.session_state["v4_profile_name"] = profile.get("profile_name", "")
    st.session_state["v4_clone_from"] = profile.get("clone_source_label") or "New profile"
    st.session_state["v4_change_note"] = profile.get("change_note") or ""
    st.session_state["v4_profile_status"] = "Draft"
    st.session_state["v4_region"] = profile.get("region") or ""
    st.session_state["v4_age_band"] = profile.get("age_band") or SELECT_AGE
    st.session_state["v4_concerns"] = list(profile.get("health_concerns") or [])
    st.session_state["v4_diet_type"] = profile.get("diet_type") or SELECT_DIET
    st.session_state["v4_member"] = profile.get("assigned_member_label") or "Select member"
    st.session_state["v4_note"] = profile.get("profile_note") or ""
    st.session_state["v4_start_date"] = clean_date(profile.get("start_date"))
    clear_item_state()
    for row in items:
        kind = row.get("item_type")
        day = int(row.get("day_number") or 0)
        slot = row.get("slot_name") or ""
        if kind not in {"meal", "exercise", "supplement"} or not slot:
            continue
        base = f"{kind}_{day}_{slot}"
        idx = int(row.get("item_order") or 1) - 1
        st.session_state[base] = max(int(st.session_state.get(base, 0) or 0), idx + 1)
        if kind == "meal":
            st.session_state[f"{base}_recipe_{idx}"] = row.get("reference_label") or "-- Select recipe --"
            st.session_state[f"{base}_portion_{idx}"] = row.get("portion") or ""
            st.session_state[f"{base}_instruction_{idx}"] = row.get("instruction") or ""
        elif kind == "exercise":
            st.session_state[f"{base}_exercise_{idx}"] = row.get("reference_label") or "-- Select exercise --"
            st.session_state[f"{base}_time_{idx}"] = row.get("scheduled_time") or ""
            st.session_state[f"{base}_intensity_{idx}"] = row.get("intensity") or SELECT_INTENSITY
            st.session_state[f"{base}_instruction_{idx}"] = row.get("instruction") or ""
        else:
            st.session_state[f"{base}_supplement_{idx}"] = row.get("reference_label") or "-- Select supplement --"
            st.session_state[f"{base}_time_{idx}"] = row.get("scheduled_time") or ""
            st.session_state[f"{base}_dose_{idx}"] = row.get("dosage_frequency") or ""
            st.session_state[f"{base}_instruction_{idx}"] = row.get("instruction") or ""


def member_sources():
    options, message = cached_members()
    return options, {row["label"]: row["id"] for row in options}, message


def current_profile_payload(member_label_to_id, clone_label_to_id):
    start_date = st.session_state.get("v4_start_date", dt.date.today())
    member_label = st.session_state.get("v4_member", "Select member")
    return {
        "id": st.session_state.get("v4_profile_id", ""),
        "profile_name": st.session_state.get("v4_profile_name", ""),
        "region": st.session_state.get("v4_region", ""),
        "age_band": clean_choice(st.session_state.get("v4_age_band", "")),
        "diet_type": clean_choice(st.session_state.get("v4_diet_type", "")),
        "health_concerns": st.session_state.get("v4_concerns", []),
        "profile_note": st.session_state.get("v4_note", ""),
        "change_note": st.session_state.get("v4_change_note", ""),
        "cycle_rule": "Weekly cyclical until replaced or stopped",
        "assigned_member_id": member_label_to_id.get(member_label, "") if not is_select(member_label) else "",
        "assigned_member_label": member_label if not is_select(member_label) else "",
        "start_date": start_date.isoformat() if isinstance(start_date, dt.date) else str(start_date or ""),
        "clone_source_profile_id": clone_label_to_id.get(st.session_state.get("v4_clone_from", ""), ""),
        "clone_source_label": st.session_state.get("v4_clone_from", "New profile"),
        "created_by_user_id": st.session_state.get("user_id", ""),
        "created_by_email": st.session_state.get("user_email", ""),
    }

init_defaults()

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
    member_options, member_label_to_id, member_message = member_sources()
    ok_sources, source_profiles, _ = cached_profile_sources()
    clone_options = ["New profile"]
    clone_label_to_id = {"New profile": ""}
    if ok_sources and source_profiles:
        for p in source_profiles:
            label = f"{p.get('profile_name', 'Untitled')} [{p.get('status', 'draft')}]"
            clone_options.append(label); clone_label_to_id[label] = p.get("id", "")

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
    if st.session_state.get("v4_profile_id"):
        st.caption(f"Current draft id: {st.session_state.get('v4_profile_id')}")
    st.markdown("</div>", unsafe_allow_html=True)

    st.session_state["v4_clone_from"] = st.session_state.get("v4_clone_from") if st.session_state.get("v4_clone_from") in clone_options else "New profile"
    st.session_state["v4_member"] = st.session_state.get("v4_member") if st.session_state.get("v4_member") in member_label_to_id else "Select member"

    c1, c2 = st.columns(2, gap="large")
    with c1:
        st.text_input("Profile Name", key="v4_profile_name")
        st.selectbox("Clone From Existing Profile", ensure_options(clone_options, st.session_state.get("v4_clone_from")), key="v4_clone_from")
        st.text_input("Change Note", key="v4_change_note")
        st.selectbox("Profile Status", ["Draft", "Active", "Archived"], key="v4_profile_status", disabled=True)
    with c2:
        st.text_input("Region / Food Culture", key="v4_region")
        st.selectbox("Age Band", ensure_options(AGE_BANDS, st.session_state.get("v4_age_band")), key="v4_age_band")
        st.multiselect("Health Concerns", ensure_options(HEALTH_CONCERNS, st.session_state.get("v4_concerns")), key="v4_concerns")
        st.selectbox("Diet Type", ensure_options(DIET_TYPES, st.session_state.get("v4_diet_type")), key="v4_diet_type")
    a1, a2 = st.columns(2, gap="large")
    with a1:
        st.selectbox("Example Member Assignment", list(member_label_to_id.keys()), key="v4_member")
        st.text_area("Profile-level Nutritionist Note", height=150, key="v4_note")
    with a2:
        st.date_input("Plan Start Date", key="v4_start_date")
        st.text_input("Cycle Rule", value="Weekly cyclical until replaced or stopped", disabled=True, key="v4_cycle")
        st.text_input("Implementation Status", value="Sprint 1: draft save/load only. Publish not enabled.", disabled=True, key="v4_status")
    if st.button("Save Draft Profile", type="primary", use_container_width=True, disabled=not STORE_STATUS.get("ok")):
        ok, profile_id, message = save_draft_profile(current_profile_payload(member_label_to_id, clone_label_to_id), collect_items())
        if ok:
            st.session_state["v4_profile_id"] = profile_id
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
    assigned_member = st.session_state.get("v4_member", "Select member")
    member_ready = assigned_member != "Select member"
    member_pill = "hm-ok" if member_ready else "hm-pending"
    member_status = "Complete" if member_ready else "Pending"
    plan_start = st.session_state.get("v4_start_date", dt.date.today())
    concerns = st.session_state.get("v4_concerns", [])
    st.markdown("<div class='hm-title'>Preview & End-to-End Flow Review</div><div class='hm-sub'>Sprint 1 is draft-only. Publish and member consumption remain disabled.</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='hm-preview'><b>Profile Summary</b><br><b>Draft ID:</b> {st.session_state.get('v4_profile_id') or 'Not saved yet'}<br><b>Profile:</b> {st.session_state.get('v4_profile_name', '') or 'Not entered yet'}<br><b>Status:</b> {st.session_state.get('v4_profile_status', 'Draft')}<br><b>Assigned Member:</b> {display_choice(assigned_member)}<br><b>Start Date:</b> {plan_start.isoformat() if isinstance(plan_start, dt.date) else plan_start}<br><b>Tags:</b> {st.session_state.get('v4_region', '') or 'NA'} - {display_choice(st.session_state.get('v4_age_band', ''))} - {display_choice(st.session_state.get('v4_diet_type', ''))} - {', '.join(concerns) if concerns else 'No health concern selected'}<br><b>Profile Note:</b> {st.session_state.get('v4_note', '') or 'NA'}</div>", unsafe_allow_html=True)
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
