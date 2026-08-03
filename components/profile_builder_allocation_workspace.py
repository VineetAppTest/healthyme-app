from __future__ import annotations

import streamlit as st

from components.pbm_core import SELECT_MEMBER, clean, safe


PROFILE_BUILDER_ROUTE = "pages/38_Admin_Recommendation_Profile_Builder.py"
EXERCISE_ALLOCATION_ROUTE = "pages/42_Admin_Exercise_Member_Allocation.py"
SUPPLEMENT_ALLOCATION_ROUTE = "pages/43_Admin_Supplement_Member_Allocation.py"


def _assigned_member() -> tuple[str, str]:
    profile = dict(st.session_state.get("pbm_profile") or {})
    member_id = clean(profile.get("assigned_member_id"))
    member_label = clean(profile.get("assigned_member_label"))
    if member_label == SELECT_MEMBER:
        member_label = ""
    return member_id, member_label


def _open_allocation(route: str, member_label: str, member_id: str) -> None:
    # The independent allocation pages retain their own write authorities. Only
    # the selected Profile Builder member context and return route are shared.
    if route == EXERCISE_ALLOCATION_ROUTE:
        st.session_state["phase_c_member"] = member_label
        st.session_state["phase_c_return_page"] = PROFILE_BUILDER_ROUTE
    else:
        st.session_state["phase_d_member"] = member_label
        st.session_state["phase_d_return_page"] = PROFILE_BUILDER_ROUTE
    st.session_state["pbm_loaded_member_id"] = member_id
    st.switch_page(route)


def render_profile_builder_allocation_workspace() -> None:
    member_id, member_label = _assigned_member()
    st.markdown(
        "<div class='hm-title'>Allocate Exercise &amp; Supplement</div>"
        "<div class='hm-sub'>Use the selected profile member and continue into the focused allocation workflow.</div>",
        unsafe_allow_html=True,
    )

    if not member_id:
        st.info(
            "Select and save a Member Assignment under Setup before allocating Exercise or Supplement items."
        )
        return

    st.markdown(
        f"<div class='hm-allocation-member'><b>Member:</b> {safe(member_label or member_id)}</div>",
        unsafe_allow_html=True,
    )

    exercise_col, supplement_col = st.columns(2, gap="large")
    with exercise_col:
        st.markdown(
            "<div class='hm-allocation-card'><b>Exercise allocation</b>"
            "<span>Select an active Exercise repository item, set dates and member instructions, or manage an existing allocation.</span></div>",
            unsafe_allow_html=True,
        )
        if st.button(
            "Allocate Exercise",
            type="primary",
            use_container_width=True,
            key="pbm_open_exercise_allocation",
        ):
            _open_allocation(EXERCISE_ALLOCATION_ROUTE, member_label, member_id)

    with supplement_col:
        st.markdown(
            "<div class='hm-allocation-card'><b>Supplement allocation</b>"
            "<span>Select an active Supplement repository item, set dosage and timing, or manage an existing allocation.</span></div>",
            unsafe_allow_html=True,
        )
        if st.button(
            "Allocate Supplement",
            type="primary",
            use_container_width=True,
            key="pbm_open_supplement_allocation",
        ):
            _open_allocation(SUPPLEMENT_ALLOCATION_ROUTE, member_label, member_id)

    st.caption(
        "Exercise and Supplement remain independent allocation workflows; this tab only provides one compact entry point using the selected member."
    )
