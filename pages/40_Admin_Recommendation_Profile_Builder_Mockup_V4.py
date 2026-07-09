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

APP_BUILD_VERSION = "v100.16"
APP_BUILD_LABEL = "Profile Builder Sprint 1 Draft UX"

st.set_page_config(page_title="Recommendation Profile Builder Sprint 1", page_icon="💚", layout="wide", initial_sidebar_state="collapsed")
inject_global_styles()
apply_luxe_theme()
require_admin()
utility_logout_bar()

st.markdown(
    f"""
    <div class='hero-shell'>
      <div class='hm-v10016-brand-row'>
        <span class='hm-v10016-brand'>HealthyMe</span>
        <span class='hm-v10016-version-inline'>{APP_BUILD_VERSION} · {APP_BUILD_LABEL}</span>
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
.hm-v10016-brand-row{display:flex;align-items:baseline;gap:.55rem;flex-wrap:wrap;margin-bottom:.35rem;}
.hm-v10016-brand{color:#064E3B;font-size:.82rem;font-weight:950;letter-spacing:.02em;text-transform:uppercase;}
.hm-v10016-version-inline{color:#72551A;font-size:.72rem;font-weight:900;background:#F5E7C8;border-radius:999px;padding:.22rem .55rem;}
.hm-title{color:#064E3B;font-size:1.04rem;font-weight:950;margin:0 0 .25rem}.hm-sub{color:#64748B;font-size:.82rem;font-weight:720;margin:0 0 .7rem}
.hm-slot{font-size:.78rem;color:#72551A;font-weight:880;margin:.75rem 0 .25rem}.hm-head{font-size:.68rem;text-transform:uppercase;color:#64748B;font-weight:950;margin:.12rem 0 -.12rem}
.hm-day{border:1px solid #E3C98E;background:white;border-radius:16px;padding:.7rem .8rem;margin:.45rem 0 .85rem}.hm-day [data-testid="stButton"]>button{min-height:2.35rem!important;border-radius:14px!important;font-weight:900!important}
.hm-section-nav{margin:.35rem 0 .55rem 0;}
.hm-section-nav [data-testid="stButton"]>button{min-height:2.7rem!important;border-radius:15px!important;font-weight:930!important;border:1.15px solid rgba(216,180,98,.72)!important;background:#fff!important;color:#064E3B!important;box-shadow:0 4px 10px rgba(15,23,42,.035)!important;white-space:normal!important;overflow:visible!important;text-overflow:clip!important;line-height:1.15!important;padding:.55rem .5rem!important;}
.hm-section-nav [data-testid="stButton"]>button *{white-space:normal!important;overflow:visible!important;text-overflow:clip!important;line-height:1.15!important;}
.hm-section-nav [data-testid="stButton"]>button[kind="primary"]{background:linear-gradient(135deg,#FFF3D6,#FFFFFF)!important;border:1.5px solid #B89345!important;color:#064E3B!important;box-shadow:0 8px 18px rgba(15,23,42,.08)!important;}
.hm-section-nav [data-testid="stButton"]>button[kind="primary"] *{color:#064E3B!important;}
.hm-section-rule{height:1px;background:linear-gradient(90deg,transparent,rgba(216,168,78,.8),transparent);margin:.3rem 0 .72rem 0;}
.hm-readiness-strip{border-radius:15px;padding:.62rem .78rem;margin:.25rem 0 1rem 0;font-size:.84rem;font-weight:780;line-height:1.35;box-shadow:0 5px 12px rgba(15,23,42,.035)}
.hm-readiness-strip b{color:#064E3B!important;}
.hm-ready-ok{background:#ECFDF5;border:1px solid #A7F3D0;color:#065F46;}
.hm-ready-warn{background:#FFF7ED;border:1px solid #FED7AA;color:#9A3412;}
.hm-preview{border:1px dashed #D8A84E;background:#FFF9EC;border-radius:16px;padding:.75rem .85rem;margin:.35rem 0;color:#475569;font-size:.83rem;font-weight:740;line-height:1.45}
.hm-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:.7rem;margin:.55rem 0}.hm-mini{border:1px solid #E3C98E;background:#fff;border-radius:16px;padding:.75rem .85rem}.hm-mini b{color:#064E3B}
.hm-readiness{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:.55rem;margin:.55rem 0 0}.hm-readiness-item{background:#fff;border:1px solid #E3C98E;border-radius:14px;padding:.58rem .68rem;line-height:1.35}
.hm-pill{display:inline-block;border-radius:999px;padding:.13rem .5rem;margin:.15rem .2rem .15rem 0;font-size:.7rem;font-weight:950}.hm-ok{background:#ECFDF5;color:#047857;border:1px solid #A7F3D0}.hm-pending{background:#FFF7ED;color:#B45309;border:1px solid #FED7AA}.hm-info{background:#EFF6FF;color:#1D4ED8;border:1px solid #BFDBFE}
.hm-member-flow{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:.7rem;margin:.55rem 0}.hm-member-card{border:1px solid #E3C98E;background:#fff;border-radius:16px;padding:.8rem .9rem;min-height:8rem}.hm-member-card b{display:block;color:#064E3B;font-size:.92rem;margin-bottom:.32rem}.hm-member-card span{color:#475569;font-size:.82rem;font-weight:740;line-height:1.45}
.hm-store-box{border:1px solid #E3C98E;background:#FFFDF8;border-radius:16px;padding:.85rem .9rem;margin:.35rem 0 1rem;box-shadow:0 6px 14px rgba(15,23,42,.035)}
@media(max-width:900px){.hm-member-flow,.hm-grid,.hm-readiness{grid-template-columns:1fr}.hm-section-nav [data-testid="stButton"]>button{min-height:2.45rem!important;}}
</style>
""", unsafe_allow_html=True)

MEAL_SLOTS = ["Wake-up / Early Morning", "Breakfast", "Mid-morning Snack", "Lunch", "Evening Snack / Tea", "Dinner", "Bedtime"]
EXERCISE_SLOTS = ["Morning", "Evening", "Preferred Time"]
SUPPLEMENT_SLOTS = ["Morning", "Afternoon", "Evening", "Before Bed", "Preferred Time"]
SECTIONS = ["Profile Setup", "Meal Structure", "Exercise Regime", "Supplement Regime", "Preview & End-to-End Flow"]
NAV_LABELS = {
    "Profile Setup": "Profile Setup",
    "Meal Structure": "Meal Structure",
    "Exercise Regime": "Exercise Regime",
    "Supplement Regime": "Supplement Regime",
    "Preview & End-to-End Flow": "Preview & Flow",
}

STORE_STATUS = check_profile_builder_store()
SOURCES, SOURCE_MESSAGE = load_profile_builder_sources()
MEMBER_OPTIONS, MEMBER_MESSAGE = load_member_options()
MEMBER_LABEL_TO_ID = {row["label"]: row["id"] for row in MEMBER_OPTIONS}

RECIPES = SOURCES.get("recipe", ["-- Select recipe --"])
EXERCISES = SOURCES.get("exercise", ["-- Select exercise --"])
SUPPLEMENTS = SOURCES.get("supplement", ["-- Select supplement --"])
AGE_BANDS = SOURCES.get("age_band", ["31-45"])
HEALTH_CONCERNS = SOURCES.get("health_concern", ["Weight Management"])
DIET_TYPES = SOURCES.get("diet_type", ["Vegetarian"])


def ensure_options(options, selected=None):
    values = list(options or [])
    if selected is None:
        return values
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
    if not value:
        return dt.date.today()
    try:
        return dt.date.fromisoformat(str(value)[:10])
    except Exception:
        return dt.date.today()


def parse_time(value, default_time):
    if isinstance(value, dt.time):
        return value
    if not value:
        return default_time
    try:
        hour, minute = str(value)[:5].split(":")
        return dt.time(int(hour), int(minute))
    except Exception:
        return default_time


def time_to_text(value):
    if isinstance(value, dt.time):
        return value.strftime("%H:%M")
    return str(value or "").strip()


def base_date():
    return st.session_state.get("v4_start_date", dt.date.today())


def day_label(day):
    return f"Day {day} - {(base_date() + dt.timedelta(days=day-1)).strftime('%a, %d %b')}"


def count(key):
    st.session_state.setdefault(key, 1)
    return st.session_state[key]


def add_row(key):
    st.session_state[key] = count(key) + 1


def day_picker(key):
    st.session_state.setdefault(key, 1)
    st.markdown("<div class='hm-day'><b>Select day to edit</b><br><span style='color:#64748B;font-size:.8rem;font-weight:720;'>Row 1: Day 1 to Day 4. Row 2: Day 5 to Day 7.</span></div>", unsafe_allow_html=True)
    for row in ([1, 2, 3, 4], [5, 6, 7]):
        cols = st.columns(len(row), gap="small")
        for col, day in zip(cols, row):
            with col:
                if st.button(day_label(day), key=f"{key}_{day}", type=("primary" if st.session_state[key] == day else "secondary"), use_container_width=True):
                    st.session_state[key] = day
    return st.session_state[key]


def item_row(kind, day, slot):
    key = f"{kind}_{day}_{slot}"
    for idx in range(count(key)):
        if kind == "meal":
            recipe_key = f"{key}_recipe_{idx}"
            st.markdown("<div class='hm-head'>Recipe - Portion - Instruction</div>", unsafe_allow_html=True)
            a, b, c = st.columns([.44, .20, .36])
            a.selectbox("Recipe", ensure_options(RECIPES, st.session_state.get(recipe_key)), key=recipe_key, label_visibility="collapsed")
            b.text_input("Portion", key=f"{key}_portion_{idx}", label_visibility="collapsed")
            c.text_input("Instruction", key=f"{key}_instruction_{idx}", label_visibility="collapsed")
        elif kind == "exercise":
            exercise_key = f"{key}_exercise_{idx}"
            st.markdown("<div class='hm-head'>Exercise - Time - Intensity - Instruction</div>", unsafe_allow_html=True)
            a, b, c, d = st.columns([.40, .18, .18, .24])
            a.selectbox("Exercise", ensure_options(EXERCISES, st.session_state.get(exercise_key)), key=exercise_key, label_visibility="collapsed")
            b.time_input("Time", value=st.session_state.get(f"{key}_time_{idx}", dt.time(7, 0)), key=f"{key}_time_{idx}", label_visibility="collapsed")
            c.selectbox("Intensity", ensure_options(["Low", "Moderate", "High", "As tolerated"], st.session_state.get(f"{key}_intensity_{idx}")), key=f"{key}_intensity_{idx}", label_visibility="collapsed")
            d.text_input("Instruction", key=f"{key}_instruction_{idx}", label_visibility="collapsed")
        else:
            supplement_key = f"{key}_supplement_{idx}"
            st.markdown("<div class='hm-head'>Supplement - Time - Dosage/Frequency - Instruction</div>", unsafe_allow_html=True)
            a, b, c, d = st.columns([.36, .16, .24, .24])
            a.selectbox("Supplement", ensure_options(SUPPLEMENTS, st.session_state.get(supplement_key)), key=supplement_key, label_visibility="collapsed")
            b.time_input("Time", value=st.session_state.get(f"{key}_time_{idx}", dt.time(8, 0)), key=f"{key}_time_{idx}", label_visibility="collapsed")
            c.text_input("Dosage/Frequency", key=f"{key}_dose_{idx}", label_visibility="collapsed")
            d.text_input("Instruction", key=f"{key}_instruction_{idx}", label_visibility="collapsed")
    label = {"meal": "Add food item", "exercise": "Add workout item", "supplement": "Add supplement item"}[kind]
    if st.button(label, key=f"add_{key}", use_container_width=True):
        add_row(key)
        st.rerun()


def collect_items():
    rows = []
    for kind, slots in (("meal", MEAL_SLOTS), ("exercise", EXERCISE_SLOTS), ("supplement", SUPPLEMENT_SLOTS)):
        for day in range(1, 8):
            for slot in slots:
                key = f"{kind}_{day}_{slot}"
                for idx in range(int(st.session_state.get(key, 0) or 0)):
                    if kind == "meal":
                        rows.append({
                            "item_type": "meal",
                            "day_number": day,
                            "slot_name": slot,
                            "item_order": idx + 1,
                            "reference_label": st.session_state.get(f"{key}_recipe_{idx}", ""),
                            "portion": st.session_state.get(f"{key}_portion_{idx}", ""),
                            "instruction": st.session_state.get(f"{key}_instruction_{idx}", ""),
                        })
                    elif kind == "exercise":
                        rows.append({
                            "item_type": "exercise",
                            "day_number": day,
                            "slot_name": slot,
                            "item_order": idx + 1,
                            "reference_label": st.session_state.get(f"{key}_exercise_{idx}", ""),
                            "scheduled_time": time_to_text(st.session_state.get(f"{key}_time_{idx}")),
                            "intensity": st.session_state.get(f"{key}_intensity_{idx}", ""),
                            "instruction": st.session_state.get(f"{key}_instruction_{idx}", ""),
                        })
                    else:
                        rows.append({
                            "item_type": "supplement",
                            "day_number": day,
                            "slot_name": slot,
                            "item_order": idx + 1,
                            "reference_label": st.session_state.get(f"{key}_supplement_{idx}", ""),
                            "scheduled_time": time_to_text(st.session_state.get(f"{key}_time_{idx}")),
                            "dosage_frequency": st.session_state.get(f"{key}_dose_{idx}", ""),
                            "instruction": st.session_state.get(f"{key}_instruction_{idx}", ""),
                        })
    return rows


def selected_member_id():
    return MEMBER_LABEL_TO_ID.get(st.session_state.get("v4_member", "Select member"), "")


def current_profile_payload(clone_label_to_id):
    start_date = st.session_state.get("v4_start_date", dt.date.today())
    return {
        "id": st.session_state.get("v4_profile_id", ""),
        "profile_name": st.session_state.get("v4_profile_name", ""),
        "region": st.session_state.get("v4_region", ""),
        "age_band": st.session_state.get("v4_age_band", ""),
        "diet_type": st.session_state.get("v4_diet_type", ""),
        "health_concerns": st.session_state.get("v4_concerns", []),
        "profile_note": st.session_state.get("v4_note", ""),
        "change_note": st.session_state.get("v4_change_note", ""),
        "cycle_rule": "Weekly cyclical until replaced or stopped",
        "assigned_member_id": selected_member_id(),
        "assigned_member_label": st.session_state.get("v4_member", "Select member"),
        "start_date": start_date.isoformat() if isinstance(start_date, dt.date) else str(start_date or ""),
        "clone_source_profile_id": clone_label_to_id.get(st.session_state.get("v4_clone_from", ""), ""),
        "clone_source_label": st.session_state.get("v4_clone_from", "New profile"),
        "created_by_user_id": st.session_state.get("user_id", ""),
        "created_by_email": st.session_state.get("user_email", ""),
    }


def clear_item_state():
    for key in list(st.session_state.keys()):
        if str(key).startswith(("meal_", "exercise_", "supplement_")):
            st.session_state.pop(key, None)


def apply_profile_to_session(profile, items):
    st.session_state["v4_profile_id"] = profile.get("id", "")
    st.session_state["v4_profile_name"] = profile.get("profile_name", "")
    st.session_state["v4_clone_from"] = profile.get("clone_source_label") or "New profile"
    st.session_state["v4_change_note"] = profile.get("change_note") or ""
    st.session_state["v4_profile_status"] = "Draft"
    st.session_state["v4_region"] = profile.get("region") or ""
    st.session_state["v4_age_band"] = profile.get("age_band") or "31-45"
    st.session_state["v4_concerns"] = list(profile.get("health_concerns") or [])
    st.session_state["v4_diet_type"] = profile.get("diet_type") or "Vegetarian"
    st.session_state["v4_member"] = profile.get("assigned_member_label") or "Select member"
    st.session_state["v4_note"] = profile.get("profile_note") or ""
    st.session_state["v4_start_date"] = clean_date(profile.get("start_date"))

    clear_item_state()
    grouped = {}
    for row in items:
        kind = row.get("item_type")
        day = int(row.get("day_number") or 0)
        slot = row.get("slot_name") or ""
        if kind not in {"meal", "exercise", "supplement"} or not (1 <= day <= 7) or not slot:
            continue
        grouped.setdefault((kind, day, slot), []).append(row)

    for (kind, day, slot), rows in grouped.items():
        base = f"{kind}_{day}_{slot}"
        st.session_state[base] = len(rows)
        for idx, row in enumerate(sorted(rows, key=lambda r: int(r.get("item_order") or 1))):
            if kind == "meal":
                st.session_state[f"{base}_recipe_{idx}"] = row.get("reference_label") or "-- Select recipe --"
                st.session_state[f"{base}_portion_{idx}"] = row.get("portion") or ""
                st.session_state[f"{base}_instruction_{idx}"] = row.get("instruction") or ""
            elif kind == "exercise":
                st.session_state[f"{base}_exercise_{idx}"] = row.get("reference_label") or "-- Select exercise --"
                st.session_state[f"{base}_time_{idx}"] = parse_time(row.get("scheduled_time"), dt.time(7, 0))
                st.session_state[f"{base}_intensity_{idx}"] = row.get("intensity") or "Low"
                st.session_state[f"{base}_instruction_{idx}"] = row.get("instruction") or ""
            else:
                st.session_state[f"{base}_supplement_{idx}"] = row.get("reference_label") or "-- Select supplement --"
                st.session_state[f"{base}_time_{idx}"] = parse_time(row.get("scheduled_time"), dt.time(8, 0))
                st.session_state[f"{base}_dose_{idx}"] = row.get("dosage_frequency") or ""
                st.session_state[f"{base}_instruction_{idx}"] = row.get("instruction") or ""


def initialise_defaults():
    st.session_state.setdefault("v4_profile_id", "")
    st.session_state.setdefault("v4_profile_name", "North India - Adult - Weight Management - Vegetarian")
    st.session_state.setdefault("v4_clone_from", "New profile")
    st.session_state.setdefault("v4_change_note", "Cloned and adjusted for member preference / region / concern")
    st.session_state.setdefault("v4_profile_status", "Draft")
    st.session_state.setdefault("v4_region", "North India")
    st.session_state.setdefault("v4_age_band", "31-45")
    st.session_state.setdefault("v4_concerns", ["Weight Management"])
    st.session_state.setdefault("v4_diet_type", "Vegetarian")
    st.session_state.setdefault("v4_member", "Select member")
    st.session_state.setdefault("v4_note", "")
    st.session_state.setdefault("v4_start_date", dt.date.today())
    st.session_state.setdefault("v4_active_section", "Profile Setup")


initialise_defaults()

st.markdown("<div class='hm-section-nav'>", unsafe_allow_html=True)
nav_cols = st.columns([1, 1, 1, 1, .9], gap="small")
for col, section_name in zip(nav_cols, SECTIONS):
    with col:
        if st.button(NAV_LABELS[section_name], key=f"v4_nav_{section_name}", type=("primary" if st.session_state["v4_active_section"] == section_name else "secondary"), use_container_width=True):
            st.session_state["v4_active_section"] = section_name
st.markdown("</div>", unsafe_allow_html=True)
st.markdown("<div class='hm-section-rule'></div>", unsafe_allow_html=True)

if STORE_STATUS.get("ok"):
    readiness_class = "hm-ready-ok"
    readiness_text = "<b>Sprint 1 draft store is ready.</b> Draft save/load is enabled. This message appears directly below the section buttons."
else:
    readiness_class = "hm-ready-warn"
    readiness_text = f"<b>Sprint 1 draft store is not ready.</b> {STORE_STATUS.get('message', 'Run the Sprint 1 SQL script, then refresh this page.')}"
st.markdown(f"<div class='hm-readiness-strip {readiness_class}'>{readiness_text}</div>", unsafe_allow_html=True)

section = st.session_state["v4_active_section"]

ok_sources, source_profiles, _source_msg = list_profile_sources()
clone_options = ["New profile"]
clone_label_to_id = {"New profile": ""}
if ok_sources and source_profiles:
    for profile_row in source_profiles:
        label = f"{profile_row.get('profile_name', 'Untitled')} [{profile_row.get('status', 'draft')}]"
        clone_options.append(label)
        clone_label_to_id[label] = profile_row.get("id", "")
else:
    clone_options.extend(["Profile A - Gut Reset", "Profile B - Weight Management", "Profile C - Senior Wellness"])
    clone_label_to_id.update({label: "" for label in clone_options})

if section == "Profile Setup":
    st.markdown("<div class='hm-title'>Recommendation Profile Setup</div><div class='hm-sub'>Reusable profile with cloning, categorisation, member assignment and cycle context.</div>", unsafe_allow_html=True)

    st.markdown("<div class='hm-store-box'>", unsafe_allow_html=True)
    st.caption(f"Dropdown source: {SOURCE_MESSAGE} Member source: {MEMBER_MESSAGE}")

    ok_drafts, draft_profiles, draft_message = list_draft_profiles()
    draft_label_to_id = {"-- Select saved draft --": ""}
    if ok_drafts:
        for draft in draft_profiles:
            label = f"{draft.get('profile_name', 'Untitled draft')} · {str(draft.get('updated_at', ''))[:16]}"
            draft_label_to_id[label] = draft.get("id", "")
    load_cols = st.columns([.58, .21, .21])
    selected_draft_label = load_cols[0].selectbox("Load saved draft", list(draft_label_to_id.keys()), key="v4_load_draft_choice")
    if load_cols[1].button("Load Draft", use_container_width=True, disabled=not bool(draft_label_to_id.get(selected_draft_label))):
        ok, profile_payload, item_payload, message = load_profile(draft_label_to_id.get(selected_draft_label, ""))
        if ok:
            apply_profile_to_session(profile_payload, item_payload)
            st.success(message)
            st.rerun()
        else:
            st.error(message)
    if load_cols[2].button("New Draft", use_container_width=True):
        for key in list(st.session_state.keys()):
            if str(key).startswith("v4_") or str(key).startswith(("meal_", "exercise_", "supplement_")):
                st.session_state.pop(key, None)
        initialise_defaults()
        st.rerun()
    if not ok_drafts and STORE_STATUS.get("ok"):
        st.caption(draft_message)
    if st.session_state.get("v4_profile_id"):
        st.caption(f"Current draft id: {st.session_state.get('v4_profile_id')}")
    st.markdown("</div>", unsafe_allow_html=True)

    st.session_state["v4_clone_from"] = st.session_state.get("v4_clone_from") if st.session_state.get("v4_clone_from") in clone_options else "New profile"
    st.session_state["v4_age_band"] = st.session_state.get("v4_age_band") if st.session_state.get("v4_age_band") in AGE_BANDS else "31-45"
    st.session_state["v4_diet_type"] = st.session_state.get("v4_diet_type") if st.session_state.get("v4_diet_type") in DIET_TYPES else "Vegetarian"
    st.session_state["v4_member"] = st.session_state.get("v4_member") if st.session_state.get("v4_member") in MEMBER_LABEL_TO_ID else "Select member"

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
        st.selectbox("Example Member Assignment", list(MEMBER_LABEL_TO_ID.keys()), key="v4_member")
        st.text_area("Profile-level Nutritionist Note", height=150, key="v4_note")
    with a2:
        st.date_input("Plan Start Date", key="v4_start_date")
        st.text_input("Cycle Rule", value="Weekly cyclical until replaced or stopped", disabled=True, key="v4_cycle")
        st.text_input("Implementation Status", value="Sprint 1: draft save/load only. Publish not enabled.", disabled=True, key="v4_status")

    if st.button("Save Draft Profile", type="primary", use_container_width=True, disabled=not STORE_STATUS.get("ok")):
        ok, profile_id, message = save_draft_profile(current_profile_payload(clone_label_to_id), collect_items())
        if ok:
            st.session_state["v4_profile_id"] = profile_id
            st.success(message)
        else:
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
    profile_note = st.session_state.get("v4_note", "")
    plan_start = st.session_state.get("v4_start_date", dt.date.today())
    concerns = st.session_state.get("v4_concerns", [])

    st.markdown("<div class='hm-title'>Preview & End-to-End Flow Review</div><div class='hm-sub'>This is the contract review page before implementation. It checks what Admin creates, what gets published, and what Web Member and Flutter Member consume.</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='hm-preview'><b>Profile Summary</b><br><b>Draft ID:</b> {st.session_state.get('v4_profile_id') or 'Not saved yet'}<br><b>Profile:</b> {st.session_state.get('v4_profile_name', '')}<br><b>Clone Source:</b> {st.session_state.get('v4_clone_from', 'New profile')}<br><b>Status:</b> {st.session_state.get('v4_profile_status', 'Draft')}<br><b>Assigned Member:</b> {assigned_member}<br><b>Start Date:</b> {plan_start.isoformat() if isinstance(plan_start, dt.date) else plan_start}<br><b>Cycle:</b> Weekly cyclical until replaced or stopped<br><b>Tags:</b> {st.session_state.get('v4_region', '')} - {st.session_state.get('v4_age_band', '')} - {st.session_state.get('v4_diet_type', '')} - {', '.join(concerns) if concerns else 'No health concern selected'}<br><b>Change Note:</b> {st.session_state.get('v4_change_note', '') or 'NA'}<br><b>Profile Note:</b> {profile_note or 'NA'}</div>", unsafe_allow_html=True)
    st.markdown("""
<div class='hm-grid'>
  <div class='hm-mini'><b>1. Admin Creates</b><br>Profile setup, weekly meal structure, weekly exercise regime and weekly supplement regime.</div>
  <div class='hm-mini'><b>2. Admin Saves Draft</b><br>Sprint 1 stores draft data only. It does not publish or activate a member profile.</div>
  <div class='hm-mini'><b>3. Later Publish Sprint</b><br>Publish will convert a complete draft into one active member recommendation profile.</div>
  <div class='hm-mini'><b>4. Later Member Read Sprint</b><br>My Recommendations and Today's Journey will consume the same published profile structure.</div>
</div>
""", unsafe_allow_html=True)
    st.markdown(f"""
<div class='hm-preview'>
<b>Publish Readiness Checklist</b><br>
This checklist remains admin-side as the final gate before publish. In Sprint 1, it is informational only.
<div class='hm-readiness'>
  <div class='hm-readiness-item'><span class='hm-pill hm-ok'>Complete</span><br><b>Profile name added</b><br>Reusable profile identity is available.</div>
  <div class='hm-readiness-item'><span class='hm-pill hm-info'>Ready</span><br><b>Clone / source context captured</b><br>Admin can trace whether this is new or cloned.</div>
  <div class='hm-readiness-item'><span class='hm-pill {member_pill}'>{member_status}</span><br><b>Member assigned</b><br>Publishing must stay blocked until a member is selected.</div>
  <div class='hm-readiness-item'><span class='hm-pill hm-ok'>Complete</span><br><b>Start date selected</b><br>Start date drives the day-slice calculation.</div>
  <div class='hm-readiness-item'><span class='hm-pill hm-ok'>Complete</span><br><b>Weekly cycle rule present</b><br>Cycle continues until replaced or stopped.</div>
  <div class='hm-readiness-item'><span class='hm-pill hm-info'>Sprint 1</span><br><b>Draft save/load enabled</b><br>Publish and member consumption are deliberately not enabled yet.</div>
</div>
</div>
""", unsafe_allow_html=True)
    st.markdown("""
<div class='hm-preview'>
<b>How this profile will appear to the member</b><br>
<div class='hm-member-flow'>
  <div class='hm-member-card'>
    <b>My Recommendations</b>
    <span>Shows the member's full active weekly recommendation profile. This will be wired only after publish is implemented.</span>
  </div>
  <div class='hm-member-card'>
    <b>Today's Journey</b>
    <span>Shows only the current day's slice from the active weekly cycle. This will be wired in the member-consumption sprint.</span>
  </div>
  <div class='hm-member-card'>
    <b>Cycle Rule</b>
    <span>The same weekly cycle repeats until an admin replaces or stops the profile. Sprint 1 stores the draft rule only.</span>
  </div>
</div>
</div>
""", unsafe_allow_html=True)
    st.markdown("""
<div class='hm-preview'>
<b>Sprint 1 No-data-loss checkpoints</b><br>
[ ] Draft profile header saves and reloads.<br>
[ ] Meal rows visited/entered by admin save as repeatable rows.<br>
[ ] Exercise rows visited/entered by admin save as repeatable rows.<br>
[ ] Supplement rows visited/entered by admin save as repeatable rows.<br>
[ ] Save/load does not publish anything to member-facing flows.<br>
[ ] Dropdowns use Supabase-backed master data when Sprint 1 SQL is available, with safe fallback before SQL is run.
</div>
""", unsafe_allow_html=True)

render_page_nav("Recommendation Profile Builder", back_page="pages/10_Admin_Dashboard.py", dashboard_page="pages/10_Admin_Dashboard.py", show_evaluation=False, show_dashboard=True, location="bottom")
render_back_to_top()
