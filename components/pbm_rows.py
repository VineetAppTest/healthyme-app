from __future__ import annotations

import copy
import uuid
from typing import Any, Dict, List

import streamlit as st

from components.pbm_core import (
    EXERCISE_TIME_OF_DAY,
    SOURCE_FIELDS,
    SUPPLEMENT_TIMELINE,
    SELECT_EXERCISE,
    SELECT_RECIPE,
    SELECT_SUPPLEMENT,
    clean,
    frequency_from_source,
    image_reference,
    new_row,
    row_has_content,
    rows_for,
    source_snapshot_for_item,
    timeline_from_source,
)
from components.profile_builder_canonical_sources import (
    apply_source_selection,
    current_source_option_id,
    source_option_labels,
    source_options_for_row,
)


def widget_key(row: Dict, field: str) -> str:
    return f"pbm_row_{row['ui_id']}_{field}"


def set_default(key: str, value) -> None:
    if key not in st.session_state:
        st.session_state[key] = value


def _clear_source_detail_widget_state(row: Dict[str, Any]) -> None:
    prefix = widget_key(row, "source_")
    selector_key = widget_key(row, "source_option_id")
    for key in list(st.session_state.keys()):
        if str(key).startswith(prefix) and str(key) != selector_key:
            st.session_state.pop(key, None)


def apply_source_defaults(kind: str, row: Dict, snapshot: Dict[str, Any]) -> None:
    if not snapshot:
        return
    if kind == "meal":
        portion = clean(snapshot.get("portion_size"))
        instruction = clean(snapshot.get("instructions") or snapshot.get("steps"))
        if portion:
            row["portion"] = portion
            st.session_state[widget_key(row, "portion")] = portion
        if instruction and not clean(row.get("instruction")):
            row["instruction"] = instruction
            st.session_state[widget_key(row, "instruction")] = instruction
    elif kind == "exercise":
        instruction = clean(snapshot.get("instructions"))
        if instruction:
            row["instruction"] = instruction
            st.session_state[widget_key(row, "instruction")] = instruction
    else:
        frequency = frequency_from_source(snapshot.get("frequency"))
        timeline = timeline_from_source(snapshot.get("timing"))
        dosage = clean(snapshot.get("dosage"))
        instruction = clean(snapshot.get("instructions"))
        if frequency:
            row["frequency"] = frequency
            st.session_state[widget_key(row, "frequency")] = frequency
        if timeline:
            row["timeline"] = timeline
            st.session_state[widget_key(row, "timeline")] = timeline
        if dosage:
            row["dosage"] = dosage
            st.session_state[widget_key(row, "dosage")] = dosage
        if instruction:
            row["instruction"] = instruction
            st.session_state[widget_key(row, "instruction")] = instruction


def _source_kind(kind: str) -> str:
    return "recipe" if kind == "meal" else kind


def _source_placeholder(kind: str) -> str:
    return {
        "meal": SELECT_RECIPE,
        "exercise": SELECT_EXERCISE,
        "supplement": SELECT_SUPPLEMENT,
    }[kind]


def _source_label(kind: str) -> str:
    return {
        "meal": "Recipe",
        "exercise": "Exercise",
        "supplement": "Supplement",
    }[kind]


def render_source_selector(
    column,
    kind: str,
    row: Dict[str, Any],
    options: Dict[str, Any],
) -> Dict[str, Any]:
    source_kind = _source_kind(kind)
    active_options = list(options.get(f"{source_kind}_sources") or [])
    row_options = source_options_for_row(source_kind, row, active_options)
    option_ids = [""] + [
        clean(option.get("option_id"))
        for option in row_options
        if clean(option.get("option_id"))
    ]
    labels = source_option_labels(row_options)
    placeholder = _source_placeholder(kind)
    selected_default = current_source_option_id(source_kind, row, row_options)
    source_key = widget_key(row, "source_option_id")
    if source_key not in st.session_state or st.session_state[source_key] not in option_ids:
        st.session_state[source_key] = selected_default if selected_default in option_ids else ""

    selected_option_id = column.selectbox(
        _source_label(kind),
        option_ids,
        format_func=lambda value: placeholder if not value else labels.get(value, value),
        key=source_key,
    )
    changed, snapshot = apply_source_selection(
        source_kind,
        row,
        selected_option_id,
        row_options,
    )
    if changed:
        _clear_source_detail_widget_state(row)
        apply_source_defaults(kind, row, snapshot)
    return snapshot


def source_detail_groups(kind: str):
    """Return accepted source-detail rows without duplicate instruction fields."""
    fields = [field for field in SOURCE_FIELDS[kind] if field[0] != "instructions"]
    if kind == "exercise":
        return (fields[:3], fields[3:6])
    if kind == "supplement":
        return (fields,)
    return (fields[:4], fields[4:])


def render_source_details(kind: str, row: Dict) -> None:
    snapshot = source_snapshot_for_item(kind, row)
    if not snapshot:
        return

    st.markdown(
        "<div class='hm-source-box'><b>Pulled Source Details</b> "
        "<span>Repository information is tied to the selected source ID; non-duplicate context remains editable.</span></div>",
        unsafe_allow_html=True,
    )
    defaults = dict(snapshot)
    defaults["image_reference"] = image_reference(snapshot)
    overrides = dict(row.get("source_admin_overrides") or {})

    for group in source_detail_groups(kind):
        if not group:
            continue
        columns = st.columns(len(group), gap="small")
        for column, (field, label, field_type) in zip(columns, group):
            key = widget_key(row, f"source_{field}")
            default = overrides.get(field, defaults.get(field, ""))
            set_default(key, clean(default))

            use_area = field_type == "area"
            if kind in {"exercise", "supplement"}:
                use_area = False
            elif kind == "meal" and field == "image_reference":
                use_area = True

            if use_area:
                value = column.text_area(
                    label,
                    key=key,
                    height=84,
                    disabled=field == "image_reference",
                )
            else:
                value = column.text_input(
                    label,
                    key=key,
                    disabled=field == "image_reference",
                )

            default_text = clean(defaults.get(field))
            if field != "image_reference" and clean(value) != default_text:
                overrides[field] = clean(value)
            else:
                overrides.pop(field, None)

    row["source_admin_overrides"] = overrides


def remove_row(ui_id: str) -> None:
    st.session_state["pbm_items"] = [
        row for row in st.session_state["pbm_items"] if row.get("ui_id") != ui_id
    ]
    for key in list(st.session_state.keys()):
        if str(key).startswith(f"pbm_row_{ui_id}_"):
            st.session_state.pop(key, None)


def render_row(kind: str, row: Dict, options: Dict[str, Any]) -> None:
    ui_id = row["ui_id"]
    if kind == "meal":
        columns = st.columns([.42, .20, .32, .06], gap="small")
        render_source_selector(columns[0], kind, row, options)
        portion_key = widget_key(row, "portion")
        set_default(portion_key, row.get("portion", ""))
        row["portion"] = columns[1].text_input("Portion", key=portion_key)
        instruction_key = widget_key(row, "instruction")
        set_default(instruction_key, row.get("instruction", ""))
        row["instruction"] = columns[2].text_input("Instruction", key=instruction_key)
        remove = columns[3].button("×", key=f"pbm_remove_{ui_id}", help="Remove row")
    elif kind == "exercise":
        columns = st.columns([.35, .22, .37, .06], gap="small")
        render_source_selector(columns[0], kind, row, options)
        time_key = widget_key(row, "scheduled_time")
        current = row.get("scheduled_time")
        current = "As advised" if current == "Night / As advised" else current
        set_default(
            time_key,
            current if current in EXERCISE_TIME_OF_DAY else "Morning",
        )
        row["scheduled_time"] = columns[1].selectbox(
            "Time of Day",
            EXERCISE_TIME_OF_DAY,
            key=time_key,
        )
        instruction_key = widget_key(row, "instruction")
        set_default(instruction_key, row.get("instruction", ""))
        row["instruction"] = columns[2].text_input("Instruction", key=instruction_key)
        remove = columns[3].button("×", key=f"pbm_remove_{ui_id}", help="Remove row")
    else:
        columns = st.columns([.22, .12, .24, .16, .20, .06], gap="small")
        render_source_selector(columns[0], kind, row, options)
        frequency_key = widget_key(row, "frequency")
        set_default(frequency_key, int(row.get("frequency") or 0))
        row["frequency"] = columns[1].number_input(
            "Frequency",
            min_value=0,
            max_value=7,
            step=1,
            key=frequency_key,
        )
        timeline_key = widget_key(row, "timeline")
        set_default(timeline_key, list(row.get("timeline") or []))
        row["timeline"] = columns[2].multiselect(
            "Timeline",
            SUPPLEMENT_TIMELINE,
            key=timeline_key,
        )
        dosage_key = widget_key(row, "dosage")
        set_default(dosage_key, row.get("dosage", ""))
        row["dosage"] = columns[3].text_input("Dosage", key=dosage_key)
        instruction_key = widget_key(row, "instruction")
        set_default(instruction_key, row.get("instruction", ""))
        row["instruction"] = columns[4].text_input("Instruction", key=instruction_key)
        remove = columns[5].button("×", key=f"pbm_remove_{ui_id}", help="Remove row")
        if row["frequency"] and len(row["timeline"]) != row["frequency"]:
            st.caption(
                f"Timeline validation: Frequency is {row['frequency']}; "
                f"select exactly {row['frequency']} timeline option(s)."
            )
    if remove:
        remove_row(ui_id)
        st.rerun()
    render_source_details(kind, row)


def add_row(kind: str, day: int, slot: str) -> None:
    rows = rows_for(kind, day, slot)
    row = new_row(kind, day, slot)
    row["item_order"] = len(rows) + 1
    st.session_state["pbm_items"].append(row)


def copy_day(kind: str, source_day: int, target_days: List[int]) -> None:
    source_rows = [
        row
        for row in st.session_state["pbm_items"]
        if row.get("item_type") == kind
        and int(row.get("day_number") or 0) == source_day
        and row_has_content(row)
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
    for key in list(st.session_state.keys()):
        if str(key).startswith("pbm_row_"):
            st.session_state.pop(key, None)
