from __future__ import annotations

import streamlit as st

from components.meal_profile_builder_phase_b import (
    ALLOCATION_WORKSPACE_SECTION,
    MEAL_PROFILE_BUILDER_SECTIONS,
    VIEW_PROFILES_SECTION,
)
from components.member_plan_builder_allocations import render_member_plan_allocations
from components.member_plan_builder_export import render_view_member_plan
from components.member_plan_builder_meals import render_member_plan_meals
from components.member_plan_builder_setup import render_member_plan_setup
from components.pbm_core import ensure_state, safe_key
from components.profile_builder_access import (
    current_profile_builder_role,
    current_profile_builder_user_can_publish,
)
from components.profile_builder_form_hygiene import (
    install_profile_builder_form_hygiene,
)
from components.recommendation_profile_store import load_profile_builder_sources


APP_BUILD_VERSION = "v101.00"
APP_BUILD_LABEL = "Simplified Member Plan Builder"
SECTION_LABELS = {
    "Profile Setup": "Setup",
    "Meal Structure": "Meals",
    ALLOCATION_WORKSPACE_SECTION: "Exercise & Supplement",
    VIEW_PROFILES_SECTION: "View Member Plan",
}


install_profile_builder_form_hygiene()


def _render_css() -> None:
    st.markdown(
        """
<style id="hm-member-plan-builder-rebuild-v1">
.hm-title{color:#064E3B;font-size:1.05rem;font-weight:950;margin:.18rem 0 .22rem}
.hm-sub{color:#64748B;font-size:.82rem;font-weight:700;margin:0 0 .72rem}
.mpb-nav [data-testid="stButton"]>button{width:100%!important;min-height:2.62rem!important;border-radius:14px!important;font-weight:900!important;border:1px solid #D8A84E!important;background:#fff!important;color:#064E3B!important}
.mpb-nav [data-testid="stButton"]>button[kind="primary"]{background:linear-gradient(135deg,#064E3B,#0F766E)!important;color:#fff!important;border-color:#064E3B!important}
.mpb-rule{height:1px;background:linear-gradient(90deg,transparent,#D8A84E,transparent);margin:.38rem 0 .86rem}
.mpb-meal-card{border:1px solid #E3C98E;background:#FFFDF8;border-radius:15px;padding:.66rem .74rem;margin:.45rem 0;box-shadow:0 5px 14px rgba(15,23,42,.035)}
.mpb-meal-card-title{color:#064E3B;font-size:.88rem;font-weight:950;margin:0 0 .44rem}
.mpb-selected-recipe{min-height:2.44rem;display:flex;align-items:center;border:1px solid #E2E8F0;border-radius:10px;padding:.35rem .55rem;background:#fff;color:#475569;font-size:.80rem;font-weight:720}
.mpb-allocation-card{border:1px solid #E3C98E;background:#FFFDF8;border-radius:15px;padding:.70rem .82rem;margin:.28rem 0 .72rem}
.mpb-allocation-card b{display:block;color:#064E3B;font-size:.92rem;margin-bottom:.18rem}
.mpb-allocation-card span{display:block;color:#64748B;font-size:.80rem;font-weight:680}
div[data-testid="stExpander"]{border-color:#E3C98E!important;border-radius:12px!important}
@media(max-width:900px){.mpb-nav [data-testid="stButton"]>button{font-size:.76rem!important}.mpb-meal-card{padding:.56rem}}
</style>
""",
        unsafe_allow_html=True,
    )


def render_modular_profile_builder() -> None:
    ensure_state()
    _render_css()

    role = current_profile_builder_role()
    can_publish = current_profile_builder_user_can_publish()
    visible_sections = list(MEAL_PROFILE_BUILDER_SECTIONS)
    if role not in {"admin", "super_admin"}:
        visible_sections.remove(ALLOCATION_WORKSPACE_SECTION)
    if st.session_state.get("pbm_section") not in visible_sections:
        st.session_state["pbm_section"] = "Profile Setup"

    sources, _message = load_profile_builder_sources()
    options = {
        "recipe": list(sources.get("recipe") or []),
        "age_band": list(sources.get("age_band") or []),
        "health_concern": list(sources.get("health_concern") or []),
        "diet_type": list(sources.get("diet_type") or []),
    }

    st.markdown(
        "<div class='hero-shell'>"
        "<div class='hero-kicker'>Member Planning</div>"
        "<div class='hero-title'>Member Plan Builder</div>"
        "<div class='hero-subtitle'>Set up the member, build the seven-day meal plan, publish it and manage Exercise or Supplement allocations from one simple workflow.</div>"
        f"<div><span class='meta-pill'>{APP_BUILD_VERSION} · {APP_BUILD_LABEL}</span></div>"
        "</div>",
        unsafe_allow_html=True,
    )

    st.markdown("<div class='mpb-nav'>", unsafe_allow_html=True)
    columns = st.columns(len(visible_sections), gap="small")
    for column, section in zip(columns, visible_sections):
        if column.button(
            SECTION_LABELS[section],
            key=f"mpb_nav_{safe_key(section)}",
            type=(
                "primary"
                if st.session_state.get("pbm_section") == section
                else "secondary"
            ),
            use_container_width=True,
        ):
            st.session_state["pbm_section"] = section
            st.rerun()
    st.markdown("</div><div class='mpb-rule'></div>", unsafe_allow_html=True)

    section = st.session_state.get("pbm_section")
    if section == "Profile Setup":
        render_member_plan_setup(options)
    elif section == "Meal Structure":
        render_member_plan_meals(options["recipe"], can_publish)
    elif section == ALLOCATION_WORKSPACE_SECTION:
        render_member_plan_allocations()
    else:
        render_view_member_plan()
