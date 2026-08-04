from __future__ import annotations

import datetime as dt
from typing import Dict

import pandas as pd
import streamlit as st

from components.exercise_member_allocation import (
    list_active_exercise_sources,
    list_member_exercise_allocations,
    save_exercise_member_allocation,
    stop_exercise_member_allocation,
)
from components.member_plan_builder_allocation_common import (
    allocation_choice_map,
    render_allocation_member_selector,
    source_summary,
)
from components.pbm_core import clean


def _actor_id() -> str:
    return st.session_state.get("user_id") or st.session_state.get("oidc_email") or "admin"


def _to_date(value: object, fallback: dt.date) -> dt.date:
    try:
        text = clean(value)[:10]
        return dt.date.fromisoformat(text) if text else fallback
    except Exception:
        return fallback


def _clear_prefix(prefix: str) -> None:
    for key in list(st.session_state.keys()):
        if str(key).startswith(prefix):
            st.session_state.pop(key, None)


def _exercise_label(row: Dict) -> str:
    detail = clean(row.get("duration_or_reps") or row.get("category"))
    return f"{clean(row.get('title')) or 'Exercise'}{' · ' + detail if detail else ''}"


def _render_source_details(source: Dict) -> None:
    source_summary(
        clean(source.get("title")) or "Exercise",
        (
            clean(source.get("duration_or_reps")),
            clean(source.get("difficulty")),
            clean(source.get("category")),
        ),
    )
    with st.expander("More details", expanded=False):
        details = (
            ("Category", source.get("category")),
            ("Difficulty", source.get("difficulty")),
            ("Duration / Reps", source.get("duration_or_reps")),
            ("Equipment", source.get("equipment")),
            ("Benefits", source.get("benefits")),
        )
        shown = False
        for label, value in details:
            if clean(value):
                shown = True
                st.markdown(f"**{label}:** {clean(value)}")
        if not shown:
            st.caption("No additional repository information is available.")


def _render_add_exercise(member_id: str) -> None:
    st.markdown("<div class='mpb-section-label'>Allocate Exercise</div>", unsafe_allow_html=True)
    sources = list_active_exercise_sources()
    source_options = {_exercise_label(row): row for row in sources}
    if not source_options:
        st.info("No active Exercise repository items are available.")
        return

    with st.container(border=True):
        selected_label = st.selectbox(
            "Exercise",
            list(source_options),
            key=f"mpb_ex_add_source_{member_id}",
        )
        source = source_options[selected_label]
        _render_source_details(source)

        date_cols = st.columns(2, gap="small")
        start = date_cols[0].date_input(
            "Start Date",
            dt.date.today(),
            key=f"mpb_ex_add_start_{member_id}",
        )
        end = date_cols[1].date_input(
            "End Date",
            dt.date.today() + dt.timedelta(days=6),
            key=f"mpb_ex_add_end_{member_id}",
        )
        note_cols = st.columns([0.68, 0.32], gap="small")
        instructions = note_cols[0].text_area(
            "Member Instructions",
            value=clean(source.get("instructions")),
            height=72,
            key=f"mpb_ex_add_instruction_{member_id}",
        )
        notes = note_cols[1].text_input(
            "Notes",
            key=f"mpb_ex_add_notes_{member_id}",
        )
        if st.button(
            "Save Exercise",
            type="primary",
            use_container_width=True,
            key=f"mpb_ex_add_save_{member_id}",
        ):
            try:
                save_exercise_member_allocation(
                    member_id=member_id,
                    source_id=clean(source.get("source_id") or source.get("id")),
                    start_date=start,
                    end_date=end,
                    instructions=instructions,
                    notes=notes,
                    status="active",
                    actor_id=_actor_id(),
                )
                _clear_prefix("mpb_ex_add_")
                st.session_state["mpb_exercise_flash"] = "Exercise allocation saved."
                st.rerun()
            except Exception as exc:
                st.error(str(exc))


def _render_edit_exercise(member_id: str) -> None:
    st.markdown("<div class='mpb-section-label'>Edit Exercise</div>", unsafe_allow_html=True)
    rows = list_member_exercise_allocations(member_id, include_stopped=True)
    if not rows:
        st.info("No Exercise allocations exist for this member.")
        return

    st.dataframe(
        pd.DataFrame(
            [
                {
                    "Exercise": row.get("exercise_name"),
                    "Start": row.get("start_date"),
                    "End": row.get("end_date") or "Open",
                    "Status": clean(row.get("status")).title(),
                }
                for row in rows
            ]
        ),
        use_container_width=True,
        hide_index=True,
    )

    choices = allocation_choice_map(
        rows,
        name_fields=("exercise_name", "title"),
    )
    selected_label = st.selectbox(
        "Select Exercise Allocation to Edit",
        list(choices),
        key=f"mpb_ex_edit_choice_{member_id}",
    )
    selected = choices[selected_label]
    allocation_id = clean(selected.get("id"))
    stopped = clean(selected.get("status")).lower() != "active"

    with st.container(border=True):
        source_summary(
            clean(selected.get("exercise_name")) or "Exercise",
            (
                clean(selected.get("start_date")),
                clean(selected.get("end_date")) or "Open",
                clean(selected.get("status")).title(),
            ),
        )
        date_cols = st.columns(2, gap="small")
        edit_start = date_cols[0].date_input(
            "Start Date",
            _to_date(selected.get("start_date"), dt.date.today()),
            disabled=stopped,
            key=f"mpb_ex_edit_start_{allocation_id}",
        )
        edit_end = date_cols[1].date_input(
            "End Date",
            _to_date(selected.get("end_date"), dt.date.today()),
            disabled=stopped,
            key=f"mpb_ex_edit_end_{allocation_id}",
        )
        note_cols = st.columns([0.68, 0.32], gap="small")
        edit_instruction = note_cols[0].text_area(
            "Member Instructions",
            value=clean(selected.get("instructions")),
            height=72,
            disabled=stopped,
            key=f"mpb_ex_edit_instruction_{allocation_id}",
        )
        edit_notes = note_cols[1].text_input(
            "Notes",
            value=clean(selected.get("notes")),
            disabled=stopped,
            key=f"mpb_ex_edit_notes_{allocation_id}",
        )
        action_cols = st.columns(2, gap="small")
        if action_cols[0].button(
            "Save Changes",
            type="primary",
            use_container_width=True,
            disabled=stopped,
            key=f"mpb_ex_edit_save_{allocation_id}",
        ):
            try:
                save_exercise_member_allocation(
                    member_id=member_id,
                    source_id=clean(selected.get("source_id")),
                    start_date=edit_start,
                    end_date=edit_end,
                    instructions=edit_instruction,
                    notes=edit_notes,
                    status="active",
                    actor_id=_actor_id(),
                    allocation_id=allocation_id,
                )
                st.session_state["mpb_exercise_flash"] = "Exercise allocation updated."
                st.rerun()
            except Exception as exc:
                st.error(str(exc))
        if action_cols[1].button(
            "Stop Exercise",
            use_container_width=True,
            disabled=stopped,
            key=f"mpb_ex_edit_stop_{allocation_id}",
        ):
            try:
                stop_exercise_member_allocation(
                    member_id=member_id,
                    allocation_id=allocation_id,
                    actor_id=_actor_id(),
                    stop_date=dt.date.today(),
                    stop_reason=edit_notes,
                )
                st.session_state["mpb_exercise_flash"] = "Exercise allocation stopped; history retained."
                st.rerun()
            except Exception as exc:
                st.error(str(exc))


def render_member_plan_exercise() -> None:
    st.markdown(
        "<div class='hm-title'>Exercise</div>"
        "<div class='hm-sub'>Select the member, allocate one repository exercise, then edit or stop existing allocations below.</div>",
        unsafe_allow_html=True,
    )
    member_id, _member = render_allocation_member_selector("mpb_exercise_member")
    if not member_id:
        return
    flash = st.session_state.pop("mpb_exercise_flash", "")
    if flash:
        st.success(flash)
    _render_add_exercise(member_id)
    _render_edit_exercise(member_id)
