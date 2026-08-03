from __future__ import annotations

import copy
import uuid
from typing import Dict, List

import streamlit as st

from components.pbm_core import (
    SELECT_AGE,
    SELECT_DIET,
    SELECT_MEMBER,
    bump_epoch,
    clean,
    clean_date,
    load_selected,
    member_maps,
    profile_payload,
    reset_profile,
    with_placeholder,
)
from components.profile_builder_module_store import (
    EDIT_SCOPE_ALL,
    list_profiles_for_editing,
    save_profile_module,
    save_profile_shell,
)
from components.recommendation_profile_store import check_profile_builder_store


NEW_PLAN = "__new_plan__"


def _profile_label(row: Dict) -> str:
    status = clean(row.get("status"), "draft").title()
    member = clean(row.get("assigned_member_label")) or "Unallocated"
    return f"{clean(row.get('profile_name')) or 'Untitled'} · {member} · {status}"


def _new_plan() -> None:
    reset_profile()
    st.session_state["mpb_plan_selector"] = NEW_PLAN
    st.session_state["mpb_setup_flash"] = "New blank meal plan started."


def _handle_plan_selection(selected_id: str) -> None:
    previous = clean(st.session_state.get("mpb_last_plan_selector"))
    if selected_id == previous:
        return
    st.session_state["mpb_last_plan_selector"] = selected_id
    if selected_id == NEW_PLAN:
        reset_profile()
        st.session_state["mpb_plan_selector"] = NEW_PLAN
        st.session_state["mpb_setup_flash"] = "New blank meal plan started."
        st.rerun()

    ok, message = load_selected(selected_id, shell_only=False)
    if ok:
        st.session_state["mpb_setup_flash"] = message
        st.session_state["mpb_plan_selector"] = selected_id
        st.rerun()
    st.error(message)


def _clone_complete_plan() -> None:
    profile = copy.deepcopy(st.session_state.get("pbm_profile") or {})
    source_id = clean(profile.get("id"))
    source_name = clean(profile.get("profile_name")) or "Selected plan"
    meals = [
        copy.deepcopy(row)
        for row in st.session_state.get("pbm_items") or []
        if clean(row.get("item_type")).lower() == "meal"
    ]
    if not source_id:
        st.error("Load and save a plan before cloning it.")
        return
    if not meals:
        st.error("The selected plan has no saved meal rows to clone.")
        return

    clone = copy.deepcopy(profile)
    clone["id"] = ""
    clone["status"] = "draft"
    clone["profile_name"] = f"Copy of {source_name}"
    clone["clone_source_profile_id"] = source_id
    clone["clone_source_label"] = source_name
    clone["created_by_user_id"] = st.session_state.get("user_id", "")
    clone["created_by_email"] = st.session_state.get("user_email", "")

    ok, new_id, message = save_profile_shell(clone)
    if not ok:
        st.error(message)
        return

    for index, row in enumerate(meals, 1):
        row["ui_id"] = uuid.uuid4().hex
        row["id"] = ""
        row["item_order"] = int(row.get("item_order") or index)

    save_ok, save_message = save_profile_module(
        new_id,
        clean(clone.get("assigned_member_id")),
        "meal",
        meals,
        created_by_user_id=st.session_state.get("user_id", ""),
        created_by_email=st.session_state.get("user_email", ""),
    )
    if not save_ok:
        st.error(
            f"The new Draft was created, but its meals could not be copied. {save_message}"
        )
        return

    clone["id"] = new_id
    st.session_state["pbm_profile"] = clone
    st.session_state["pbm_items"] = meals
    st.session_state["pbm_loaded_profile_id"] = new_id
    st.session_state["pbm_loaded_member_id"] = clean(clone.get("assigned_member_id"))
    st.session_state["mpb_plan_selector"] = new_id
    st.session_state["mpb_setup_flash"] = (
        f"Complete meal plan cloned as a new Draft. {len(meals)} meal row(s) copied."
    )
    bump_epoch()
    st.rerun()


def render_member_plan_setup(options: Dict[str, List[str]]) -> None:
    st.markdown(
        "<div class='hm-title'>Setup</div>"
        "<div class='hm-sub'>Select a plan and it loads automatically. Keep only the information needed to build and allocate the meal plan.</div>",
        unsafe_allow_html=True,
    )

    member_labels, label_to_id, id_to_label, _member_message = member_maps()
    ok_profiles, profiles, profile_message = list_profiles_for_editing(EDIT_SCOPE_ALL)
    if not ok_profiles:
        profiles = []
        st.warning(profile_message)

    profile_by_id = {
        clean(row.get("id")): row for row in profiles if clean(row.get("id"))
    }
    selector_options = [NEW_PLAN] + list(profile_by_id.keys())
    loaded_id = clean(st.session_state.get("pbm_loaded_profile_id"))
    if "mpb_plan_selector" not in st.session_state:
        st.session_state["mpb_plan_selector"] = (
            loaded_id if loaded_id in selector_options else NEW_PLAN
        )
    if st.session_state["mpb_plan_selector"] not in selector_options:
        st.session_state["mpb_plan_selector"] = NEW_PLAN

    select_col, new_col, clone_col = st.columns([0.58, 0.18, 0.24], gap="small")
    selected_id = select_col.selectbox(
        "Meal Plan",
        selector_options,
        key="mpb_plan_selector",
        format_func=lambda value: (
            "New Meal Plan" if value == NEW_PLAN else _profile_label(profile_by_id[value])
        ),
    )
    if new_col.button("New Plan", use_container_width=True, key="mpb_new_plan"):
        _new_plan()
        st.rerun()
    clone_disabled = not bool(loaded_id)
    if clone_col.button(
        "Clone Complete Plan",
        use_container_width=True,
        disabled=clone_disabled,
        key="mpb_clone_complete_plan",
    ):
        _clone_complete_plan()

    _handle_plan_selection(selected_id)

    flash = st.session_state.pop("mpb_setup_flash", "")
    if flash:
        st.success(flash)

    profile = st.session_state["pbm_profile"]
    epoch = int(st.session_state.get("pbm_epoch", 0))

    current_member_id = clean(profile.get("assigned_member_id"))
    current_member = id_to_label.get(
        current_member_id,
        clean(profile.get("assigned_member_label")) or SELECT_MEMBER,
    )
    if current_member not in member_labels:
        current_member = SELECT_MEMBER

    row1 = st.columns([0.42, 0.34, 0.24], gap="small")
    profile["profile_name"] = row1[0].text_input(
        "Plan Name",
        value=clean(profile.get("profile_name")),
        key=f"mpb_profile_name_{epoch}",
    )
    selected_member = row1[1].selectbox(
        "Member",
        member_labels,
        index=member_labels.index(current_member),
        key=f"mpb_member_{epoch}",
        disabled=(
            bool(profile.get("id"))
            and clean(profile.get("status")).lower() == "active"
        ),
    )
    profile["assigned_member_label"] = selected_member
    profile["assigned_member_id"] = label_to_id.get(selected_member, "")
    profile["start_date"] = row1[2].date_input(
        "Plan Start Date",
        value=clean_date(profile.get("start_date")),
        key=f"mpb_start_date_{epoch}",
    )

    row2 = st.columns(3, gap="small")
    profile["region"] = row2[0].text_input(
        "Region / Food Culture",
        value=clean(profile.get("region")),
        key=f"mpb_region_{epoch}",
    )
    diet_options = with_placeholder(list(options.get("diet_type") or []), SELECT_DIET)
    current_diet = clean(profile.get("diet_type")) or SELECT_DIET
    if current_diet not in diet_options:
        diet_options.append(current_diet)
    profile["diet_type"] = row2[1].selectbox(
        "Diet Type",
        diet_options,
        index=diet_options.index(current_diet),
        key=f"mpb_diet_{epoch}",
    )
    age_options = with_placeholder(list(options.get("age_band") or []), SELECT_AGE)
    current_age = clean(profile.get("age_band")) or SELECT_AGE
    if current_age not in age_options:
        age_options.append(current_age)
    profile["age_band"] = row2[2].selectbox(
        "Age Band",
        age_options,
        index=age_options.index(current_age),
        key=f"mpb_age_{epoch}",
    )

    concerns = list(options.get("health_concern") or [])
    for concern in profile.get("health_concerns") or []:
        if concern not in concerns:
            concerns.append(concern)
    profile["health_concerns"] = st.multiselect(
        "Health Concerns",
        concerns,
        default=list(profile.get("health_concerns") or []),
        key=f"mpb_concerns_{epoch}",
    )

    with st.expander("More setup details", expanded=False):
        profile["profile_note"] = st.text_area(
            "Nutritionist Note",
            value=clean(profile.get("profile_note")),
            height=90,
            key=f"mpb_note_{epoch}",
        )
        profile["change_note"] = st.text_input(
            "Change Note",
            value=clean(profile.get("change_note")),
            key=f"mpb_change_note_{epoch}",
        )
        st.caption(
            "Clone Complete Plan copies Setup and all seven-day Meal rows into a new Draft. Exercise and Supplement allocations retain their independent IDs and history."
        )

    if st.button(
        "Save Setup",
        type="primary",
        use_container_width=True,
        disabled=not check_profile_builder_store().get("ok"),
        key="mpb_save_setup",
    ):
        ok, profile_id, message = save_profile_shell(profile_payload())
        if ok:
            profile["id"] = profile_id
            st.session_state["pbm_loaded_profile_id"] = profile_id
            st.session_state["pbm_loaded_member_id"] = clean(
                profile.get("assigned_member_id")
            )
            st.session_state["mpb_plan_selector"] = profile_id
            st.success(message)
        else:
            st.error(message)
