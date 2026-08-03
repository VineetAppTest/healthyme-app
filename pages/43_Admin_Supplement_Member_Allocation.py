import datetime as dt

import pandas as pd
import streamlit as st

from components.db import list_members
from components.guards import require_admin
from components.supplement_member_allocation import (
    list_active_supplement_sources,
    list_member_supplement_allocations,
    save_supplement_member_allocation,
    stop_supplement_member_allocation,
)
from components.ui_common import (
    apply_luxe_theme,
    inject_global_styles,
    render_back_to_top,
    render_page_nav,
    topbar,
    utility_logout_bar,
)


st.set_page_config(
    page_title="Supplement Member Allocation",
    page_icon="💚",
    layout="wide",
    initial_sidebar_state="collapsed",
)
inject_global_styles()
apply_luxe_theme()
require_admin()
utility_logout_bar()

topbar(
    "Supplement Member Allocation",
    "Allocate active repository supplements and manage member-specific regimens.",
    "Member Planning",
)


def _actor_id() -> str:
    return (
        st.session_state.get("user_id")
        or st.session_state.get("oidc_email")
        or "admin"
    )


def _member_label(row: dict) -> str:
    return f"{row.get('name') or 'Member'} — {row.get('email') or row.get('id')}"


def _source_id(row: dict) -> str:
    return str(row.get("source_id") or row.get("id") or "")


def _source_label(row: dict) -> str:
    name = row.get("supplement_name") or row.get("title") or "Supplement"
    details = " · ".join(
        value
        for value in [
            str(row.get("dosage") or "").strip(),
            str(row.get("frequency") or "").strip(),
        ]
        if value
    )
    return f"{name}{' · ' + details if details else ''} · ID {_source_id(row)}"


def _to_date(value: object, fallback: dt.date) -> dt.date:
    try:
        text = str(value or "")[:10]
        return dt.date.fromisoformat(text) if text else fallback
    except Exception:
        return fallback


def _clear_add_form(member_id: str) -> None:
    for suffix in (
        "source",
        "dosage",
        "frequency",
        "timing",
        "instructions",
        "start",
        "end",
        "no_end",
    ):
        st.session_state.pop(f"phase_d_{suffix}_{member_id}", None)


def _mapping_label(value: object) -> str:
    labels = {
        "canonical": "Canonical source retained",
        "canonical_new": "Canonical source",
        "canonical_existing": "Canonical source retained",
        "mapped_by_legacy_id": "Legacy ID match — pending backfill",
        "mapped_by_exact_name": "Exact-name match — pending backfill",
        "backfilled_mapped_by_legacy_id": "Legacy ID mapping persisted",
        "backfilled_mapped_by_exact_name": "Exact-name mapping persisted",
        "explicit_admin_mapping": "Admin mapping persisted",
        "unmapped_legacy": "Legacy row requires mapping",
        "ambiguous_legacy_id": "Ambiguous legacy ID",
        "ambiguous_exact_name": "Ambiguous exact name",
        "missing_canonical_source": "Canonical source is unavailable",
    }
    raw = str(value or "")
    return labels.get(raw, raw.replace("_", " ").title() or "Unmapped")


st.markdown(
    """
<style>
.hm-phase-d-note{border:1px solid #E3C98E;background:#FFFDF8;border-radius:14px;padding:.72rem .88rem;color:#475569;font-size:.84rem;font-weight:720;line-height:1.4;margin:.25rem 0 .9rem;}
.hm-phase-d-map{border:1px solid rgba(216,180,98,.55);background:#fff;border-radius:14px;padding:.65rem .78rem;margin:.3rem 0 .7rem;color:#475569;font-size:.82rem;font-weight:720;}
</style>
""",
    unsafe_allow_html=True,
)
st.markdown(
    """
<div class='hm-phase-d-note'>
<b>Boundary:</b> this workflow writes only <code>member_supplements</code>.
New allocations use active canonical Supplement repository IDs. Existing legacy
allocation IDs and stopped history remain unchanged.
</div>
""",
    unsafe_allow_html=True,
)

flash_message = st.session_state.pop("phase_d_flash", "")
if flash_message:
    st.success(flash_message)

members = list_members()
if not members:
    st.warning("No active members are available.")
    render_page_nav(
        "Supplement Member Allocation",
        back_page="pages/10_Admin_Dashboard.py",
        dashboard_page="pages/10_Admin_Dashboard.py",
        show_evaluation=False,
        show_dashboard=True,
        location="bottom",
    )
    render_back_to_top()
    st.stop()

member_options = {_member_label(member): member for member in members}
selected_member_label = st.selectbox(
    "Select member",
    list(member_options.keys()),
    key="phase_d_member",
)
member = member_options[selected_member_label]
member_id = str(member.get("id"))

sources = list_active_supplement_sources()
source_options = {_source_label(source): source for source in sources}
source_by_id = {_source_id(source): source for source in sources}
allocations = list_member_supplement_allocations(
    member_id,
    include_stopped=True,
)

tab_add, tab_manage = st.tabs(["Add Allocation", "Current Allocations"])

with tab_add:
    st.markdown("### Allocate a Supplement")
    if not source_options:
        st.info(
            "No active Supplement repository items are available. "
            "Activate or add a Supplement in the repository first."
        )
    else:
        selected_source_label = st.selectbox(
            "Supplement",
            list(source_options.keys()),
            key=f"phase_d_source_{member_id}",
        )
        selected_source = source_options[selected_source_label]
        dosage = st.text_input(
            "Dosage",
            value=str(selected_source.get("dosage") or ""),
            key=f"phase_d_dosage_{member_id}",
        )
        frequency = st.text_input(
            "Frequency",
            value=str(selected_source.get("frequency") or ""),
            key=f"phase_d_frequency_{member_id}",
        )
        timing = st.text_input(
            "Timing",
            value=str(selected_source.get("timing") or ""),
            key=f"phase_d_timing_{member_id}",
        )
        instructions = st.text_area(
            "Member instructions",
            value=str(selected_source.get("instructions") or ""),
            height=100,
            key=f"phase_d_instructions_{member_id}",
        )
        start_date = st.date_input(
            "Start date",
            value=dt.date.today(),
            key=f"phase_d_start_{member_id}",
        )
        no_end_date = st.checkbox(
            "No predefined end date",
            value=True,
            key=f"phase_d_no_end_{member_id}",
        )
        end_date = st.date_input(
            "End date",
            value=dt.date.today() + dt.timedelta(days=30),
            disabled=no_end_date,
            key=f"phase_d_end_{member_id}",
        )
        if st.button(
            "Save Supplement Allocation",
            type="primary",
            use_container_width=True,
            key=f"phase_d_save_{member_id}",
        ):
            try:
                saved = save_supplement_member_allocation(
                    member_id=member_id,
                    source_id=_source_id(selected_source),
                    dosage=dosage,
                    frequency=frequency,
                    timing=timing,
                    instructions=instructions,
                    start_date=start_date,
                    end_date="" if no_end_date else end_date,
                    actor_id=_actor_id(),
                )
                _clear_add_form(member_id)
                st.session_state["phase_d_flash"] = (
                    f"Supplement allocation saved with ID {saved.get('id')}."
                )
                st.rerun()
            except ValueError as exc:
                st.error(str(exc))

with tab_manage:
    st.markdown("### Current and Historical Allocations")
    if not allocations:
        st.info("No Supplement allocations exist for this member.")
    else:
        summary_rows = [
            {
                "Allocation ID": row.get("id"),
                "Supplement": row.get("supplement_name"),
                "Source ID": row.get("source_id") or "Unmapped",
                "Mapping": _mapping_label(row.get("source_mapping_status")),
                "Start": row.get("start_date"),
                "End": row.get("end_date"),
                "Status": row.get("status"),
            }
            for row in allocations
        ]
        st.dataframe(
            pd.DataFrame(summary_rows),
            use_container_width=True,
            hide_index=True,
        )

        allocation_options = {
            f"{row.get('supplement_name')} · {row.get('status')} · {row.get('id')}": row
            for row in allocations
        }
        selected_allocation_label = st.selectbox(
            "Select allocation",
            list(allocation_options.keys()),
            key=f"phase_d_existing_{member_id}",
        )
        selected = allocation_options[selected_allocation_label]
        current_status = str(selected.get("status") or "Active")
        is_stopped = current_status == "Stopped"
        mapping_status = str(selected.get("source_mapping_status") or "")
        selected_source_id = str(selected.get("source_id") or "")

        st.markdown(
            f"<div class='hm-phase-d-map'><b>Source mapping:</b> "
            f"{_mapping_label(mapping_status)}</div>",
            unsafe_allow_html=True,
        )

        if selected_source_id:
            source_display = source_by_id.get(selected_source_id)
            st.text_input(
                "Canonical Supplement source",
                value=(
                    _source_label(source_display)
                    if source_display
                    else f"Source ID {selected_source_id}"
                ),
                disabled=True,
                key=f"phase_d_fixed_source_{selected.get('id')}",
            )
            edit_source_id = selected_source_id
        else:
            if source_options and not is_stopped:
                mapping_label = st.selectbox(
                    "Map to canonical Supplement source",
                    list(source_options.keys()),
                    key=f"phase_d_map_source_{selected.get('id')}",
                )
                edit_source_id = _source_id(source_options[mapping_label])
                st.caption(
                    "Saving will attach this source to the existing allocation ID; "
                    "the allocation itself will not be replaced."
                )
            else:
                edit_source_id = ""
                st.warning(
                    "This historical allocation has no canonical source mapping."
                )

        edit_dosage = st.text_input(
            "Dosage",
            value=str(selected.get("dosage") or ""),
            disabled=is_stopped,
            key=f"phase_d_edit_dosage_{selected.get('id')}",
        )
        edit_frequency = st.text_input(
            "Frequency",
            value=str(selected.get("frequency") or ""),
            disabled=is_stopped,
            key=f"phase_d_edit_frequency_{selected.get('id')}",
        )
        edit_timing = st.text_input(
            "Timing",
            value=str(selected.get("timing") or ""),
            disabled=is_stopped,
            key=f"phase_d_edit_timing_{selected.get('id')}",
        )
        edit_instructions = st.text_area(
            "Member instructions",
            value=str(selected.get("instructions") or ""),
            height=100,
            disabled=is_stopped,
            key=f"phase_d_edit_instructions_{selected.get('id')}",
        )
        today = dt.date.today()
        no_start_date = st.checkbox(
            "Start date is not recorded",
            value=not bool(selected.get("start_date")),
            disabled=is_stopped,
            key=f"phase_d_no_start_{selected.get('id')}",
        )
        edit_start = st.date_input(
            "Start date",
            value=_to_date(selected.get("start_date"), today),
            disabled=is_stopped or no_start_date,
            key=f"phase_d_edit_start_{selected.get('id')}",
        )
        no_end_date = st.checkbox(
            "No predefined end date",
            value=not bool(selected.get("end_date")),
            disabled=is_stopped,
            key=f"phase_d_edit_no_end_{selected.get('id')}",
        )
        edit_end = st.date_input(
            "End date",
            value=_to_date(
                selected.get("end_date"),
                _to_date(selected.get("start_date"), today)
                + dt.timedelta(days=30),
            ),
            disabled=is_stopped or no_end_date,
            key=f"phase_d_edit_end_{selected.get('id')}",
        )

        update_col, stop_col = st.columns(2, gap="large")
        with update_col:
            if st.button(
                "Update Allocation",
                type="primary",
                use_container_width=True,
                disabled=is_stopped or not edit_source_id,
                key=f"phase_d_update_{selected.get('id')}",
            ):
                try:
                    save_supplement_member_allocation(
                        member_id=member_id,
                        source_id=edit_source_id,
                        dosage=edit_dosage,
                        frequency=edit_frequency,
                        timing=edit_timing,
                        instructions=edit_instructions,
                        start_date="" if no_start_date else edit_start,
                        end_date="" if no_end_date else edit_end,
                        actor_id=_actor_id(),
                        allocation_id=str(selected.get("id")),
                    )
                    st.session_state["phase_d_flash"] = (
                        "Supplement allocation updated."
                    )
                    st.rerun()
                except ValueError as exc:
                    st.error(str(exc))
        with stop_col:
            if st.button(
                "Stop Allocation",
                use_container_width=True,
                disabled=is_stopped,
                key=f"phase_d_stop_{selected.get('id')}",
            ):
                try:
                    stop_supplement_member_allocation(
                        member_id=member_id,
                        allocation_id=str(selected.get("id")),
                        stop_date=dt.date.today(),
                        actor_id=_actor_id(),
                    )
                    st.session_state["phase_d_flash"] = (
                        "Supplement allocation stopped; history retained."
                    )
                    st.rerun()
                except ValueError as exc:
                    st.error(str(exc))

        with st.expander("View immutable source snapshot", expanded=False):
            st.json(selected.get("source_snapshot") or {})

render_page_nav(
    "Supplement Member Allocation",
    back_page="pages/10_Admin_Dashboard.py",
    dashboard_page="pages/10_Admin_Dashboard.py",
    show_evaluation=False,
    show_dashboard=True,
    location="bottom",
)
render_back_to_top()
