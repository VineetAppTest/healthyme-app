from __future__ import annotations

import datetime as dt
from typing import Dict, List

import pandas as pd
import streamlit as st

from components.db import list_members
from components.exercise_member_allocation import (
    list_active_exercise_sources,
    list_member_exercise_allocations,
    save_exercise_member_allocation,
    stop_exercise_member_allocation,
)
from components.pbm_core import clean
from components.supplement_member_allocation import (
    list_active_supplement_sources,
    list_member_supplement_allocations,
    save_supplement_member_allocation,
    stop_supplement_member_allocation,
)


def _actor_id() -> str:
    return st.session_state.get("user_id") or st.session_state.get("oidc_email") or "admin"


def _member_label(row: Dict) -> str:
    return f"{row.get('name') or 'Member'} — {row.get('email') or row.get('id')}"


def _to_date(value: object, fallback: dt.date) -> dt.date:
    try:
        text = clean(value)[:10]
        return dt.date.fromisoformat(text) if text else fallback
    except Exception:
        return fallback


def _clear(prefix: str) -> None:
    for key in list(st.session_state.keys()):
        if str(key).startswith(prefix):
            st.session_state.pop(key, None)


def _exercise_label(row: Dict) -> str:
    detail = clean(row.get("duration_or_reps") or row.get("category"))
    return f"{row.get('title') or 'Exercise'}{' · ' + detail if detail else ''}"


def _duration_or_reps(row: Dict) -> str:
    snapshot = row.get("source_snapshot") if isinstance(row.get("source_snapshot"), dict) else {}
    return clean(row.get("duration_or_reps") or snapshot.get("duration_or_reps"))


def _supplement_id(row: Dict) -> str:
    return clean(row.get("source_id") or row.get("id"))


def _supplement_label(row: Dict) -> str:
    detail = " · ".join(
        value for value in (clean(row.get("dosage")), clean(row.get("frequency"))) if value
    )
    return f"{row.get('supplement_name') or row.get('title') or 'Supplement'}{' · ' + detail if detail else ''}"


def _render_exercise(member_id: str) -> None:
    sources = list_active_exercise_sources()
    source_options = {_exercise_label(row): row for row in sources}
    st.markdown(
        "<div class='mpb-allocation-card'><b>Add Exercise Allocation</b>"
        "<span>Select, adjust and save. Existing allocations remain listed below for Edit or Stop.</span></div>",
        unsafe_allow_html=True,
    )
    if not source_options:
        st.info("No active Exercise repository items are available.")
    else:
        label = st.selectbox("Exercise", list(source_options), key=f"mpb_ex_source_{member_id}")
        source = source_options[label]
        with st.expander("More details", expanded=False):
            for name, field in (
                ("Category", "category"),
                ("Difficulty", "difficulty"),
                ("Duration / Reps", "duration_or_reps"),
                ("Equipment", "equipment"),
                ("Benefits", "benefits"),
            ):
                if clean(source.get(field)):
                    st.markdown(f"**{name}:** {clean(source.get(field))}")
        detail_cols = st.columns([0.42, 0.29, 0.29], gap="small")
        duration_or_reps = detail_cols[0].text_input(
            "Reps/Duration",
            value=_duration_or_reps(source) or "As advised",
            key=f"mpb_ex_duration_{member_id}",
        )
        start = detail_cols[1].date_input("Start Date", dt.date.today(), key=f"mpb_ex_start_{member_id}")
        end = detail_cols[2].date_input(
            "End Date", dt.date.today() + dt.timedelta(days=6), key=f"mpb_ex_end_{member_id}"
        )
        instructions = st.text_area(
            "Member Instructions",
            value=clean(source.get("instructions")),
            height=80,
            key=f"mpb_ex_instruction_{member_id}",
        )
        notes = st.text_input("Notes", key=f"mpb_ex_notes_{member_id}")
        if st.button(
            "Save Exercise Allocation",
            type="primary",
            use_container_width=True,
            key=f"mpb_ex_save_{member_id}",
        ):
            try:
                saved = save_exercise_member_allocation(
                    member_id=member_id,
                    source_id=clean(source.get("source_id") or source.get("id")),
                    start_date=start,
                    end_date=end,
                    duration_or_reps=duration_or_reps,
                    instructions=instructions,
                    notes=notes,
                    status="active",
                    actor_id=_actor_id(),
                )
                _clear("mpb_ex_")
                st.session_state["mpb_allocation_flash"] = (
                    f"Exercise allocation saved with ID {saved.get('id')}."
                )
                st.rerun()
            except ValueError as exc:
                st.error(str(exc))

    rows = list_member_exercise_allocations(member_id, include_stopped=True)
    if not rows:
        st.info("No Exercise allocations exist for this member.")
        return
    st.dataframe(
        pd.DataFrame(
            [
                {
                    "Exercise": row.get("exercise_name"),
                    "Reps/Duration": _duration_or_reps(row) or "As advised",
                    "Start": row.get("start_date"),
                    "End": row.get("end_date"),
                    "Status": row.get("status"),
                    "Allocation ID": row.get("id"),
                }
                for row in rows
            ]
        ),
        use_container_width=True,
        hide_index=True,
    )
    choices = {
        f"{row.get('exercise_name')} · {row.get('status')} · {row.get('id')}": row
        for row in rows
    }
    selected = choices[
        st.selectbox(
            "Select Exercise Allocation to Edit",
            list(choices),
            key=f"mpb_ex_existing_{member_id}",
        )
    ]
    allocation_id = clean(selected.get("id"))
    stopped = clean(selected.get("status")).lower() != "active"
    with st.expander("Edit selected Exercise allocation", expanded=False):
        detail_cols = st.columns([0.42, 0.29, 0.29], gap="small")
        edit_duration_or_reps = detail_cols[0].text_input(
            "Reps/Duration",
            value=_duration_or_reps(selected) or "As advised",
            disabled=stopped,
            key=f"mpb_ex_edit_duration_{allocation_id}",
        )
        edit_start = detail_cols[1].date_input(
            "Start Date",
            _to_date(selected.get("start_date"), dt.date.today()),
            disabled=stopped,
            key=f"mpb_ex_edit_start_{allocation_id}",
        )
        edit_end = detail_cols[2].date_input(
            "End Date",
            _to_date(selected.get("end_date"), dt.date.today()),
            disabled=stopped,
            key=f"mpb_ex_edit_end_{allocation_id}",
        )
        edit_instruction = st.text_area(
            "Member Instructions",
            value=clean(selected.get("instructions")),
            height=80,
            disabled=stopped,
            key=f"mpb_ex_edit_instruction_{allocation_id}",
        )
        edit_notes = st.text_input(
            "Notes",
            value=clean(selected.get("notes")),
            disabled=stopped,
            key=f"mpb_ex_edit_notes_{allocation_id}",
        )
        save_col, stop_col = st.columns(2, gap="small")
        if save_col.button(
            "Save Changes",
            type="primary",
            use_container_width=True,
            disabled=stopped,
            key=f"mpb_ex_update_{allocation_id}",
        ):
            try:
                save_exercise_member_allocation(
                    member_id=member_id,
                    source_id=clean(selected.get("source_id")),
                    start_date=edit_start,
                    end_date=edit_end,
                    duration_or_reps=edit_duration_or_reps,
                    instructions=edit_instruction,
                    notes=edit_notes,
                    status="active",
                    actor_id=_actor_id(),
                    allocation_id=allocation_id,
                )
                st.session_state["mpb_allocation_flash"] = "Exercise allocation updated."
                st.rerun()
            except ValueError as exc:
                st.error(str(exc))
        if stop_col.button(
            "Stop Allocation",
            use_container_width=True,
            disabled=stopped,
            key=f"mpb_ex_stop_{allocation_id}",
        ):
            try:
                stop_exercise_member_allocation(
                    member_id=member_id,
                    allocation_id=allocation_id,
                    actor_id=_actor_id(),
                    stop_date=dt.date.today(),
                    stop_reason=edit_notes,
                )
                st.session_state["mpb_allocation_flash"] = (
                    "Exercise allocation stopped; history retained."
                )
                st.rerun()
            except ValueError as exc:
                st.error(str(exc))


def _render_supplement(member_id: str) -> None:
    sources = list_active_supplement_sources()
    source_options = {_supplement_label(row): row for row in sources}
    source_by_id = {_supplement_id(row): row for row in sources}
    st.markdown(
        "<div class='mpb-allocation-card'><b>Add Supplement Allocation</b>"
        "<span>Select, adjust and save. Existing allocations remain listed below for Edit or Stop.</span></div>",
        unsafe_allow_html=True,
    )
    if not source_options:
        st.info("No active Supplement repository items are available.")
    else:
        label = st.selectbox(
            "Supplement", list(source_options), key=f"mpb_su_source_{member_id}"
        )
        source = source_options[label]
        fields = st.columns(3, gap="small")
        dosage = fields[0].text_input(
            "Dosage", value=clean(source.get("dosage")), key=f"mpb_su_dosage_{member_id}"
        )
        frequency = fields[1].text_input(
            "Frequency",
            value=clean(source.get("frequency")),
            key=f"mpb_su_frequency_{member_id}",
        )
        timing = fields[2].text_input(
            "Timing", value=clean(source.get("timing")), key=f"mpb_su_timing_{member_id}"
        )
        instructions = st.text_area(
            "Member Instructions",
            value=clean(source.get("instructions")),
            height=80,
            key=f"mpb_su_instruction_{member_id}",
        )
        dates = st.columns([0.4, 0.25, 0.35], gap="small")
        start = dates[0].date_input("Start Date", dt.date.today(), key=f"mpb_su_start_{member_id}")
        no_end = dates[1].checkbox("No End Date", True, key=f"mpb_su_no_end_{member_id}")
        end = dates[2].date_input(
            "End Date",
            dt.date.today() + dt.timedelta(days=30),
            disabled=no_end,
            key=f"mpb_su_end_{member_id}",
        )
        if st.button(
            "Save Supplement Allocation",
            type="primary",
            use_container_width=True,
            key=f"mpb_su_save_{member_id}",
        ):
            try:
                saved = save_supplement_member_allocation(
                    member_id=member_id,
                    source_id=_supplement_id(source),
                    dosage=dosage,
                    frequency=frequency,
                    timing=timing,
                    instructions=instructions,
                    start_date=start,
                    end_date="" if no_end else end,
                    actor_id=_actor_id(),
                )
                _clear("mpb_su_")
                st.session_state["mpb_allocation_flash"] = (
                    f"Supplement allocation saved with ID {saved.get('id')}."
                )
                st.rerun()
            except ValueError as exc:
                st.error(str(exc))

    rows = list_member_supplement_allocations(member_id, include_stopped=True)
    if not rows:
        st.info("No Supplement allocations exist for this member.")
        return
    st.dataframe(
        pd.DataFrame(
            [
                {
                    "Supplement": row.get("supplement_name"),
                    "Dosage": row.get("dosage"),
                    "Frequency": row.get("frequency"),
                    "Timing": row.get("timing"),
                    "Start": row.get("start_date"),
                    "End": row.get("end_date"),
                    "Status": row.get("status"),
                    "Allocation ID": row.get("id"),
                }
                for row in rows
            ]
        ),
        use_container_width=True,
        hide_index=True,
    )
    choices = {
        f"{row.get('supplement_name')} · {row.get('status')} · {row.get('id')}": row
        for row in rows
    }
    selected = choices[
        st.selectbox(
            "Select Supplement Allocation to Edit",
            list(choices),
            key=f"mpb_su_existing_{member_id}",
        )
    ]
    allocation_id = clean(selected.get("id"))
    stopped = clean(selected.get("status")).lower() == "stopped"
    with st.expander("Edit selected Supplement allocation", expanded=False):
        source_id = clean(selected.get("source_id"))
        if source_id:
            source = source_by_id.get(source_id)
            st.text_input(
                "Repository Source",
                value=_supplement_label(source) if source else f"Source ID {source_id}",
                disabled=True,
                key=f"mpb_su_fixed_source_{allocation_id}",
            )
        elif source_options and not stopped:
            map_label = st.selectbox(
                "Map Repository Source",
                list(source_options),
                key=f"mpb_su_map_{allocation_id}",
            )
            source_id = _supplement_id(source_options[map_label])
        else:
            st.warning("This historical allocation has no canonical source mapping.")

        fields = st.columns(3, gap="small")
        edit_dosage = fields[0].text_input(
            "Dosage",
            value=clean(selected.get("dosage")),
            disabled=stopped,
            key=f"mpb_su_edit_dosage_{allocation_id}",
        )
        edit_frequency = fields[1].text_input(
            "Frequency",
            value=clean(selected.get("frequency")),
            disabled=stopped,
            key=f"mpb_su_edit_frequency_{allocation_id}",
        )
        edit_timing = fields[2].text_input(
            "Timing",
            value=clean(selected.get("timing")),
            disabled=stopped,
            key=f"mpb_su_edit_timing_{allocation_id}",
        )
        edit_instruction = st.text_area(
            "Member Instructions",
            value=clean(selected.get("instructions")),
            height=80,
            disabled=stopped,
            key=f"mpb_su_edit_instruction_{allocation_id}",
        )
        dates = st.columns([0.4, 0.25, 0.35], gap="small")
        edit_start = dates[0].date_input(
            "Start Date",
            _to_date(selected.get("start_date"), dt.date.today()),
            disabled=stopped,
            key=f"mpb_su_edit_start_{allocation_id}",
        )
        no_end = dates[1].checkbox(
            "No End Date",
            not bool(selected.get("end_date")),
            disabled=stopped,
            key=f"mpb_su_edit_no_end_{allocation_id}",
        )
        edit_end = dates[2].date_input(
            "End Date",
            _to_date(selected.get("end_date"), dt.date.today() + dt.timedelta(days=30)),
            disabled=stopped or no_end,
            key=f"mpb_su_edit_end_{allocation_id}",
        )
        save_col, stop_col = st.columns(2, gap="small")
        if save_col.button(
            "Save Changes",
            type="primary",
            use_container_width=True,
            disabled=stopped or not source_id,
            key=f"mpb_su_update_{allocation_id}",
        ):
            try:
                save_supplement_member_allocation(
                    member_id=member_id,
                    source_id=source_id,
                    dosage=edit_dosage,
                    frequency=edit_frequency,
                    timing=edit_timing,
                    instructions=edit_instruction,
                    start_date=edit_start,
                    end_date="" if no_end else edit_end,
                    actor_id=_actor_id(),
                    allocation_id=allocation_id,
                )
                st.session_state["mpb_allocation_flash"] = (
                    "Supplement allocation updated."
                )
                st.rerun()
            except ValueError as exc:
                st.error(str(exc))
        if stop_col.button(
            "Stop Allocation",
            use_container_width=True,
            disabled=stopped,
            key=f"mpb_su_stop_{allocation_id}",
        ):
            try:
                stop_supplement_member_allocation(
                    member_id=member_id,
                    allocation_id=allocation_id,
                    stop_date=dt.date.today(),
                    actor_id=_actor_id(),
                )
                st.session_state["mpb_allocation_flash"] = (
                    "Supplement allocation stopped; history retained."
                )
                st.rerun()
            except ValueError as exc:
                st.error(str(exc))


def render_member_plan_allocations() -> None:
    st.markdown(
        "<div class='hm-title'>Exercise & Supplement</div>"
        "<div class='hm-sub'>Select the member once, then add or edit independent Exercise and Supplement allocations without leaving the Member Plan Builder.</div>",
        unsafe_allow_html=True,
    )
    members: List[Dict] = list_members()
    if not members:
        st.warning("No active members are available.")
        return
    options = {_member_label(row): row for row in members}
    labels = list(options)
    assigned_id = clean((st.session_state.get("pbm_profile") or {}).get("assigned_member_id"))
    default_label = next(
        (label for label in labels if clean(options[label].get("id")) == assigned_id),
        labels[0],
    )
    if st.session_state.get("mpb_allocation_member") not in labels:
        st.session_state["mpb_allocation_member"] = default_label
    selected_label = st.selectbox("Member", labels, key="mpb_allocation_member")
    member_id = clean(options[selected_label].get("id"))

    flash = st.session_state.pop("mpb_allocation_flash", "")
    if flash:
        st.success(flash)

    allocation_type = st.radio(
        "Allocation Type",
        ["Exercise", "Supplement"],
        horizontal=True,
        key="mpb_allocation_type",
        label_visibility="collapsed",
    )
    if allocation_type == "Exercise":
        _render_exercise(member_id)
    else:
        _render_supplement(member_id)
