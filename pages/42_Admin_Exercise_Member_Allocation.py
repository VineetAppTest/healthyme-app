import datetime as dt

import pandas as pd
import streamlit as st

from components.db import list_members
from components.exercise_member_allocation import (
    list_active_exercise_sources,
    list_member_exercise_allocations,
    save_exercise_member_allocation,
    stop_exercise_member_allocation,
)
from components.guards import require_admin
from components.ui_common import (
    apply_luxe_theme,
    inject_global_styles,
    render_back_to_top,
    render_page_nav,
    topbar,
    utility_logout_bar,
)


st.set_page_config(
    page_title="Exercise Member Allocation",
    page_icon="💚",
    layout="wide",
    initial_sidebar_state="collapsed",
)
inject_global_styles()
apply_luxe_theme()
require_admin()
utility_logout_bar()

topbar(
    "Exercise Member Allocation",
    "Allocate active repository exercises to a member and manage the allocation lifecycle.",
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


def _source_label(row: dict) -> str:
    meta = str(row.get("duration_or_reps") or row.get("category") or "").strip()
    return (
        f"{row.get('title') or 'Exercise'}"
        f"{' · ' + meta if meta else ''}"
        f" · ID {row.get('source_id') or row.get('id')}"
    )


def _to_date(value: object, fallback: dt.date) -> dt.date:
    try:
        text = str(value or "")[:10]
        return dt.date.fromisoformat(text) if text else fallback
    except Exception:
        return fallback


st.markdown(
    """
<style>
.hm-phase-c-note{border:1px solid #E3C98E;background:#FFFDF8;border-radius:14px;padding:.72rem .88rem;color:#475569;font-size:.84rem;font-weight:720;line-height:1.4;margin:.25rem 0 .9rem;}
.hm-phase-c-card{border:1px solid rgba(216,180,98,.55);background:#fff;border-radius:16px;padding:.75rem .85rem;margin:.35rem 0 .65rem;box-shadow:0 7px 16px rgba(15,23,42,.04);}
</style>
""",
    unsafe_allow_html=True,
)
st.markdown(
    """
<div class='hm-phase-c-note'>
<b>Boundary:</b> this workflow writes only <code>member_exercise_allocations</code>.
It does not publish recommendation shares, edit Supplements, or change repository definitions.
Historical and stopped allocations remain readable.
</div>
""",
    unsafe_allow_html=True,
)

members = list_members()
if not members:
    st.warning("No active members are available.")
    render_page_nav(
        "Exercise Member Allocation",
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
    key="phase_c_member",
)
member = member_options[selected_member_label]
member_id = str(member.get("id"))

sources = list_active_exercise_sources()
source_options = {_source_label(source): source for source in sources}
allocations = list_member_exercise_allocations(member_id, include_stopped=True)

tab_add, tab_manage = st.tabs(["Add Allocation", "Current Allocations"])

with tab_add:
    st.markdown("### Allocate an Exercise")
    if not source_options:
        st.info(
            "No active Exercise repository items are available. "
            "Activate or add an Exercise in the Exercise repository first."
        )
    else:
        selected_source_label = st.selectbox(
            "Exercise",
            list(source_options.keys()),
            key=f"phase_c_source_{member_id}",
        )
        selected_source = source_options[selected_source_label]
        start_date = st.date_input(
            "Start date",
            value=dt.date.today(),
            key=f"phase_c_start_{member_id}",
        )
        end_date = st.date_input(
            "End date",
            value=dt.date.today() + dt.timedelta(days=6),
            key=f"phase_c_end_{member_id}",
        )
        instructions = st.text_area(
            "Member instructions",
            value=str(selected_source.get("instructions") or ""),
            height=110,
            key=f"phase_c_instructions_{member_id}",
        )
        notes = st.text_area(
            "Admin / member-specific notes",
            height=90,
            key=f"phase_c_notes_{member_id}",
        )
        if st.button(
            "Save Exercise Allocation",
            type="primary",
            use_container_width=True,
            key=f"phase_c_save_{member_id}",
        ):
            try:
                saved = save_exercise_member_allocation(
                    member_id=member_id,
                    source_id=str(
                        selected_source.get("source_id")
                        or selected_source.get("id")
                    ),
                    start_date=start_date,
                    end_date=end_date,
                    instructions=instructions,
                    notes=notes,
                    status="active",
                    actor_id=_actor_id(),
                )
                st.success(
                    f"Exercise allocation saved with ID {saved.get('id')}."
                )
                st.rerun()
            except ValueError as exc:
                st.error(str(exc))

with tab_manage:
    st.markdown("### Current and Historical Allocations")
    if not allocations:
        st.info("No Exercise allocations exist for this member.")
    else:
        summary_rows = [
            {
                "Allocation ID": row.get("id"),
                "Exercise": row.get("exercise_name"),
                "Source ID": row.get("source_id"),
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
            f"{row.get('exercise_name')} · {row.get('status')} · {row.get('id')}": row
            for row in allocations
        }
        selected_allocation_label = st.selectbox(
            "Select allocation to edit",
            list(allocation_options.keys()),
            key=f"phase_c_existing_{member_id}",
        )
        selected = allocation_options[selected_allocation_label]
        today = dt.date.today()
        edit_start = st.date_input(
            "Start date",
            value=_to_date(selected.get("start_date"), today),
            key=f"phase_c_edit_start_{selected.get('id')}",
        )
        edit_end = st.date_input(
            "End date",
            value=_to_date(
                selected.get("end_date"),
                _to_date(selected.get("start_date"), today),
            ),
            key=f"phase_c_edit_end_{selected.get('id')}",
        )
        edit_instructions = st.text_area(
            "Member instructions",
            value=str(selected.get("instructions") or ""),
            height=110,
            key=f"phase_c_edit_instructions_{selected.get('id')}",
        )
        edit_notes = st.text_area(
            "Notes",
            value=str(selected.get("notes") or ""),
            height=90,
            key=f"phase_c_edit_notes_{selected.get('id')}",
        )
        status_options = ["active", "stopped"]
        current_status = (
            "stopped"
            if str(selected.get("status")).lower() != "active"
            else "active"
        )
        edit_status = st.selectbox(
            "Status",
            status_options,
            index=status_options.index(current_status),
            key=f"phase_c_edit_status_{selected.get('id')}",
        )

        save_col, stop_col = st.columns(2, gap="large")
        with save_col:
            if st.button(
                "Update Allocation",
                type="primary",
                use_container_width=True,
                key=f"phase_c_update_{selected.get('id')}",
            ):
                try:
                    save_exercise_member_allocation(
                        member_id=member_id,
                        source_id=str(selected.get("source_id")),
                        start_date=edit_start,
                        end_date=edit_end,
                        instructions=edit_instructions,
                        notes=edit_notes,
                        status=edit_status,
                        actor_id=_actor_id(),
                        allocation_id=str(selected.get("id")),
                    )
                    st.success("Exercise allocation updated.")
                    st.rerun()
                except ValueError as exc:
                    st.error(str(exc))
        with stop_col:
            if st.button(
                "Stop Allocation",
                use_container_width=True,
                disabled=current_status == "stopped",
                key=f"phase_c_stop_{selected.get('id')}",
            ):
                try:
                    stop_exercise_member_allocation(
                        member_id=member_id,
                        allocation_id=str(selected.get("id")),
                        actor_id=_actor_id(),
                        stop_date=dt.date.today(),
                        stop_reason=edit_notes,
                    )
                    st.success("Exercise allocation stopped; history retained.")
                    st.rerun()
                except ValueError as exc:
                    st.error(str(exc))

        with st.expander("View immutable source snapshot", expanded=False):
            st.json(selected.get("source_snapshot") or {})

render_page_nav(
    "Exercise Member Allocation",
    back_page="pages/10_Admin_Dashboard.py",
    dashboard_page="pages/10_Admin_Dashboard.py",
    show_evaluation=False,
    show_dashboard=True,
    location="bottom",
)
render_back_to_top()
