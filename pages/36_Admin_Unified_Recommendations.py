import datetime as dt

import pandas as pd
import streamlit as st

from components.guards import require_admin
from components.db import list_members
from components.recommendation_contract import (
    get_latest_unified_recommendation_share,
    get_member_resource_allocations,
    list_repository_items,
    migrate_legacy_resource_assignments,
    recommendation_contract_diagnostics,
    save_member_resource_allocations,
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
    "H9A.5E contract workbench: repository → member allocation → published recommendation snapshot.",
    "Admin recommendations",
)

st.markdown(
    """
<style>
.hm-h9a5e-note{border:1px solid #E3C98E;background:#FFFDF8;border-radius:14px;padding:.7rem .85rem;color:#475569;font-size:.84rem;font-weight:720;line-height:1.38;margin:.25rem 0 .85rem;}
.hm-h9a5e-kpi{background:#fff;border:1px solid #E3C98E;border-radius:16px;padding:.75rem .85rem;box-shadow:0 7px 16px rgba(15,23,42,.04);}
.hm-h9a5e-kpi-label{font-size:.72rem;text-transform:uppercase;letter-spacing:.04em;color:#64748B;font-weight:900;}
.hm-h9a5e-kpi-value{font-size:1.45rem;color:#064E3B;font-weight:950;line-height:1.05;margin-top:.15rem;}
</style>
""",
    unsafe_allow_html=True,
)


def _actor_id():
    return st.session_state.get("user_id") or st.session_state.get("oidc_email") or "admin"


def _label_member(row):
    return f"{row.get('name') or 'Member'} — {row.get('email') or row.get('id')}"


def _resource_label(row, kind):
    title = str(row.get("title") or "Untitled").strip()
    if kind == "recipes":
        meta = str(row.get("meal_type") or row.get("prep_time") or "").strip()
    else:
        meta = str(row.get("duration_or_reps") or row.get("category") or "").strip()
    return f"{row.get('id')} — {title}{' · ' + meta if meta else ''}"


def _selected_labels(options, selected_ids):
    selected_ids = {str(x) for x in selected_ids or []}
    return [label for label, value in options.items() if str(value) in selected_ids]


def _kpi(label, value):
    st.markdown(
        f"<div class='hm-h9a5e-kpi'><div class='hm-h9a5e-kpi-label'>{label}</div><div class='hm-h9a5e-kpi-value'>{value}</div></div>",
        unsafe_allow_html=True,
    )


st.markdown(
    """
<div class='hm-h9a5e-note'>
<b>Purpose:</b> this page creates the missing single allocation gate. It mirrors CSV repositories into app-state, converts old direct allocations into canonical allocations, and publishes a member-facing recommendation snapshot that Flutter can read.
</div>
""",
    unsafe_allow_html=True,
)

repo_recipes = list_repository_items("recipes", active_only=False)
repo_exercises = list_repository_items("exercises", active_only=False)
active_recipes = [r for r in repo_recipes if str(r.get("status", "active")).lower() == "active"]
active_exercises = [r for r in repo_exercises if str(r.get("status", "active")).lower() == "active"]

k1, k2, k3, k4 = st.columns(4)
with k1:
    _kpi("Recipe Repository", len(repo_recipes))
with k2:
    _kpi("Exercise Repository", len(repo_exercises))
with k3:
    _kpi("Active Recipes", len(active_recipes))
with k4:
    _kpi("Active Exercises", len(active_exercises))

sync_col, migrate_col = st.columns(2, gap="large")
with sync_col:
    if st.button("Sync recipe/exercise repositories to app-state", type="primary", use_container_width=True):
        counts = sync_all_repositories_to_state()
        st.success(f"Repository mirror updated. Recipes: {counts['recipes']}; Exercises: {counts['exercises']}.")
        st.rerun()
with migrate_col:
    if st.button("Migrate old direct allocations to unified layer", use_container_width=True):
        counts = migrate_legacy_resource_assignments(actor_id=_actor_id())
        st.success(f"Legacy allocations migrated. Recipes: {counts['recipes']}; Exercises: {counts['exercises']}.")
        st.rerun()

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

st.markdown("### 1. Member allocation layer")
st.caption("Both direct allocation and Recommendation Share must eventually land here.")

recipe_options = {_resource_label(r, "recipes"): str(r.get("id")) for r in active_recipes}
exercise_options = {_resource_label(r, "exercises"): str(r.get("id")) for r in active_exercises}
current_recipe_allocs = get_member_resource_allocations(member_id, "recipes")
current_exercise_allocs = get_member_resource_allocations(member_id, "exercises")
current_recipe_ids = [str(r.get("recipe_id")) for r in current_recipe_allocs if str(r.get("recipe_id", "")).strip()]
current_exercise_ids = [str(r.get("exercise_id")) for r in current_exercise_allocs if str(r.get("exercise_id", "")).strip()]

alloc_col_1, alloc_col_2 = st.columns(2, gap="large")
with alloc_col_1:
    st.subheader("Recipes")
    if not recipe_options:
        st.info("No active recipes available. Add recipes first on the Recipe Repository page.")
        selected_recipe_labels = []
    else:
        selected_recipe_labels = st.multiselect(
            "Allocated recipes",
            list(recipe_options.keys()),
            default=_selected_labels(recipe_options, current_recipe_ids),
            key=f"h9a5e_recipes_{member_id}",
        )
    if st.button("Save recipe allocations", use_container_width=True, disabled=not bool(recipe_options)):
        selected_ids = [recipe_options[label] for label in selected_recipe_labels]
        rows = save_member_resource_allocations(member_id, "recipes", selected_ids, actor_id=_actor_id(), source="h9a5e_unified_workbench")
        st.success(f"Saved {len(rows)} recipe allocation(s) into member_recipe_allocations.")
        st.rerun()

with alloc_col_2:
    st.subheader("Exercises")
    if not exercise_options:
        st.info("No active exercises available. Add exercises first on the Exercise Repository page.")
        selected_exercise_labels = []
    else:
        selected_exercise_labels = st.multiselect(
            "Allocated exercises",
            list(exercise_options.keys()),
            default=_selected_labels(exercise_options, current_exercise_ids),
            key=f"h9a5e_exercises_{member_id}",
        )
    if st.button("Save exercise allocations", use_container_width=True, disabled=not bool(exercise_options)):
        selected_ids = [exercise_options[label] for label in selected_exercise_labels]
        rows = save_member_resource_allocations(member_id, "exercises", selected_ids, actor_id=_actor_id(), source="h9a5e_unified_workbench")
        st.success(f"Saved {len(rows)} exercise allocation(s) into member_exercise_allocations.")
        st.rerun()

st.markdown("### 2. Publish member-facing snapshot")
st.caption("This creates recommendation_shares[member_id] with real recipe/exercise names and IDs. Flutter My Recommendations reads this layer.")

latest = get_latest_unified_recommendation_share(member_id, include_draft=True)
start_default = dt.date.today()
try:
    if latest.get("start_date"):
        start_default = dt.date.fromisoformat(str(latest.get("start_date"))[:10])
except Exception:
    start_default = dt.date.today()

pub_col_1, pub_col_2 = st.columns([0.35, 0.65], gap="large")
with pub_col_1:
    start_date = st.date_input("Start Date", value=start_default, key=f"h9a5e_start_{member_id}")
    end_date = start_date + dt.timedelta(days=6)
    st.text_input("End Date", value=end_date.isoformat(), disabled=True)
with pub_col_2:
    nutritionist_report = st.text_area(
        "Nutritionist Report / Member Note",
        value=str(latest.get("nutritionist_report", "") or ""),
        height=125,
        key=f"h9a5e_note_{member_id}",
    )

publish_disabled = not current_recipe_allocs and not current_exercise_allocs
if publish_disabled:
    st.warning("Save at least one recipe or exercise allocation before publishing the snapshot.")

if st.button("Publish unified recommendation snapshot", type="primary", use_container_width=True, disabled=publish_disabled):
    payload = {
        "id": latest.get("id", ""),
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "nutritionist_report": nutritionist_report,
        # Leave these empty intentionally. The contract helper fills them from the canonical allocation layer.
        "meal_plan": [],
        "exercise_plan": [],
        "supplement_plan": latest.get("supplement_plan", []),
    }
    saved = save_unified_recommendation_share(member_id, payload, actor_id=_actor_id(), publish=True)
    real_recipes = sum(1 for row in saved.get("meal_plan", []) if row.get("recipe_id") or row.get("recipe_name"))
    real_exercises = sum(1 for row in saved.get("exercise_plan", []) if row.get("exercise_id") or row.get("exercise_name"))
    st.success(f"Published unified snapshot. Real recipe items: {real_recipes}; real exercise items: {real_exercises}.")
    st.rerun()

st.markdown("### 3. Contract diagnostics")
diag = recommendation_contract_diagnostics(member_id)
diag_cols = st.columns(4)
with diag_cols[0]:
    _kpi("Member Recipe Allocations", diag.get("member_recipe_allocations_count", 0))
with diag_cols[1]:
    _kpi("Member Exercise Allocations", diag.get("member_exercise_allocations_count", 0))
with diag_cols[2]:
    _kpi("Published Recipe Items", diag.get("published_recipe_items", 0))
with diag_cols[3]:
    _kpi("Published Exercise Items", diag.get("published_exercise_items", 0))

issues = diag.get("issues", [])
if issues:
    st.warning("Contract issues found:")
    for issue in issues[:8]:
        st.write(f"- {issue}")
else:
    st.success("Contract diagnostics are clean for this member.")

with st.expander("View current canonical allocations", expanded=False):
    left, right = st.columns(2, gap="large")
    with left:
        st.caption("member_recipe_allocations")
        st.dataframe(pd.DataFrame(get_member_resource_allocations(member_id, "recipes")), use_container_width=True, hide_index=True)
    with right:
        st.caption("member_exercise_allocations")
        st.dataframe(pd.DataFrame(get_member_resource_allocations(member_id, "exercises")), use_container_width=True, hide_index=True)

latest_published = get_latest_unified_recommendation_share(member_id, include_draft=False)
with st.expander("View latest published recommendation share", expanded=False):
    if latest_published:
        st.json(latest_published)
    else:
        st.info("No published unified recommendation share found for this member yet.")

render_page_nav("Unified Recommendations", back_page="pages/10_Admin_Dashboard.py", dashboard_page="pages/10_Admin_Dashboard.py", show_evaluation=False, show_dashboard=True, location="bottom")
render_back_to_top()
