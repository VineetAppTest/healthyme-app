from __future__ import annotations

import streamlit as st
from streamlit.errors import StreamlitAPIException

from components.member_plan_builder_expander_hygiene import (
    install_member_plan_builder_expander_hygiene,
)
from components.member_plan_builder_performance import (
    install_member_plan_builder_performance_cache,
    load_member_plan_recipe_options,
    load_member_plan_setup_options,
)


# Install performance and presentation guards before rebuilt renderers bind their
# source and widget functions.
install_member_plan_builder_performance_cache()
install_member_plan_builder_expander_hygiene()

from components.meal_profile_builder_phase_b import (
    EXERCISE_SECTION,
    MEAL_PROFILE_BUILDER_SECTIONS,
    SUPPLEMENT_SECTION,
    VIEW_PROFILES_SECTION,
)
from components.pbm_core import SELECT_PROFILE, ensure_state, reset_profile, safe_key
from components.profile_builder_access import (
    current_profile_builder_role,
    current_profile_builder_user_can_publish,
)
from components.profile_builder_form_hygiene import (
    install_profile_builder_form_hygiene,
)


# Install the established success-only reset layer before renderer modules bind
# any Profile Builder save or publish functions.
install_profile_builder_form_hygiene()

from components.member_plan_builder_exercise import render_member_plan_exercise
from components.member_plan_builder_meals_compact import (
    render_member_plan_meals_compact,
)
from components.member_plan_builder_setup import render_member_plan_setup
from components.member_plan_builder_supplement import render_member_plan_supplement
from components.member_plan_builder_view_compact import (
    render_view_member_plan_compact,
)


APP_BUILD_VERSION = "v101.11"
APP_BUILD_LABEL = "Repository-led Member Plan Builder"
SECTION_LABELS = {
    "Profile Setup": "Setup",
    "Meal Structure": "Meals",
    EXERCISE_SECTION: "Exercise",
    SUPPLEMENT_SECTION: "Supplement",
    VIEW_PROFILES_SECTION: "View Member Plan",
}

_MEAL_PROFILE_SELECTOR = "mpb_meal_repository_profile"
_MEAL_PROFILE_SELECTOR_RESET_PENDING = "_hm_mpb_meal_profile_selector_reset_pending"


def _apply_pending_meal_profile_selector_reset() -> None:
    """Reset the Meal Profile widget before Streamlit instantiates it."""

    if not st.session_state.pop(_MEAL_PROFILE_SELECTOR_RESET_PENDING, False):
        return
    st.session_state[_MEAL_PROFILE_SELECTOR] = SELECT_PROFILE


def _render_meals_with_selector_reset_guard(
    recipes: list[str],
    can_publish: bool,
) -> None:
    """Recover from the legacy post-publish widget-state reset ordering bug.

    The publish flow completes its persistence work before trying to reset the
    Meal Profile selectbox. Streamlit does not allow a keyed widget's state to
    be changed after that widget has been instantiated in the same run. Defer
    only that selector reset to the next rerun, while preserving the successful
    publish and clearing the builder state exactly once.
    """

    try:
        render_member_plan_meals_compact(recipes, can_publish)
    except StreamlitAPIException as exc:
        message = str(exc)
        is_selector_reset_error = (
            _MEAL_PROFILE_SELECTOR in message
            and "cannot be modified after the widget with key" in message
        )
        if not is_selector_reset_error:
            raise

        st.session_state[_MEAL_PROFILE_SELECTOR_RESET_PENDING] = True
        reset_profile()
        st.session_state["mpb_meal_saved"] = False
        st.session_state["mpb_publish_flash"] = (
            "Meal Profile published. The builder was reset safely for the next allocation."
        )
        st.rerun()


def _render_css() -> None:
    st.markdown(
        """
<style id="hm-member-plan-builder-compact-v2">
.hm-title{color:#064E3B;font-size:1.03rem;font-weight:950;margin:.12rem 0 .18rem}
.hm-sub{color:#64748B;font-size:.80rem;font-weight:680;margin:0 0 .62rem}
.mpb-nav [data-testid="stButton"]>button{width:100%!important;min-height:2.48rem!important;border-radius:13px!important;font-weight:900!important;border:1px solid #D8A84E!important;background:#fff!important;color:#064E3B!important;padding:.32rem .46rem!important}
.mpb-nav [data-testid="stButton"]>button[kind="primary"]{background:linear-gradient(135deg,#064E3B,#0F766E)!important;color:#fff!important;border-color:#064E3B!important}
.mpb-rule{height:1px;background:linear-gradient(90deg,transparent,#D8A84E,transparent);margin:.32rem 0 .68rem}
.mpb-meal-card-title{display:flex;justify-content:space-between;align-items:center;color:#064E3B;font-size:.88rem;font-weight:950;margin:0 0 .42rem}
.mpb-meal-card-title span{color:#8A6A24;font-size:.69rem;font-weight:760;border:1px solid #E3C98E;background:#FFF9EC;border-radius:999px;padding:.12rem .38rem}
.mpb-meal-guide{display:grid;grid-template-columns:38fr 22fr 30fr 10fr;gap:.45rem;color:#64748B;font-size:.70rem;font-weight:850;text-transform:uppercase;letter-spacing:.02em;padding:0 .25rem .28rem}
.mpb-meal-guide b:last-child{text-align:center}
.mpb-section-label{color:#064E3B;font-size:.94rem;font-weight:950;margin:.72rem 0 .34rem}
.mpb-source-summary{display:flex;align-items:center;gap:.55rem;flex-wrap:wrap;border:1px solid #E3C98E;background:#FFF9EC;border-radius:11px;padding:.42rem .56rem;margin:.12rem 0 .42rem}
.mpb-source-summary b{color:#064E3B;font-size:.83rem;font-weight:950}
.mpb-source-summary span{color:#64748B;font-size:.75rem;font-weight:720}
.mpb-integrity-note{border:1px solid #A7D7C8;background:#F0FDF8;color:#065F46;border-radius:11px;padding:.48rem .60rem;margin:.20rem 0 .54rem;font-size:.77rem;font-weight:760}
div[data-testid="stVerticalBlockBorderWrapper"]{border-color:#E3C98E!important;border-radius:14px!important;background:#FFFDF8!important;box-shadow:0 5px 14px rgba(15,23,42,.028)!important;margin:.34rem 0!important}
div[data-testid="stExpander"]{border:0!important;border-radius:10px!important;background:transparent!important}
div[data-testid="stExpander"] details{border:1.2px solid #D8A84E!important;border-radius:10px!important;background:#FFFDF8!important;overflow:hidden!important}
div[data-testid="stExpander"] details summary{list-style:none!important;min-height:2.42rem!important;padding:.42rem .58rem!important;display:flex!important;align-items:center!important;gap:.48rem!important;border-radius:9px!important;font-size:0!important}
div[data-testid="stExpander"] details summary::-webkit-details-marker{display:none!important}
div[data-testid="stExpander"] details summary::marker{content:""!important;display:none!important}
div[data-testid="stExpander"] details summary:before{content:"+"!important;display:inline-flex!important;align-items:center!important;justify-content:center!important;width:1.34rem!important;height:1.34rem!important;flex:0 0 1.34rem!important;border-radius:6px!important;background:#DDF7F3!important;color:#006D6F!important;font-size:.82rem!important;font-weight:950!important;line-height:1!important}
div[data-testid="stExpander"] details[open] summary:before{content:"−"!important}
div[data-testid="stExpander"] details summary p{display:block!important;width:100%!important;max-width:none!important;white-space:normal!important;overflow:visible!important;text-overflow:clip!important;color:#064E3B!important;font-size:.80rem!important;font-weight:900!important;line-height:1.2!important;margin:0!important;text-align:left!important}
div[data-testid="stExpander"] details summary svg,div[data-testid="stExpander"] details summary [data-testid="stExpanderToggleIcon"],div[data-testid="stExpander"] details summary [data-testid="stIconMaterial"],div[data-testid="stExpander"] details summary [class*="material-symbol"],div[data-testid="stExpander"] details summary span[aria-hidden="true"]{display:none!important;width:0!important;min-width:0!important;font-size:0!important}
@media(max-width:980px){.mpb-nav [data-testid="stButton"]>button{font-size:.72rem!important}.mpb-meal-guide{display:none}}
</style>
""",
        unsafe_allow_html=True,
    )


def render_modular_profile_builder() -> None:
    ensure_state()
    _apply_pending_meal_profile_selector_reset()
    _render_css()

    role = current_profile_builder_role()
    can_publish = current_profile_builder_user_can_publish()
    visible_sections = list(MEAL_PROFILE_BUILDER_SECTIONS)
    if role not in {"admin", "super_admin"}:
        for section in (EXERCISE_SECTION, SUPPLEMENT_SECTION):
            if section in visible_sections:
                visible_sections.remove(section)
    if st.session_state.get("pbm_section") not in visible_sections:
        st.session_state["pbm_section"] = "Profile Setup"

    st.markdown(
        "<div class='hero-shell'>"
        "<div class='hero-kicker'>Member Planning</div>"
        "<div class='hero-title'>Member Plan Builder</div>"
        "<div class='hero-subtitle'>Create reusable Meal Profiles, publish one to a member, then attach Exercise and Supplement allocations to that active plan.</div>"
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
            type="primary" if st.session_state.get("pbm_section") == section else "secondary",
            use_container_width=True,
        ):
            st.session_state["pbm_section"] = section
            st.rerun()
    st.markdown("</div><div class='mpb-rule'></div>", unsafe_allow_html=True)

    section = st.session_state.get("pbm_section")
    if section == "Profile Setup":
        render_member_plan_setup(load_member_plan_setup_options())
    elif section == "Meal Structure":
        _render_meals_with_selector_reset_guard(
            load_member_plan_recipe_options(),
            can_publish,
        )
    elif section == EXERCISE_SECTION:
        render_member_plan_exercise()
    elif section == SUPPLEMENT_SECTION:
        render_member_plan_supplement()
    else:
        render_view_member_plan_compact()
