import copy
import uuid

import streamlit as st

import components.pbm_core as _pbm_core
import components.pbm_rows as _pbm_rows
from components.meal_profile_builder_phase_b import (
    ALLOCATION_WORKSPACE_SECTION,
    MEAL_PROFILE_BUILDER_SECTIONS,
    VIEW_PROFILES_SECTION,
    split_profile_items,
)
from components.pbm_core import ensure_state, safe, safe_key
from components.profile_builder_access import (
    current_profile_builder_role,
    current_profile_builder_user_can_publish,
)
from components.profile_builder_allocation_workspace import (
    render_profile_builder_allocation_workspace,
)

APP_BUILD_VERSION = "v100.45"
APP_BUILD_LABEL = "Member Planning · Streamlit Acceptance"
SECTION_LABELS = {
    "Profile Setup": "Setup",
    "Meal Structure": "Meals",
    ALLOCATION_WORKSPACE_SECTION: "Allocate Exercise & Supplement",
    VIEW_PROFILES_SECTION: "View Profiles",
}


def _epoch_widget_key(row, field):
    return f"pbm_row_{st.session_state.get('pbm_epoch', 0)}_{row['ui_id']}_{field}"


def _meaningful_row(row):
    kind = row.get("item_type")
    if kind == "meal":
        fields = ("reference_label", "portion", "instruction")
    elif kind == "exercise":
        fields = ("reference_label", "instruction", "intensity")
    else:
        fields = ("reference_label", "instruction", "dosage_frequency", "dosage")
    return any(str(row.get(field) or "").strip() for field in fields)


def _remove_row(ui_id):
    st.session_state["pbm_items"] = [
        row for row in st.session_state["pbm_items"] if row.get("ui_id") != ui_id
    ]


def _copy_day(kind, source_day, target_days):
    source_rows = [
        row
        for row in st.session_state["pbm_items"]
        if row.get("item_type") == kind
        and int(row.get("day_number") or 0) == source_day
        and _meaningful_row(row)
    ]
    st.session_state["pbm_items"] = [
        row
        for row in st.session_state["pbm_items"]
        if not (
            row.get("item_type") == kind
            and int(row.get("day_number") or 0) in target_days
        )
    ]
    for day in target_days:
        for source in source_rows:
            cloned = copy.deepcopy(source)
            cloned["ui_id"] = uuid.uuid4().hex
            cloned["day_number"] = day
            st.session_state["pbm_items"].append(cloned)


_pbm_core.row_has_content = _meaningful_row
_pbm_rows.row_has_content = _meaningful_row
_pbm_rows.widget_key = _epoch_widget_key
_pbm_rows.remove_row = _remove_row
_pbm_rows.copy_day = _copy_day

# Install success-only reset behaviour before binding the section renderers below.
from components.profile_builder_form_hygiene import install_profile_builder_form_hygiene

install_profile_builder_form_hygiene()

from components.pbm_modules import render_module, render_preview
from components.pbm_setup import render_setup
from components.profile_publish_control_v2 import render_profile_publish_control
from components.recommendation_profile_store import load_profile_builder_sources
from components.recommendation_profile_viewer import render_view_profiles


def _render_css() -> None:
    st.markdown(
        """
<style>
.hm-title{color:#064E3B;font-size:1.04rem;font-weight:950;margin:0 0 .25rem}.hm-sub{color:#64748B;font-size:.82rem;font-weight:720;margin:0 0 .7rem}
.hm-section-rule{height:1px;background:linear-gradient(90deg,transparent,rgba(216,168,78,.8),transparent);margin:.3rem 0 .72rem}
.hm-tab-nav [data-testid="stButton"]>button{width:100%!important;height:2.82rem!important;min-height:2.82rem!important;border-radius:15px!important;font-weight:930!important;border:1.15px solid rgba(216,180,98,.72)!important;background:#fff!important;color:#064E3B!important;white-space:normal!important;padding:.35rem!important}
.hm-tab-nav [data-testid="stButton"]>button[kind="primary"]{background:linear-gradient(135deg,#064E3B,#0F766E)!important;border-color:#064E3B!important;color:#fff!important}
.hm-load-label{min-height:1.22rem}.hm-slot{font-size:.80rem;color:#72551A;font-weight:900;margin:.8rem 0 .3rem}
.hm-preview{border:1px dashed #D8A84E;background:#FFF9EC;border-radius:16px;padding:.75rem .85rem;margin:.45rem 0;color:#475569;font-size:.83rem;line-height:1.5}
.hm-source-box{border:1px solid #D8A84E;background:#FFFDF7;border-radius:12px;padding:.48rem .65rem;margin:.35rem 0;color:#475569;font-size:.78rem}.hm-source-box b{color:#064E3B}.hm-source-box span{color:#64748B;font-weight:720}
.hm-count-grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:.65rem;margin:.55rem 0 1rem}.hm-count-card{background:#fff;border:1px solid #E3C98E;border-radius:15px;padding:.7rem .8rem}.hm-count-card b{display:block;color:#064E3B}.hm-count-card span{color:#64748B;font-size:.78rem;font-weight:780}
.hm-meal-actions{border-top:1px solid #E7D8BE;margin:1rem 0 .5rem;padding-top:.85rem}.hm-meal-actions-title{color:#064E3B;font-size:.92rem;font-weight:950;margin:0 0 .45rem}
.hm-allocation-member{border:1px solid #E3C98E;background:#FFF9EC;border-radius:14px;padding:.65rem .78rem;margin:.35rem 0 .75rem;color:#475569;font-size:.84rem}.hm-allocation-member b{color:#064E3B}
.hm-allocation-card{min-height:6rem;border:1px solid rgba(216,180,98,.64);background:#FFFDF8;border-radius:16px;padding:.78rem .86rem;margin:.15rem 0 .48rem}.hm-allocation-card b{display:block;color:#064E3B;font-size:.94rem;margin-bottom:.28rem}.hm-allocation-card span{display:block;color:#64748B;font-size:.80rem;line-height:1.4;font-weight:680}
@media(max-width:900px){.hm-count-grid{grid-template-columns:1fr 1fr}.hm-tab-nav [data-testid="stButton"]>button{font-size:.76rem!important}}
</style>
""",
        unsafe_allow_html=True,
    )


def _loaded_row_groups():
    return split_profile_items(st.session_state.get("pbm_items") or [])


def _render_workflow_boundary() -> None:
    groups = _loaded_row_groups()
    legacy_count = len(groups["legacy_exercise"]) + len(groups["legacy_supplement"])
    text = (
        f"{legacy_count} historical Exercise/Supplement row(s) remain preserved in the loaded profile. "
        if legacy_count
        else ""
    )
    st.caption(
        f"Meals are edited here; Exercise and Supplement use their independent allocation workflows. {text}"
        "Current Member Plan consolidates all three for the member."
    )


def _render_preview_with_legacy_boundary() -> None:
    groups = _loaded_row_groups()
    if groups["legacy_exercise"] or groups["legacy_supplement"]:
        st.caption(
            "Preview includes retained historical Exercise/Supplement rows for continuity; they are not editable here."
        )
    render_preview()


def _render_publish_with_legacy_boundary() -> None:
    groups = _loaded_row_groups()
    if groups["legacy_exercise"] or groups["legacy_supplement"]:
        st.caption(
            "Publishing preserves retained historical Exercise/Supplement rows without rewriting them."
        )
    render_profile_publish_control()


def _set_meal_action(action: str) -> None:
    current = str(st.session_state.get("pbm_meal_action_panel") or "")
    st.session_state["pbm_meal_action_panel"] = "" if current == action else action
    st.rerun()


def _render_meal_actions(can_publish: bool) -> None:
    st.markdown(
        "<div class='hm-meal-actions'><div class='hm-meal-actions-title'>Preview &amp; Publish</div></div>",
        unsafe_allow_html=True,
    )
    preview_col, publish_col = st.columns(2, gap="large")
    with preview_col:
        if st.button(
            "Preview Meal Plan",
            use_container_width=True,
            type=(
                "primary"
                if st.session_state.get("pbm_meal_action_panel") == "preview"
                else "secondary"
            ),
            key="pbm_meal_preview_action",
        ):
            _set_meal_action("preview")
    with publish_col:
        if st.button(
            "Publish Meal Plan",
            use_container_width=True,
            type=(
                "primary"
                if st.session_state.get("pbm_meal_action_panel") == "publish"
                else "secondary"
            ),
            disabled=not can_publish,
            key="pbm_meal_publish_action",
        ):
            _set_meal_action("publish")

    action = str(st.session_state.get("pbm_meal_action_panel") or "")
    if action == "preview":
        _render_preview_with_legacy_boundary()
    elif action == "publish" and can_publish:
        _render_publish_with_legacy_boundary()


def render_modular_profile_builder() -> None:
    ensure_state()
    _render_css()
    can_publish = current_profile_builder_user_can_publish()
    role = current_profile_builder_role()
    visible_sections = list(MEAL_PROFILE_BUILDER_SECTIONS)
    if role not in {"admin", "super_admin"}:
        visible_sections.remove(ALLOCATION_WORKSPACE_SECTION)
    if st.session_state.get("pbm_section") not in visible_sections:
        st.session_state["pbm_section"] = "Profile Setup"

    sources, _source_message = load_profile_builder_sources()
    options = {
        "recipe": list(sources.get("recipe") or []),
        # Exercise and Supplement sources remain unavailable to Meal rows. The
        # allocation workspace routes to their independent allocation stores.
        "exercise": [],
        "supplement": [],
        "age_band": list(sources.get("age_band") or []),
        "health_concern": list(sources.get("health_concern") or []),
        "diet_type": list(sources.get("diet_type") or []),
    }
    role_note = (
        "Nutritionist meal-planning access · Publish remains Admin/Super Admin only"
        if role == "nutritionist"
        else "Admin member planning"
    )
    st.markdown(
        f"<div class='hero-shell'><div class='hero-kicker'>{safe(role_note)}</div>"
        f"<div class='hero-title'>Meal Profile Builder</div>"
        f"<div class='hero-subtitle'>Build the seven-day meal plan, allocate Exercise and Supplement items, and review member profiles from one guided workflow.</div><div><span class='meta-pill'>"
        f"{APP_BUILD_VERSION} · {APP_BUILD_LABEL}</span></div></div>",
        unsafe_allow_html=True,
    )
    _render_workflow_boundary()
    st.markdown("<div class='hm-tab-nav'>", unsafe_allow_html=True)
    columns = st.columns(len(visible_sections), gap="small")
    for column, section in zip(columns, visible_sections):
        if column.button(
            SECTION_LABELS[section],
            key=f"pbm_nav_{safe_key(section)}",
            type=(
                "primary"
                if st.session_state["pbm_section"] == section
                else "secondary"
            ),
            use_container_width=True,
        ):
            st.session_state["pbm_section"] = section
            st.rerun()
    st.markdown("</div><div class='hm-section-rule'></div>", unsafe_allow_html=True)

    section = st.session_state["pbm_section"]
    if section == "Profile Setup":
        render_setup(options)
    elif section == "Meal Structure":
        render_module("meal", options)
        _render_meal_actions(can_publish)
    elif section == ALLOCATION_WORKSPACE_SECTION:
        render_profile_builder_allocation_workspace()
    else:
        render_view_profiles()
