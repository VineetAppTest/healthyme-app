import datetime as dt

import pandas as pd
import streamlit as st

from components.guards import require_admin
from components.db import list_active_member_supplements, list_members
from components.recommendation_contract import (
    get_latest_unified_recommendation_share,
    list_repository_items,
    save_unified_recommendation_share,
    sync_all_repositories_to_state,
)
from components.ui_common import (
    inject_global_styles,
    apply_luxe_theme,
    utility_logout_bar,
    topbar,
    render_page_nav,
    render_back_to_top,
)


st.set_page_config(
    page_title="Unified Recommendations",
    page_icon="💚",
    layout="wide",
    initial_sidebar_state="collapsed",
)
inject_global_styles()
apply_luxe_theme()
require_admin()
utility_logout_bar()

topbar(
    "Unified Recommendations",
    "Create the member-facing snapshot in one flow: meal plan, exercise plan, supplement plan and nutritionist note.",
    "Admin recommendations",
)

st.markdown(
    """
<style>
.hm-h9a5e-note{border:1px solid #E3C98E;background:#FFFDF8;border-radius:14px;padding:.72rem .85rem;color:#475569;font-size:.84rem;font-weight:720;line-height:1.38;margin:.25rem 0 .85rem;}
.hm-h9a5e-panel{border:1px solid #E3C98E;background:#FFFDF8;border-radius:16px;padding:.82rem .9rem;margin:.55rem 0 .9rem;box-shadow:0 7px 16px rgba(15,23,42,.035);}
.hm-h9a5e-panel-title{color:#064E3B;font-size:.96rem;font-weight:950;margin:0 0 .22rem;}
.hm-h9a5e-panel-sub{color:#64748B;font-size:.80rem;font-weight:720;line-height:1.35;margin:0 0 .55rem;}
.hm-h9a5e-status-ok{border:1px solid #BEE8D6;background:#ECFDF5;color:#064E3B;border-radius:14px;padding:.62rem .75rem;font-size:.84rem;font-weight:850;line-height:1.36;margin:.45rem 0;}
.hm-h9a5e-status-warn{border:1px solid #F6D18B;background:#FFFBEB;color:#7C4A03;border-radius:14px;padding:.62rem .75rem;font-size:.84rem;font-weight:850;line-height:1.36;margin:.45rem 0;}
.hm-h9a5e-compact-line{color:#475569;font-size:.82rem;font-weight:760;line-height:1.35;margin:.2rem 0 .45rem;}
.hm-h9a5e-mini-grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:.55rem;margin:.5rem 0 .75rem;}
.hm-h9a5e-mini{border:1px solid #E3C98E;background:#FFFFFF;border-radius:13px;padding:.55rem .62rem;}
.hm-h9a5e-mini-label{font-size:.68rem;text-transform:uppercase;letter-spacing:.04em;color:#64748B;font-weight:900;}
.hm-h9a5e-mini-value{font-size:1.05rem;color:#064E3B;font-weight:950;line-height:1.05;margin-top:.12rem;}
@media(max-width:850px){.hm-h9a5e-mini-grid{grid-template-columns:repeat(2,minmax(0,1fr));}}
</style>
""",
    unsafe_allow_html=True,
)


MEAL_SLOTS = ["Breakfast", "Lunch", "Snacks", "Dinner", "Bedtime"]
EXERCISE_SLOTS = ["Morning", "Evening"]


def _actor_id():
    return st.session_state.get("user_id") or st.session_state.get("oidc_email") or "admin"


def _clean(value):
    text = str(value or "").strip()
    if text.lower() in {"nan", "none", "null", "na", "n/a", "select"}:
        return ""
    return text


def _label_member(row):
    return f"{row.get('name') or 'Member'} — {row.get('email') or row.get('id')}"


def _resource_label(row, kind):
    title = _clean(row.get("title")) or "Untitled"
    if kind == "recipes":
        meta = _clean(row.get("meal_type")) or _clean(row.get("prep_time"))
    else:
        meta = _clean(row.get("duration_or_reps")) or _clean(row.get("category"))
    return f"{row.get('id')} — {title}{' · ' + meta if meta else ''}"


def _select_label_for_id(options, item_id):
    for label, value in options.items():
        if str(value) == str(item_id):
            return label
    return list(options.keys())[0] if options else ""


def _existing_meal(share, slot):
    for item in (share or {}).get("meal_plan", []) or []:
        if _clean(item.get("meal_slot")).lower() == slot.lower():
            return item
    return {}


def _existing_exercise(share, timing):
    for item in (share or {}).get("exercise_plan", []) or []:
        if _clean(item.get("timing")).lower() == timing.lower():
            return item
    return {}


def _latest_contract_status(member_id):
    latest = get_latest_unified_recommendation_share(member_id, include_draft=False)
    if not latest:
        return {
            "latest": {},
            "ok": False,
            "recipe_count": 0,
            "exercise_count": 0,
            "supplement_count": 0,
            "issues": ["No published recommendation snapshot found for this member."],
        }
    meal_plan = latest.get("meal_plan", []) or []
    exercise_plan = latest.get("exercise_plan", []) or []
    supplement_plan = latest.get("supplement_plan", []) or []
    recipe_count = sum(1 for row in meal_plan if _clean(row.get("recipe_id")) or _clean(row.get("recipe_name")) or _clean(row.get("name")))
    exercise_count = sum(1 for row in exercise_plan if _clean(row.get("exercise_id")) or _clean(row.get("exercise_name")) or _clean(row.get("name")) or _clean(row.get("title")))
    supplement_count = 0
    for row in supplement_plan:
        if isinstance(row, dict):
            details = row.get("supplement_details", []) or []
            ids = row.get("supplement_ids", []) or []
            if details:
                supplement_count += len(details)
            elif ids:
                supplement_count += len(ids)
    issues = []
    if recipe_count <= 0:
        issues.append("Latest published snapshot has no real recipe item.")
    if exercise_count <= 0:
        issues.append("Latest published snapshot has no real exercise item.")
    return {
        "latest": latest,
        "ok": len(issues) == 0,
        "recipe_count": recipe_count,
        "exercise_count": exercise_count,
        "supplement_count": supplement_count,
        "issues": issues,
    }


st.markdown(
    """
<div class='hm-h9a5e-note'>
<b>Purpose:</b> build one clean member-facing recommendation snapshot. The admin does not first allocate a loose list and then publish it. Recipes are selected directly against meal slots; exercises are selected directly against timing slots; active supplements and the nutritionist note are included in the same snapshot.
</div>
""",
    unsafe_allow_html=True,
)

repo_recipes = list_repository_items("recipes", active_only=False)
repo_exercises = list_repository_items("exercises", active_only=False)
active_recipes = [r for r in repo_recipes if str(r.get("status", "active")).lower() == "active"]
active_exercises = [r for r in repo_exercises if str(r.get("status", "active")).lower() == "active"]

st.markdown("<div class='hm-h9a5e-panel'>", unsafe_allow_html=True)
st.markdown("<div class='hm-h9a5e-panel-title'>Repository readiness</div>", unsafe_allow_html=True)
st.markdown(
    f"<div class='hm-h9a5e-compact-line'>Recipe repository: <b>{len(repo_recipes)}</b> total / <b>{len(active_recipes)}</b> active. Exercise repository: <b>{len(repo_exercises)}</b> total / <b>{len(active_exercises)}</b> active.</div>",
    unsafe_allow_html=True,
)
if st.button("Sync recipe and exercise repositories to app-state", type="primary", use_container_width=True):
    counts = sync_all_repositories_to_state()
    st.success(f"Repository mirror updated. Recipes: {counts['recipes']}; Exercises: {counts['exercises']}.")
    st.rerun()
st.markdown("</div>", unsafe_allow_html=True)

members = list_members()
if not members:
    st.warning("No active members available.")
    render_page_nav("Unified Recommendations", back_page="pages/10_Admin_Dashboard.py", dashboard_page="pages/10_Admin_Dashboard.py", show_evaluation=False, show_dashboard=True, location="bottom")
    render_back_to_top()
    st.stop()

member_options = {_label_member(m): m for m in members}
selected_member_label = st.selectbox("Select member", list(member_options.keys()), key="h9a5e_member")
member = member_options[selected_member_label]
member_id = member["id"]

latest = get_latest_unified_recommendation_share(member_id, include_draft=True)
start_default = dt.date.today()
try:
    if latest.get("start_date"):
        start_default = dt.date.fromisoformat(str(latest.get("start_date"))[:10])
except Exception:
    start_default = dt.date.today()

recipe_options = {"— No recipe —": ""}
recipe_options.update({_resource_label(r, "recipes"): str(r.get("id")) for r in active_recipes})
exercise_options = {"— No exercise —": ""}
exercise_options.update({_resource_label(r, "exercises"): str(r.get("id")) for r in active_exercises})

st.markdown("### Member-facing recommendation snapshot")
st.caption("This is the contract that should feed Flutter My Recommendations and the web member journey.")

window_col, note_col = st.columns([0.36, 0.64], gap="large")
with window_col:
    start_date = st.date_input("Start Date", value=start_default, key=f"h9a5e_start_{member_id}")
    end_date = start_date + dt.timedelta(days=6)
    st.text_input("End Date", value=end_date.isoformat(), disabled=True)
with note_col:
    nutritionist_report = st.text_area(
        "Nutritionist Report / Member Note",
        value=str(latest.get("nutritionist_report", "") or ""),
        height=116,
        key=f"h9a5e_note_{member_id}",
    )

meal_plan = []
exercise_plan = []
active_supps = list_active_member_supplements(member_id)
supplement_plan = []

tab_meal, tab_exercise, tab_supplement = st.tabs(["Meal Plan", "Exercise Plan", "Supplement Plan"])

with tab_meal:
    st.markdown("<div class='hm-h9a5e-panel-title'>Meal Plan</div>", unsafe_allow_html=True)
    st.markdown("<div class='hm-h9a5e-panel-sub'>Choose the recipe directly for each meal slot. Empty slots are not published as blank placeholders.</div>", unsafe_allow_html=True)
    for slot in MEAL_SLOTS:
        existing_item = _existing_meal(latest, slot)
        default_label = _select_label_for_id(recipe_options, existing_item.get("recipe_id", ""))
        row_col, note_col = st.columns([0.58, 0.42], gap="small")
        with row_col:
            chosen_label = st.selectbox(
                f"{slot} recipe",
                list(recipe_options.keys()),
                index=list(recipe_options.keys()).index(default_label),
                key=f"h9a5e_meal_{member_id}_{slot}",
            )
        with note_col:
            meal_note = st.text_input(
                f"{slot} note",
                value=_clean(existing_item.get("notes")),
                key=f"h9a5e_meal_note_{member_id}_{slot}",
            )
        recipe_id = recipe_options.get(chosen_label, "")
        if recipe_id:
            meal_plan.append({
                "day_number": 1,
                "date": start_date.isoformat(),
                "meal_slot": slot,
                "recipe_id": recipe_id,
                "notes": meal_note,
            })

with tab_exercise:
    st.markdown("<div class='hm-h9a5e-panel-title'>Exercise Plan</div>", unsafe_allow_html=True)
    st.markdown("<div class='hm-h9a5e-panel-sub'>Choose exercises directly by timing. Morning and evening are the default member-facing slots.</div>", unsafe_allow_html=True)
    for timing in EXERCISE_SLOTS:
        existing_item = _existing_exercise(latest, timing)
        default_label = _select_label_for_id(exercise_options, existing_item.get("exercise_id", ""))
        ex_col, instr_col = st.columns([0.55, 0.45], gap="small")
        with ex_col:
            chosen_label = st.selectbox(
                f"{timing} exercise",
                list(exercise_options.keys()),
                index=list(exercise_options.keys()).index(default_label),
                key=f"h9a5e_exercise_{member_id}_{timing}",
            )
        with instr_col:
            ex_note = st.text_input(
                f"{timing} instruction",
                value=_clean(existing_item.get("notes")),
                key=f"h9a5e_exercise_note_{member_id}_{timing}",
            )
        exercise_id = exercise_options.get(chosen_label, "")
        if exercise_id:
            exercise_plan.append({
                "day_number": 1,
                "date": start_date.isoformat(),
                "exercise_id": exercise_id,
                "timing": timing,
                "notes": ex_note,
            })

with tab_supplement:
    st.markdown("<div class='hm-h9a5e-panel-title'>Supplement Plan</div>", unsafe_allow_html=True)
    st.markdown("<div class='hm-h9a5e-panel-sub'>Active member supplements are included in the snapshot. Edit the regimen from the Supplement Manager if the source needs correction.</div>", unsafe_allow_html=True)
    if not active_supps:
        st.info("No active supplements are assigned to this member.")
    else:
        supp_rows = []
        for row in active_supps:
            supp_rows.append({
                "supplement_id": str(row.get("id") or row.get("supplement_id") or ""),
                "supplement_name": _clean(row.get("supplement_name")) or "Supplement",
                "dosage": _clean(row.get("dosage")),
                "frequency": _clean(row.get("frequency")),
                "timing": _clean(row.get("timing")),
                "start_date": _clean(row.get("start_date")),
                "end_date": _clean(row.get("end_date")),
                "instructions": _clean(row.get("instructions")) or _clean(row.get("member_instructions")),
            })
        st.dataframe(pd.DataFrame(supp_rows), use_container_width=True, hide_index=True)
        supplement_plan.append({
            "day_number": 1,
            "date": start_date.isoformat(),
            "supplement_ids": [r.get("supplement_id") for r in supp_rows if r.get("supplement_id")],
            "supplement_details": supp_rows,
            "notes": "Pulled from active supplement regimen.",
        })

selected_recipe_count = len(meal_plan)
selected_exercise_count = len(exercise_plan)

if selected_recipe_count == 0 or selected_exercise_count == 0:
    st.markdown(
        "<div class='hm-h9a5e-status-warn'>Select at least one meal recipe and one exercise before publishing. Blank placeholders will not be saved.</div>",
        unsafe_allow_html=True,
    )
else:
    st.markdown(
        f"<div class='hm-h9a5e-status-ok'>Ready to publish: {selected_recipe_count} meal item(s), {selected_exercise_count} exercise item(s), {len(active_supps)} active supplement item(s).</div>",
        unsafe_allow_html=True,
    )

if st.button(
    "Publish member-facing recommendation snapshot",
    type="primary",
    use_container_width=True,
    disabled=(selected_recipe_count == 0 or selected_exercise_count == 0),
):
    payload = {
        "id": latest.get("id", ""),
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "nutritionist_report": nutritionist_report,
        "meal_plan": meal_plan,
        "exercise_plan": exercise_plan,
        "supplement_plan": supplement_plan,
    }
    saved = save_unified_recommendation_share(member_id, payload, actor_id=_actor_id(), publish=True)
    real_recipes = sum(1 for row in saved.get("meal_plan", []) if row.get("recipe_id") or row.get("recipe_name"))
    real_exercises = sum(1 for row in saved.get("exercise_plan", []) if row.get("exercise_id") or row.get("exercise_name"))
    st.success(f"Published snapshot. Real meal items: {real_recipes}; real exercise items: {real_exercises}; active supplements included: {len(active_supps)}.")
    st.rerun()

st.markdown("### Contract status")
st.caption("This checks only the latest published snapshot for the selected member. Historical broken shares are not shown as current errors.")
status = _latest_contract_status(member_id)
st.markdown(
    f"""
<div class='hm-h9a5e-mini-grid'>
  <div class='hm-h9a5e-mini'><div class='hm-h9a5e-mini-label'>Latest Meal Items</div><div class='hm-h9a5e-mini-value'>{status['recipe_count']}</div></div>
  <div class='hm-h9a5e-mini'><div class='hm-h9a5e-mini-label'>Latest Exercise Items</div><div class='hm-h9a5e-mini-value'>{status['exercise_count']}</div></div>
  <div class='hm-h9a5e-mini'><div class='hm-h9a5e-mini-label'>Supplement Items</div><div class='hm-h9a5e-mini-value'>{status['supplement_count']}</div></div>
  <div class='hm-h9a5e-mini'><div class='hm-h9a5e-mini-label'>Status</div><div class='hm-h9a5e-mini-value'>{'OK' if status['ok'] else 'Review'}</div></div>
</div>
""",
    unsafe_allow_html=True,
)

if status["ok"]:
    st.markdown("<div class='hm-h9a5e-status-ok'>Latest published recommendation snapshot is clean for meal and exercise data.</div>", unsafe_allow_html=True)
else:
    st.markdown("<div class='hm-h9a5e-status-warn'>Current contract needs attention before Flutter retest.</div>", unsafe_allow_html=True)
    for issue in status["issues"]:
        st.write(f"- {issue}")

with st.expander("View latest published recommendation share", expanded=False):
    if status["latest"]:
        st.json(status["latest"])
    else:
        st.info("No published recommendation share found for this member yet.")

render_page_nav("Unified Recommendations", back_page="pages/10_Admin_Dashboard.py", dashboard_page="pages/10_Admin_Dashboard.py", show_evaluation=False, show_dashboard=True, location="bottom")
render_back_to_top()
