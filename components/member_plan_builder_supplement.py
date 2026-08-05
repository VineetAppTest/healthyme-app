from __future__ import annotations

import datetime as dt
import re
from typing import Dict

import pandas as pd
import streamlit as st

from components.member_plan_builder_allocation_common import (
    allocation_choice_map,
    render_allocation_member_selector,
)
from components.pbm_core import clean
from components.supplement_member_allocation import (
    list_active_supplement_sources,
    list_member_supplement_allocations,
    save_supplement_member_allocation,
    stop_supplement_member_allocation,
)


TIMING_OPTIONS = [
    "Early Morning",
    "Morning",
    "Mid-morning",
    "Midday",
    "Afternoon",
    "Evening",
    "Night",
    "Before Bed",
    "With Food",
    "Empty Stomach",
    "After Meals",
]
FREQUENCY_OPTIONS = [
    "Once",
    "Twice",
    "Thrice",
    "Four times",
    "Five times",
    "Six times",
    "Seven times",
    "Eight times",
    "Nine times",
    "Ten times",
]
FREQUENCY_COUNTS = {
    "Once": 1,
    "Twice": 2,
    "Thrice": 3,
    "Four times": 4,
    "Five times": 5,
    "Six times": 6,
    "Seven times": 7,
    "Eight times": 8,
    "Nine times": 9,
    "Ten times": 10,
}


def _options_with_current(options: list[str], current: object) -> list[str]:
    value = clean(current)
    return options + [value] if value and value not in options else list(options)


def _timing_values(value: object) -> list[str]:
    if isinstance(value, (list, tuple, set)):
        raw_values = list(value)
    else:
        raw_values = re.split(r"[,;|]", clean(value))
    return list(dict.fromkeys(clean(item) for item in raw_values if clean(item)))


def _timing_options_with_current(value: object) -> list[str]:
    current = _timing_values(value)
    return list(dict.fromkeys([*TIMING_OPTIONS, *current]))


def _frequency_count(value: object) -> int:
    text = clean(value)
    if text in FREQUENCY_COUNTS:
        return FREQUENCY_COUNTS[text]
    if text.lower() in {"daily", "once daily", "one time"}:
        return 1
    match = re.search(r"\d+", text)
    return int(match.group(0)) if match else 0


def _frequency_timing_error(frequency: object, timings: list[str]) -> str:
    expected = _frequency_count(frequency)
    if expected <= 0:
        return "Choose a supported Frequency before selecting Timing."
    if len(timings) != expected:
        return (
            f"Select exactly {expected} Timing option(s) for {clean(frequency)}. "
            f"Currently selected: {len(timings)}."
        )
    return ""


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


def _source_id(row: Dict) -> str:
    return clean(row.get("source_id") or row.get("id"))


def _supplement_label(row: Dict) -> str:
    title = clean(row.get("supplement_name") or row.get("title")) or "Supplement"
    details = " · ".join(
        value for value in (clean(row.get("dosage")), clean(row.get("frequency"))) if value
    )
    return f"{title}{' · ' + details if details else ''}"


def _render_add_supplement(member_id: str) -> None:
    st.markdown("<div class='mpb-section-label'>Allocate Supplement</div>", unsafe_allow_html=True)
    sources = list_active_supplement_sources()
    source_options = {_supplement_label(row): row for row in sources}
    if not source_options:
        st.info("No active Supplement repository items are available.")
        return

    with st.container(border=True):
        selected_label = st.selectbox(
            "Supplement",
            list(source_options),
            key=f"mpb_su_add_source_{member_id}",
        )
        source = source_options[selected_label]
        fields = st.columns(3, gap="small")
        dosage = fields[0].text_input(
            "Dosage",
            value=clean(source.get("dosage")),
            key=f"mpb_su_add_dosage_{member_id}",
        )
        frequency_options = _options_with_current(
            FREQUENCY_OPTIONS, source.get("frequency")
        )
        current_frequency = clean(source.get("frequency")) or FREQUENCY_OPTIONS[0]
        frequency = fields[1].selectbox(
            "Frequency",
            frequency_options,
            index=frequency_options.index(current_frequency),
            key=f"mpb_su_add_frequency_{member_id}",
        )
        timing_options = _timing_options_with_current(source.get("timing"))
        current_timings = _timing_values(source.get("timing"))
        if not current_timings:
            current_timings = TIMING_OPTIONS[: _frequency_count(frequency)]
        timing = fields[2].multiselect(
            "Timing",
            timing_options,
            default=current_timings,
            key=f"mpb_su_add_timing_{member_id}",
            help="Select one timing for each daily dose.",
        )
        timing_error = _frequency_timing_error(frequency, timing)
        if timing_error:
            st.warning(timing_error)
        instructions = st.text_area(
            "Member Instructions",
            value=clean(source.get("instructions")),
            height=72,
            key=f"mpb_su_add_instruction_{member_id}",
        )
        date_cols = st.columns([0.4, 0.22, 0.38], gap="small")
        start = date_cols[0].date_input(
            "Start Date",
            dt.date.today(),
            key=f"mpb_su_add_start_{member_id}",
        )
        no_end = date_cols[1].checkbox(
            "No End Date",
            True,
            key=f"mpb_su_add_no_end_{member_id}",
        )
        end = date_cols[2].date_input(
            "End Date",
            dt.date.today() + dt.timedelta(days=30),
            disabled=no_end,
            key=f"mpb_su_add_end_{member_id}",
        )
        if st.button(
            "Save Supplement",
            type="primary",
            use_container_width=True,
            disabled=bool(timing_error),
            key=f"mpb_su_add_save_{member_id}",
        ):
            try:
                save_supplement_member_allocation(
                    member_id=member_id,
                    source_id=_source_id(source),
                    dosage=dosage,
                    frequency=frequency,
                    timing=", ".join(timing),
                    instructions=instructions,
                    start_date=start,
                    end_date="" if no_end else end,
                    actor_id=_actor_id(),
                )
                _clear_prefix("mpb_su_add_")
                st.session_state["mpb_supplement_flash"] = "Supplement allocation saved."
                st.rerun()
            except Exception as exc:
                st.error(str(exc))


def _render_edit_supplement(member_id: str) -> None:
    st.markdown("<div class='mpb-section-label'>Edit Supplement</div>", unsafe_allow_html=True)
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
        name_fields=("supplement_name", "title"),
    )
    selected_label = st.selectbox(
        "Select Supplement Allocation to Edit",
        list(choices),
        key=f"mpb_su_edit_choice_{member_id}",
    )
    selected = choices[selected_label]
    allocation_id = clean(selected.get("id"))
    stopped = clean(selected.get("status")).lower() == "stopped"

    sources = list_active_supplement_sources()
    source_options = {_supplement_label(row): row for row in sources}
    source_by_id = {_source_id(row): row for row in sources}
    source_id = clean(selected.get("source_id"))

    with st.container(border=True):
        if source_id:
            source = source_by_id.get(source_id)
            st.text_input(
                "Repository Source",
                value=_supplement_label(source) if source else "Saved repository source",
                disabled=True,
                key=f"mpb_su_edit_fixed_source_{allocation_id}",
            )
        elif source_options and not stopped:
            map_label = st.selectbox(
                "Map Repository Source",
                list(source_options),
                key=f"mpb_su_edit_map_{allocation_id}",
            )
            source_id = _source_id(source_options[map_label])
        else:
            st.warning("This historical allocation has no active repository mapping.")

        fields = st.columns(3, gap="small")
        dosage = fields[0].text_input(
            "Dosage",
            value=clean(selected.get("dosage")),
            disabled=stopped,
            key=f"mpb_su_edit_dosage_{allocation_id}",
        )
        edit_frequency_options = _options_with_current(
            FREQUENCY_OPTIONS, selected.get("frequency")
        )
        current_edit_frequency = clean(selected.get("frequency")) or FREQUENCY_OPTIONS[0]
        frequency = fields[1].selectbox(
            "Frequency",
            edit_frequency_options,
            index=edit_frequency_options.index(current_edit_frequency),
            disabled=stopped,
            key=f"mpb_su_edit_frequency_{allocation_id}",
        )
        edit_timing_options = _timing_options_with_current(selected.get("timing"))
        current_edit_timings = _timing_values(selected.get("timing"))
        if not current_edit_timings:
            current_edit_timings = TIMING_OPTIONS[: _frequency_count(frequency)]
        timing = fields[2].multiselect(
            "Timing",
            edit_timing_options,
            default=current_edit_timings,
            disabled=stopped,
            key=f"mpb_su_edit_timing_{allocation_id}",
            help="Select one timing for each daily dose.",
        )
        timing_error = _frequency_timing_error(frequency, timing)
        if timing_error and not stopped:
            st.warning(timing_error)
        instructions = st.text_area(
            "Member Instructions",
            value=clean(selected.get("instructions")),
            height=72,
            disabled=stopped,
            key=f"mpb_su_edit_instruction_{allocation_id}",
        )
        date_cols = st.columns([0.4, 0.22, 0.38], gap="small")
        start = date_cols[0].date_input(
            "Start Date",
            _to_date(selected.get("start_date"), dt.date.today()),
            disabled=stopped,
            key=f"mpb_su_edit_start_{allocation_id}",
        )
        no_end = date_cols[1].checkbox(
            "No End Date",
            not bool(selected.get("end_date")),
            disabled=stopped,
            key=f"mpb_su_edit_no_end_{allocation_id}",
        )
        end = date_cols[2].date_input(
            "End Date",
            _to_date(selected.get("end_date"), dt.date.today() + dt.timedelta(days=30)),
            disabled=stopped or no_end,
            key=f"mpb_su_edit_end_{allocation_id}",
        )
        actions = st.columns(2, gap="small")
        if actions[0].button(
            "Save Changes",
            type="primary",
            use_container_width=True,
            disabled=stopped or not source_id or bool(timing_error),
            key=f"mpb_su_edit_save_{allocation_id}",
        ):
            try:
                save_supplement_member_allocation(
                    member_id=member_id,
                    source_id=source_id,
                    dosage=dosage,
                    frequency=frequency,
                    timing=", ".join(timing),
                    instructions=instructions,
                    start_date=start,
                    end_date="" if no_end else end,
                    actor_id=_actor_id(),
                    allocation_id=allocation_id,
                )
                st.session_state["mpb_supplement_flash"] = "Supplement allocation updated."
                st.rerun()
            except Exception as exc:
                st.error(str(exc))
        if actions[1].button(
            "Stop Supplement",
            use_container_width=True,
            disabled=stopped,
            key=f"mpb_su_edit_stop_{allocation_id}",
        ):
            try:
                stop_supplement_member_allocation(
                    member_id=member_id,
                    allocation_id=allocation_id,
                    stop_date=dt.date.today(),
                    actor_id=_actor_id(),
                )
                st.session_state["mpb_supplement_flash"] = "Supplement allocation stopped; history retained."
                st.rerun()
            except Exception as exc:
                st.error(str(exc))


def render_member_plan_supplement() -> None:
    st.markdown(
        "<div class='hm-title'>Supplement</div>"
        "<div class='hm-sub'>Select the member, allocate one repository supplement, then edit or stop existing allocations below.</div>",
        unsafe_allow_html=True,
    )
    member_id, _member = render_allocation_member_selector("mpb_supplement_member")
    if not member_id:
        return
    flash = st.session_state.pop("mpb_supplement_flash", "")
    if flash:
        st.success(flash)
    _render_add_supplement(member_id)
    _render_edit_supplement(member_id)
