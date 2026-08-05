from __future__ import annotations

import copy
import uuid
from typing import Dict, List

import streamlit as st

from components.pbm_core import (
    SELECT_AGE,
    SELECT_DIET,
    bump_epoch,
    clean,
    load_selected,
    profile_payload,
    reset_profile,
    with_placeholder,
)
from components.profile_builder_module_store import (
    list_profiles_for_repository,
    save_profile_module,
    save_profile_shell,
)
from components.recommendation_profile_store import check_profile_builder_store


NEW_PLAN = "__new_plan__"
_SELECTOR_KEY = "mpb_plan_selector"
_SELECTOR_NEXT_KEY = "mpb_plan_selector_next"
_LAST_SELECTOR_KEY = "mpb_last_plan_selector"


def _profile_label(row: Dict) -> str:
    status = clean(row.get("status"), "draft").title()
    return f"{clean(row.get('profile_name')) or 'Untitled'} · {status}"


def _queue_plan_selector(plan_id: str) -> None:
    """Defer selector changes until the next run, before its widget is created."""

    st.session_state[_SELECTOR_NEXT_KEY] = plan_id
    st.session_state[_LAST_SELECTOR_KEY] = plan_id


def _apply_queued_plan_selector(selector_options: List[str], loaded_id: str) -> None:
    """Set selector state only before Streamlit instantiates the selectbox."""

    queued = clean(st.session_state.pop(_SELECTOR_NEXT_KEY, ""))
    if queued:
        st.session_state[_SELECTOR_KEY] = (
            queued if queued in selector_options else NEW_PLAN
        )

    if _SELECTOR_KEY not in st.session_state:
        st.session_state[_SELECTOR_KEY] = (
            loaded_id if loaded_id in selector_options else NEW_PLAN
        )
    if st.session_state[_SELECTOR_KEY] not in selector_options:
        st.session_state[_SELECTOR_KEY] = NEW_PLAN

    if _LAST_SELECTOR_KEY not in st.session_state:
        st.session_state[_LAST_SELECTOR_KEY] = st.session_state[_SELECTOR_KEY]


def _new_plan() -> None:
    reset_profile()
    _queue_plan_selector(NEW_PLAN)
    st.session_state["mpb_setup_flash"] = "New blank meal plan started."


def _handle_plan_selection(selected_id: str) -> None:
    previous = clean(st.session_state.get(_LAST_SELECTOR_KEY))
    if selected_id == previous:
        return
    st.session_state[_LAST_SELECTOR_KEY] = selected_id
    if selected_id == NEW_PLAN:
        reset_profile()
        st.session_state["mpb_setup_flash"] = "New blank meal plan started."
        st.rerun()

    ok, message = load_selected(selected_id, shell_only=False)
    if ok:
        st.session_state["mpb_setup_flash"] = message
        st.rerun()
    st.error(message)


def _clone_meal_profile() -> None:
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
    clone["assigned_member_id"] = ""
    clone["assigned_member_label"] = ""
    clone["start_date"] = ""
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
        "",
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
    st.session_state["pbm_loaded_member_id"] = ""
    _queue_plan_selector(new_id)
    st.session_state["mpb_setup_flash"] = (
        f"Meal Profile cloned as a new Draft. {len(meals)} meal row(s) copied. "
        "Exercise and Supplement allocations were not copied."
    )
    bump_epoch()
    st.rerun()


def render_member_plan_setup(options: Dict[str, List[str]]) -> None:
    st.markdown("<div class='hm-title'>Setup</div>", unsafe_allow_html=True)
    st.markdown(
        """
<style id="hm-member-plan-setup-sections-v4">
.mpb-setup-group-title{
  display:flex;
  align-items:center;
  gap:.55rem;
  color:#064E3B;
  font-size:.76rem;
  font-weight:950;
  text-transform:uppercase;
  letter-spacing:.04em;
  margin:.58rem 0 .18rem;
}
.mpb-setup-group-title:after{
  content:"";
  flex:1;
  height:1px;
  background:#F0DFC0;
}
</style>
""",
        unsafe_allow_html=True,
    )

    ok_profiles, profiles, profile_message = list_profiles_for_repository()
    if not ok_profiles:
        profiles = []
        st.warning(profile_message)
    profile_by_id = {
        clean(row.get("id")): row for row in profiles if clean(row.get("id"))
    }
    selector_options = [NEW_PLAN] + list(profile_by_id.keys())
    loaded_id = clean(st.session_state.get("pbm_loaded_profile_id"))
    _apply_queued_plan_selector(selector_options, loaded_id)

    select_col, new_col, clone_col = st.columns(
        [0.58, 0.18, 0.24],
        gap="small",
        vertical_alignment="bottom",
    )
    selected_id = select_col.selectbox(
        "Select Meal Plan",
        selector_options,
        key=_SELECTOR_KEY,
        label_visibility="collapsed",
        format_func=lambda value: (
            "New Meal Plan" if value == NEW_PLAN else _profile_label(profile_by_id[value])
        ),
    )
    if new_col.button("New Plan", use_container_width=True, key="mpb_new_plan"):
        _new_plan()
        st.rerun()
    clone_disabled = not bool(loaded_id)
    if clone_col.button(
        "Clone Meal Profile",
        use_container_width=True,
        disabled=clone_disabled,
        key="mpb_clone_complete_plan",
    ):
        _clone_meal_profile()

    _handle_plan_selection(selected_id)

    flash = st.session_state.pop("mpb_setup_flash", "")
    if flash:
        st.success(flash)

    profile = st.session_state["pbm_profile"]
    epoch = int(st.session_state.get("pbm_epoch", 0))
    profile_status = clean(profile.get("status"), "draft").lower()
    assigned_member_id = clean(profile.get("assigned_member_id"))
    setup_editable = profile_status == "draft" and not assigned_member_id

    if loaded_id and not setup_editable:
        st.caption(
            "This allocated or historical Meal Profile is retained read-only. "
            "Use Clone Meal Profile to create an editable, reusable Draft."
        )

    row1 = st.columns(1, gap="small")
    profile["profile_name"] = row1[0].text_input(
        "Plan Name",
        value=clean(profile.get("profile_name")),
        placeholder="Plan Name",
        label_visibility="collapsed",
        disabled=not setup_editable,
        key=f"mpb_profile_name_{epoch}",
    )
    if setup_editable:
        profile["assigned_member_label"] = ""
        profile["assigned_member_id"] = ""
        profile["start_date"] = ""

    st.markdown(
        "<div class='mpb-setup-group-title'>Profile classification</div>",
        unsafe_allow_html=True,
    )
    classification_cols = st.columns(
        [1.15, 1, 1, 1.15],
        gap="small",
        vertical_alignment="bottom",
    )
    profile["region"] = classification_cols[0].text_input(
        "Region / Food Culture",
        value=clean(profile.get("region")),
        disabled=not setup_editable,
        key=f"mpb_region_{epoch}",
    )
    diet_options = with_placeholder(list(options.get("diet_type") or []), SELECT_DIET)
    current_diet = clean(profile.get("diet_type")) or SELECT_DIET
    if current_diet not in diet_options:
        diet_options.append(current_diet)
    profile["diet_type"] = classification_cols[1].selectbox(
        "Diet Type",
        diet_options,
        index=diet_options.index(current_diet),
        disabled=not setup_editable,
        key=f"mpb_diet_{epoch}",
    )
    age_options = with_placeholder(list(options.get("age_band") or []), SELECT_AGE)
    current_age = clean(profile.get("age_band")) or SELECT_AGE
    if current_age not in age_options:
        age_options.append(current_age)
    profile["age_band"] = classification_cols[2].selectbox(
        "Age Band",
        age_options,
        index=age_options.index(current_age),
        disabled=not setup_editable,
        key=f"mpb_age_{epoch}",
    )

    concerns = list(options.get("health_concern") or [])
    for concern in profile.get("health_concerns") or []:
        if concern not in concerns:
            concerns.append(concern)
    profile["health_concerns"] = classification_cols[3].multiselect(
        "Health Concerns",
        concerns,
        default=list(profile.get("health_concerns") or []),
        disabled=not setup_editable,
        key=f"mpb_concerns_{epoch}",
    )

    st.markdown(
        "<div class='mpb-setup-group-title'>Internal notes</div>",
        unsafe_allow_html=True,
    )
    note_col, change_col = st.columns(2, gap="small")
    profile["profile_note"] = note_col.text_area(
        "Nutritionist Note",
        value=clean(profile.get("profile_note")),
        height=72,
        disabled=not setup_editable,
        key=f"mpb_note_{epoch}",
    )
    profile["change_note"] = change_col.text_area(
        "Change Note",
        value=clean(profile.get("change_note")),
        height=72,
        disabled=not setup_editable,
        key=f"mpb_change_note_{epoch}",
    )

    if st.button(
        "Save Setup",
        type="primary",
        use_container_width=True,
        disabled=(
            not check_profile_builder_store().get("ok") or not setup_editable
        ),
        key="mpb_save_setup",
    ):
        payload = {
            **profile_payload(),
            "assigned_member_id": "",
            "assigned_member_label": "",
            "start_date": "",
            "status": "draft",
        }
        ok, profile_id, message = save_profile_shell(payload)
        if ok:
            profile["id"] = profile_id
            st.session_state["pbm_loaded_profile_id"] = profile_id
            st.session_state["pbm_loaded_member_id"] = ""
            _queue_plan_selector(profile_id)
            st.session_state["mpb_setup_flash"] = message
            st.rerun()
        else:
            st.error(message)
