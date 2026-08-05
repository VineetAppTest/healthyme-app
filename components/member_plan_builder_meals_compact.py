from __future__ import annotations

import copy
from typing import Any, Dict, List

import pandas as pd
import streamlit as st

from components.member_plan_builder_export import (
    load_member_plan_events,
    meal_review_rows,
    render_publish_log_and_download,
)
from components.pbm_core import (
    MEAL_SLOTS,
    SELECT_RECIPE,
    clean,
    clean_date,
    day_label,
    load_selected,
    member_maps,
    new_row,
    safe,
    safe_key,
    source_snapshot,
    storage_rows,
    with_placeholder,
)
from components.profile_builder_module_store import (
    EDIT_SCOPE_ALL,
    list_profiles_for_editing,
    save_profile_module,
    save_profile_shell,
)
from components.profile_publish_control import activate_profile, clear_publish_cache


_MEAL_PROFILE_SELECTOR = "mpb_meal_repository_profile"


def _repository_profile_label(row: Dict[str, Any]) -> str:
    return clean(row.get("profile_name")) or "Untitled Meal Profile"


def _render_publish_controls(
    can_publish: bool,
) -> tuple[Dict[str, Any], str, str, object, bool]:
    ok, profiles, message = list_profiles_for_editing(EDIT_SCOPE_ALL)
    if not ok:
        st.error(message)
        return {}, "", "", clean_date(""), False
    profiles = [
        row for row in profiles if clean(row.get("status")).lower() == "draft"
    ]
    profile_by_id = {
        clean(row.get("id")): row for row in profiles if clean(row.get("id"))
    }
    profile_ids = list(profile_by_id)
    if not profile_ids:
        st.info("Create a Meal Profile under Setup before building or publishing meals.")
        return {}, "", "", clean_date(""), False

    loaded_id = clean(st.session_state.get("pbm_loaded_profile_id"))
    if st.session_state.get(_MEAL_PROFILE_SELECTOR) not in profile_ids:
        st.session_state[_MEAL_PROFILE_SELECTOR] = (
            loaded_id if loaded_id in profile_ids else profile_ids[0]
        )

    member_labels, label_to_id, _id_to_label, _member_message = member_maps()
    controls = st.columns([0.36, 0.29, 0.18, 0.17], gap="small", vertical_alignment="bottom")
    selected_profile_id = controls[0].selectbox(
        "Meal Profile",
        profile_ids,
        format_func=lambda value: _repository_profile_label(profile_by_id[value]),
        key=_MEAL_PROFILE_SELECTOR,
    )
    if selected_profile_id != loaded_id:
        load_ok, load_message = load_selected(selected_profile_id, shell_only=False)
        if load_ok:
            st.rerun()
        st.error(load_message)
        return {}, "", "", clean_date(""), False

    selected_member_label = controls[1].selectbox(
        "Member",
        member_labels,
        key=f"mpb_meal_publish_member_{selected_profile_id}",
    )
    selected_member_id = label_to_id.get(selected_member_label, "")
    start_date = controls[2].date_input(
        "Plan Start Date",
        value=clean_date(""),
        key=f"mpb_meal_publish_start_{selected_profile_id}",
    )
    publish_clicked = controls[3].button(
        "Publish",
        type="primary",
        use_container_width=True,
        disabled=not can_publish or not bool(selected_member_id),
        key=f"mpb_publish_repository_plan_{selected_profile_id}",
        help="Publish a meal-only copy to the selected member.",
    )
    if not any(label_to_id.values()):
        st.caption("No active member directory entries are available for publishing.")
    return (
        profile_by_id[selected_profile_id],
        selected_member_id,
        selected_member_label,
        start_date,
        publish_clicked,
    )


def _publish_repository_plan(
    profile: Dict[str, Any],
    member_id: str,
    member_label: str,
    start_date: object,
) -> None:
    source_id = clean(profile.get("id"))
    meals = storage_rows("meal")
    if not source_id:
        st.error("Select a saved Meal Profile before publishing.")
        return
    if not member_id:
        st.error("Select a Member before publishing.")
        return
    if not meals:
        st.error("Add and save at least one Meal item before publishing.")
        return

    member_plan = copy.deepcopy(profile)
    member_plan.update(
        {
            "id": "",
            "status": "draft",
            "assigned_member_id": member_id,
            "assigned_member_label": member_label,
            "start_date": clean(start_date),
            "clone_source_profile_id": source_id,
            "clone_source_label": clean(profile.get("profile_name")),
            "created_by_user_id": st.session_state.get("user_id", ""),
            "created_by_email": st.session_state.get("user_email", ""),
        }
    )
    ok, member_plan_id, message = save_profile_shell(member_plan)
    if not ok:
        st.error(message)
        return

    meals_ok, meals_message = save_profile_module(
        member_plan_id,
        member_id,
        "meal",
        meals,
        created_by_user_id=st.session_state.get("user_id", ""),
        created_by_email=st.session_state.get("user_email", ""),
    )
    if not meals_ok:
        st.error(
            "The member-plan Draft was created, but its meals could not be copied. "
            f"{meals_message}"
        )
        return

    member_plan["id"] = member_plan_id
    active_ok, active_message = activate_profile(member_plan, "ACTIVATE")
    if not active_ok:
        st.error(active_message)
        return
    clear_publish_cache()
    load_member_plan_events.clear()
    st.session_state["mpb_publish_flash"] = (
        f"Meal Profile published to {member_label}. Exercise and Supplement remain "
        "independent allocations linked through this member's active Meal Plan."
    )
    st.rerun()


def _meal_rows(day: int, slot: str) -> List[Dict[str, Any]]:
    rows = [
        row
        for row in st.session_state.get("pbm_items") or []
        if clean(row.get("item_type")).lower() == "meal"
        and int(row.get("day_number") or 0) == day
        and clean(row.get("slot_name")) == slot
        and (
            clean(row.get("reference_label"))
            or clean(row.get("portion"))
            or clean(row.get("instruction"))
        )
    ]
    rows.sort(key=lambda row: int(row.get("item_order") or 1))
    return rows


def _clear_composer(day: int, slot: str) -> None:
    prefix = f"mpb_compose_{day}_{safe_key(slot)}_"
    for key in list(st.session_state.keys()):
        if str(key).startswith(prefix):
            st.session_state.pop(key, None)


def _remove_row(ui_id: str) -> None:
    st.session_state["pbm_items"] = [
        row
        for row in st.session_state.get("pbm_items") or []
        if clean(row.get("ui_id")) != clean(ui_id)
    ]
    for key in list(st.session_state.keys()):
        if str(key).startswith(f"mpb_added_{ui_id}_"):
            st.session_state.pop(key, None)


def _source_detail_lines(snapshot: Dict[str, Any]) -> List[tuple[str, str]]:
    labels = {
        "meal_type": "Meal Type",
        "diet_type": "Diet Type",
        "prep_time": "Prep Time",
        "calories": "Calories",
        "protein": "Protein",
        "fat": "Fat",
        "carbohydrates": "Carbohydrates",
        "ingredients": "Ingredients",
        "steps": "Preparation",
        "instructions": "Repository Instructions",
    }
    output: List[tuple[str, str]] = []
    for field, label in labels.items():
        value = clean(snapshot.get(field))
        if value:
            output.append((label, value))
    return output


def _render_more_details(snapshot: Dict[str, Any]) -> None:
    with st.expander("More details", expanded=False):
        details = _source_detail_lines(snapshot)
        if not details:
            st.caption("No additional repository information is available.")
            return
        detail_html = "".join(
            "<div class='mpb-responsive-detail'>"
            f"<b>{safe(label)}:</b><span>{safe(value)}</span></div>"
            for label, value in details
        )
        st.markdown(
            f"<div class='mpb-responsive-details'>{detail_html}</div>",
            unsafe_allow_html=True,
        )


def _snapshot_for(label: str, snapshots: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    if not clean(label):
        return {}
    if label not in snapshots:
        snapshots[label] = source_snapshot("meal", label)
    return snapshots[label]


def _add_composer_row(
    day: int,
    slot: str,
    recipe: str,
    portion: str,
    instruction: str,
) -> None:
    if not recipe:
        st.error("Select a Recipe before adding it.")
        return
    row = new_row("meal", day, slot)
    row["reference_label"] = recipe
    row["portion"] = portion
    row["instruction"] = instruction
    row["item_order"] = len(_meal_rows(day, slot)) + 1
    st.session_state["pbm_items"].append(row)
    st.session_state["mpb_meal_saved"] = False
    _clear_composer(day, slot)
    st.rerun()


def _render_added_row(
    row: Dict[str, Any],
    recipes: List[str],
    snapshots: Dict[str, Dict[str, Any]],
) -> None:
    ui_id = clean(row.get("ui_id"))
    recipe_options = with_placeholder(recipes, SELECT_RECIPE)
    current_recipe = clean(row.get("reference_label")) or SELECT_RECIPE
    if current_recipe not in recipe_options:
        recipe_options.append(current_recipe)

    columns = st.columns([0.38, 0.22, 0.32, 0.08], gap="small")
    selected = columns[0].selectbox(
        "Recipe",
        recipe_options,
        index=recipe_options.index(current_recipe),
        key=f"mpb_added_{ui_id}_recipe",
        label_visibility="collapsed",
    )
    selected = "" if selected == SELECT_RECIPE else selected
    if selected != clean(row.get("reference_label")):
        row["reference_label"] = selected
        snapshot = _snapshot_for(selected, snapshots)
        row["portion"] = clean(snapshot.get("portion_size"))
        st.session_state[f"mpb_added_{ui_id}_portion"] = row["portion"]
        st.session_state["mpb_meal_saved"] = False

    portion_key = f"mpb_added_{ui_id}_portion"
    instruction_key = f"mpb_added_{ui_id}_instruction"
    st.session_state.setdefault(portion_key, clean(row.get("portion")))
    st.session_state.setdefault(instruction_key, clean(row.get("instruction")))
    row["portion"] = columns[1].text_input(
        "Portion Guidance",
        key=portion_key,
        label_visibility="collapsed",
    )
    row["instruction"] = columns[2].text_input(
        "Instruction",
        key=instruction_key,
        label_visibility="collapsed",
        placeholder="Optional instruction",
    )
    if columns[3].button(
        "×",
        key=f"mpb_added_{ui_id}_remove",
        help="Remove item",
        use_container_width=True,
    ):
        _remove_row(ui_id)
        st.session_state["mpb_meal_saved"] = False
        st.rerun()
    _render_more_details(_snapshot_for(row.get("reference_label") or "", snapshots))


def _render_slot(
    day: int,
    slot: str,
    recipes: List[str],
    snapshots: Dict[str, Dict[str, Any]],
) -> None:
    slot_key = safe_key(slot)
    existing = _meal_rows(day, slot)
    with st.container(border=True):
        st.markdown(
            f"<div class='mpb-meal-card-title'>{safe(slot)}"
            f"<span>{len(existing)} added</span></div>",
            unsafe_allow_html=True,
        )
        for row in existing:
            _render_added_row(row, recipes, snapshots)

        recipe_key = f"mpb_compose_{day}_{slot_key}_recipe"
        portion_key = f"mpb_compose_{day}_{slot_key}_portion"
        instruction_key = f"mpb_compose_{day}_{slot_key}_instruction"
        last_recipe_key = f"{recipe_key}_last"
        options = with_placeholder(recipes, SELECT_RECIPE)

        compose = st.columns([0.38, 0.22, 0.30, 0.10], gap="small")
        selected_recipe = compose[0].selectbox(
            f"Add Recipe — {slot}",
            options,
            key=recipe_key,
            label_visibility="collapsed",
        )
        selected_recipe = "" if selected_recipe == SELECT_RECIPE else selected_recipe
        snapshot = _snapshot_for(selected_recipe, snapshots)
        repository_portion = clean(snapshot.get("portion_size"))

        if portion_key not in st.session_state:
            st.session_state[portion_key] = repository_portion
        elif selected_recipe != clean(st.session_state.get(last_recipe_key)):
            st.session_state[portion_key] = repository_portion
        st.session_state[last_recipe_key] = selected_recipe

        portion = compose[1].text_input(
            "Portion Guidance",
            key=portion_key,
            label_visibility="collapsed",
            placeholder="Portion guidance",
        )
        instruction = compose[2].text_input(
            "Instruction",
            key=instruction_key,
            label_visibility="collapsed",
            placeholder="Optional instruction",
        )
        if compose[3].button(
            "Add",
            key=f"mpb_compose_{day}_{slot_key}_add",
            type="primary",
            use_container_width=True,
            disabled=not bool(selected_recipe),
        ):
            _add_composer_row(day, slot, selected_recipe, portion, instruction)
        if selected_recipe:
            _render_more_details(snapshot)


def _render_day_picker() -> int:
    st.session_state.setdefault("mpb_meal_day", 1)
    columns = st.columns(7, gap="small")
    for column, day in zip(columns, range(1, 8)):
        if column.button(
            f"Day {day}",
            key=f"mpb_day_{day}",
            type="primary"
            if int(st.session_state.get("mpb_meal_day", 1)) == day
            else "secondary",
            use_container_width=True,
            help=day_label(day),
        ):
            st.session_state["mpb_meal_day"] = day
            st.rerun()
    return int(st.session_state.get("mpb_meal_day", 1))


def _render_review_table() -> None:
    rows = meal_review_rows(st.session_state.get("pbm_items") or [])
    if rows:
        st.dataframe(
            pd.DataFrame(rows).drop(columns=["Order"], errors="ignore"),
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info("No Meal items have been added yet.")


def render_member_plan_meals_compact(recipes: List[str], can_publish: bool) -> None:
    st.markdown(
        """
<style id="hm-admin-plan-builder-responsive-details-v1">
.mpb-responsive-details{display:flex;flex-wrap:wrap;align-items:flex-start;gap:.48rem 1rem;width:100%;}
.mpb-responsive-detail{display:inline-flex;align-items:flex-start;gap:.25rem;flex:0 1 auto;max-width:100%;font-size:.82rem;line-height:1.35;color:#334155;white-space:normal;}
.mpb-responsive-detail b{color:#064E3B;white-space:nowrap;}
.mpb-responsive-detail span{min-width:0;overflow-wrap:anywhere;}
@media(max-width:720px){.mpb-responsive-detail{flex:1 1 100%;}}
</style>
""",
        unsafe_allow_html=True,
    )
    st.markdown(
        "<div class='hm-title'>Meals</div>"
        "<div class='hm-sub'>Select a reusable Meal Profile and member, then build or publish the meal allocation.</div>",
        unsafe_allow_html=True,
    )
    (
        _selected_profile,
        publish_member_id,
        publish_member_label,
        publish_start_date,
        publish_clicked,
    ) = _render_publish_controls(can_publish)
    profile = st.session_state.get("pbm_profile") or {}
    profile_id = clean(profile.get("id"))
    if not profile_id:
        return
    if publish_clicked:
        _publish_repository_plan(
            profile,
            publish_member_id,
            publish_member_label,
            publish_start_date,
        )

    st.markdown(
        "<div class='mpb-integrity-note'>Publishing creates a meal-only member-plan copy. "
        "The repository Meal Profile stays reusable; Exercise and Supplement allocations "
        "are managed separately.</div>",
        unsafe_allow_html=True,
    )
    day = _render_day_picker()
    st.caption(day_label(day))

    snapshots: Dict[str, Dict[str, Any]] = {}
    for slot in MEAL_SLOTS:
        _render_slot(day, slot, recipes, snapshots)

    if st.button(
        "Save Meal Plan",
        type="primary",
        use_container_width=True,
        key="mpb_save_meals",
    ):
        ok, message = save_profile_module(
            profile_id,
            clean(profile.get("assigned_member_id")),
            "meal",
            storage_rows("meal"),
            created_by_user_id=st.session_state.get("user_id", ""),
            created_by_email=st.session_state.get("user_email", ""),
        )
        if ok:
            st.session_state["mpb_meal_saved"] = True
            load_member_plan_events.clear()
            st.success(message)
        else:
            st.error(message)

    meal_items = [
        row
        for row in st.session_state.get("pbm_items") or []
        if clean(row.get("item_type")).lower() == "meal"
    ]
    show_review = bool(st.session_state.get("mpb_meal_saved")) or any(
        clean(row.get("id")) for row in meal_items
    )
    if show_review:
        st.markdown(
            "<div class='hm-title'>Meal Plan Review</div>"
            "<div class='hm-sub'>Saved items across all seven days.</div>",
            unsafe_allow_html=True,
        )
        _render_review_table()

    flash = st.session_state.pop("mpb_publish_flash", "")
    if flash:
        st.success(flash)

    if not can_publish:
        st.caption("Publishing is restricted to Admin and Super Admin.")

    render_publish_log_and_download(
        profile,
        st.session_state.get("pbm_items") or [],
    )
