from __future__ import annotations

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
    day_label,
    new_row,
    safe,
    safe_key,
    source_snapshot,
    storage_rows,
    with_placeholder,
)
from components.profile_builder_module_store import save_profile_module
from components.profile_publish_control import activate_profile, clear_publish_cache


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
        if clean(key).startswith(f"mpb_added_{ui_id}_"):
            st.session_state.pop(key, None)


def _source_detail_lines(snapshot: Dict[str, Any]) -> List[tuple[str, str]]:
    labels = {
        "meal_type": "Meal Type",
        "diet_type": "Diet Type",
        "prep_time": "Prep Time",
        "calories": "Calories",
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


def _render_more_details(snapshot: Dict[str, Any], label: str) -> None:
    with st.expander(f"More details — {label}", expanded=False):
        details = _source_detail_lines(snapshot)
        if not details:
            st.caption("No additional repository information is available.")
            return
        for label, value in details:
            st.markdown(f"**{label}:** {safe(value)}")


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
    _clear_composer(day, slot)
    st.rerun()


def _render_added_row(
    row: Dict[str, Any],
    recipes: List[str],
) -> None:
    ui_id = clean(row.get("ui_id"))
    recipe_options = with_placeholder(recipes, SELECT_RECIPE)
    current_recipe = clean(row.get("reference_label")) or SELECT_RECIPE
    if current_recipe not in recipe_options:
        recipe_options.append(current_recipe)

    columns = st.columns([0.35, 0.22, 0.35, 0.08], gap="small")
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
        snapshot = source_snapshot("meal", selected)
        row["portion"] = clean(snapshot.get("portion_size"))
        st.session_state[f"mpb_added_{ui_id}_portion"] = row["portion"]

    if f"mpb_added_{ui_id}_portion" not in st.session_state:
        st.session_state[f"mpb_added_{ui_id}_portion"] = clean(row.get("portion"))
    row["portion"] = columns[1].text_input(
        "Portion Guidance",
        key=f"mpb_added_{ui_id}_portion",
        label_visibility="collapsed",
    )
    if f"mpb_added_{ui_id}_instruction" not in st.session_state:
        st.session_state[f"mpb_added_{ui_id}_instruction"] = clean(
            row.get("instruction")
        )
    row["instruction"] = columns[2].text_input(
        "Instruction",
        key=f"mpb_added_{ui_id}_instruction",
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
        st.rerun()
    _render_more_details(
        source_snapshot("meal", row.get("reference_label") or ""),
        clean(row.get("reference_label")) or "Recipe",
    )


def _render_slot(day: int, slot: str, recipes: List[str]) -> None:
    slot_key = safe_key(slot)
    st.markdown(
        f"<div class='mpb-meal-card-title'>{safe(slot)}</div>",
        unsafe_allow_html=True,
    )

    existing = _meal_rows(day, slot)
    for row in existing:
        _render_added_row(row, recipes)

    recipe_key = f"mpb_compose_{day}_{slot_key}_recipe"
    portion_key = f"mpb_compose_{day}_{slot_key}_portion"
    instruction_key = f"mpb_compose_{day}_{slot_key}_instruction"
    last_recipe_key = f"{recipe_key}_last"
    options = with_placeholder(recipes, SELECT_RECIPE)

    compose = st.columns([0.42, 0.22, 0.26, 0.10], gap="small")
    selected_recipe = compose[0].selectbox(
        f"Add Recipe — {slot}",
        options,
        key=recipe_key,
        label_visibility="collapsed",
    )
    selected_recipe = "" if selected_recipe == SELECT_RECIPE else selected_recipe
    snapshot = source_snapshot("meal", selected_recipe)
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
        _render_more_details(snapshot, slot)


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


def _publish_current_plan() -> None:
    profile = st.session_state.get("pbm_profile") or {}
    profile_id = clean(profile.get("id"))
    if not profile_id:
        st.error("Save Setup and Meals before publishing.")
        return
    if clean(profile.get("status")).lower() == "active":
        st.info("This plan is already active for the selected member.")
        return
    if not clean(profile.get("assigned_member_id")):
        st.error("Select and save a Member under Setup before publishing.")
        return
    if not meal_review_rows(st.session_state.get("pbm_items") or []):
        st.error("Add and save at least one Meal item before publishing.")
        return
    try:
        ok, message = activate_profile(profile, "ACTIVATE")
        if ok:
            profile["status"] = "active"
            clear_publish_cache()
            load_member_plan_events.clear()
            st.session_state["mpb_publish_flash"] = message
            st.rerun()
        st.error(message)
    except Exception as exc:
        st.error(f"Could not publish the meal plan: {exc}")


def render_member_plan_meals(recipes: List[str], can_publish: bool) -> None:
    profile = st.session_state.get("pbm_profile") or {}
    profile_id = clean(profile.get("id"))
    if not profile_id:
        st.info("Create or select a Meal Plan under Setup first.")
        return

    st.markdown(
        "<div class='hm-title'>Meals</div>"
        "<div class='hm-sub'>Build one day at a time. Select a repository recipe, confirm the portion guidance and add it to the fixed meal slot.</div>",
        unsafe_allow_html=True,
    )
    day = _render_day_picker()
    st.caption(day_label(day))

    for slot in MEAL_SLOTS:
        st.markdown("<div class='mpb-meal-card'>", unsafe_allow_html=True)
        _render_slot(day, slot, recipes)
        st.markdown("</div>", unsafe_allow_html=True)

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

    st.markdown(
        "<div class='hm-title'>Saved Meal Plan Review</div>"
        "<div class='hm-sub'>The complete seven-day plan is shown in one table after Save. This replaces the earlier Preview workflow.</div>",
        unsafe_allow_html=True,
    )
    _render_review_table()

    flash = st.session_state.pop("mpb_publish_flash", "")
    if flash:
        st.success(flash)

    publish_label = (
        "Plan Already Active"
        if clean(profile.get("status")).lower() == "active"
        else "Publish & Allocate to Member"
    )
    if st.button(
        publish_label,
        type="primary",
        use_container_width=True,
        disabled=(
            not can_publish
            or clean(profile.get("status")).lower() == "active"
        ),
        key="mpb_publish_current_plan",
    ):
        _publish_current_plan()
    if not can_publish:
        st.caption("Publishing is restricted to Admin and Super Admin.")

    render_publish_log_and_download(
        profile,
        st.session_state.get("pbm_items") or [],
    )
