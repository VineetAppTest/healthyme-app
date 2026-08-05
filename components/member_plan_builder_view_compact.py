from __future__ import annotations

import html
import io
from collections import defaultdict
from datetime import date, datetime, timedelta
from typing import Any, Dict, List

import pandas as pd
import streamlit as st

from components.current_member_plan import build_current_member_plan
from components.member_plan_builder_export import load_member_plan_events, meal_review_rows
from components.pbm_core import clean, safe
from components.recommendation_profile_viewer import (
    _meal_cells,
    _render_view_profiles_css,
    load_profile_detail_readonly,
    load_profile_inventory,
)


@st.cache_data(ttl=60, show_spinner=False)
def _cached_inventory():
    return load_profile_inventory()


@st.cache_data(ttl=60, show_spinner=False)
def _cached_detail(profile_id: str):
    return load_profile_detail_readonly(profile_id)


@st.cache_data(ttl=30, show_spinner=False)
def _cached_current_plan(member_id: str):
    return build_current_member_plan(member_id)


def _profile_label(row: Dict[str, Any]) -> str:
    status = clean(row.get("status")).title() or "Unknown"
    start = clean(row.get("start_date")) or "No start date"
    return f"{clean(row.get('profile_name')) or 'Untitled'} · {status} · {start}"


def _member_label(row: Dict[str, Any]) -> str:
    return clean(row.get("assigned_member_label")) or clean(row.get("assigned_member_id")) or "Unallocated"


def _allocation_rows(model: Dict[str, Any], domain: str) -> List[Dict[str, Any]]:
    output: List[Dict[str, Any]] = []
    partitions = dict(model.get(domain) or {})
    for state in ("current", "upcoming", "expired_pending_stop", "stopped"):
        for row in list(partitions.get(state) or []):
            snapshot = dict(row.get("source_snapshot") or {})
            common = {
                "Start": clean(row.get("start_date")),
                "End": clean(row.get("end_date")) or "Open",
                "Instructions": clean(row.get("instructions") or snapshot.get("instructions")),
                "Status": state.replace("_", " ").title(),
                "Allocation ID": clean(row.get("id")),
                "Source ID": clean(row.get("source_id") or row.get("exercise_id") or row.get("supplement_id")),
            }
            if domain == "exercise":
                output.append(
                    {
                        "Exercise": clean(row.get("exercise_name") or row.get("title") or snapshot.get("title")),
                        "Duration / Reps": clean(snapshot.get("duration_or_reps")),
                        **common,
                    }
                )
            else:
                output.append(
                    {
                        "Supplement": clean(row.get("supplement_name") or row.get("title") or snapshot.get("supplement_name") or snapshot.get("title")),
                        "Dosage": clean(row.get("dosage") or snapshot.get("dosage")),
                        "Frequency": clean(row.get("frequency") or snapshot.get("frequency")),
                        "Timing": clean(row.get("timing") or snapshot.get("timing")),
                        **common,
                    }
                )
    return output


def _plain_table_cell(value: object) -> str:
    return html.unescape(str(value or "").replace("<br>", "\n"))


def _parse_date(value: object) -> date | None:
    raw = clean(value)
    if not raw:
        return None
    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%d-%m-%Y", "%d/%m/%Y"):
        try:
            return datetime.strptime(raw[:10], fmt).date()
        except ValueError:
            pass
    return None


def _html_cell(value: object) -> str:
    text = _plain_table_cell(value)
    return "<br>".join(html.escape(line) for line in text.splitlines())


def _render_weekly_table(
    start_date: str,
    section_type: str,
    headers: tuple[str, str, str, str],
    day_cells,
) -> None:
    rows = []
    for day_number in range(1, 8):
        cells = tuple(day_cells(day_number))
        prefix = ""
        if day_number == 1:
            prefix = (
                f"<td rowspan='7' class='mpb-weekly-fixed'>{_html_cell(start_date)}</td>"
                f"<td rowspan='7' class='mpb-weekly-fixed'>{html.escape(section_type)}</td>"
            )
        rows.append(
            "<tr>"
            f"{prefix}<td class='mpb-weekly-day'>Day {day_number}</td>"
            + "".join(f"<td>{_html_cell(value)}</td>" for value in cells)
            + "</tr>"
        )
    st.markdown(
        """
<style id="mpb-weekly-table-v1">
.mpb-weekly-wrap{overflow:auto;border:1px solid #D8A84E;border-radius:12px;background:#fff;margin:.34rem 0 .78rem}.mpb-weekly-table{width:100%;border-collapse:collapse;font-size:.75rem;line-height:1.28}.mpb-weekly-table th{background:#FFF4DE;color:#064E3B;font-weight:900;text-align:center;padding:.45rem .42rem;border:1px solid #D8A84E}.mpb-weekly-table td{color:#334155;font-weight:650;padding:.45rem .42rem;border:1px solid #E3C98E;vertical-align:top}.mpb-weekly-table .mpb-weekly-fixed,.mpb-weekly-table .mpb-weekly-day{text-align:center;vertical-align:middle;color:#064E3B;font-weight:900;white-space:nowrap}.mpb-weekly-title{color:#064E3B;font-size:.92rem;font-weight:950;margin:.72rem 0 .28rem}
</style>
""",
        unsafe_allow_html=True,
    )
    header_html = "".join(f"<th>{html.escape(value)}</th>" for value in headers)
    st.markdown(
        f"<div class='mpb-weekly-title'>{html.escape(section_type)}</div>"
        "<div class='mpb-weekly-wrap'><table class='mpb-weekly-table'>"
        "<thead><tr><th>Start Date</th><th>Type</th><th>Day</th>"
        f"{header_html}</tr></thead><tbody>{''.join(rows)}</tbody></table></div>",
        unsafe_allow_html=True,
    )


def _model_rows(model: Dict[str, Any], domain: str) -> List[Dict[str, Any]]:
    partitions = dict(model.get(domain) or {})
    output: List[Dict[str, Any]] = []
    for state in ("current", "upcoming"):
        output.extend(dict(row or {}) for row in partitions.get(state) or [])
    return output


def _row_applies_to_date(row: Dict[str, Any], target: date | None) -> bool:
    if target is None:
        return True
    start = _parse_date(row.get("start_date"))
    end = _parse_date(row.get("end_date"))
    if start and target < start:
        return False
    if end and target > end:
        return False
    return True


def _allocation_day_cells(
    model: Dict[str, Any],
    domain: str,
    plan_start: str,
    day_number: int,
) -> tuple[str, str, str, str]:
    parsed_start = _parse_date(plan_start)
    target = parsed_start + timedelta(days=day_number - 1) if parsed_start else None
    rows = [row for row in _model_rows(model, domain) if _row_applies_to_date(row, target)]
    timing: List[str] = []
    names: List[str] = []
    values: List[str] = []
    remarks: List[str] = []
    for row in rows:
        snapshot = dict(row.get("source_snapshot") or {})
        timing.append(clean(row.get("timing") or snapshot.get("timing")))
        if domain == "exercise":
            names.append(clean(row.get("exercise_name") or row.get("title") or snapshot.get("title")))
            values.append(clean(snapshot.get("duration_or_reps")))
        else:
            names.append(clean(row.get("supplement_name") or row.get("title") or snapshot.get("supplement_name") or snapshot.get("title")))
            dose = clean(row.get("dosage") or snapshot.get("dosage"))
            frequency = clean(row.get("frequency") or snapshot.get("frequency"))
            values.append(" · ".join(value for value in (dose, frequency) if value))
        remarks.append(clean(row.get("instructions") or snapshot.get("instructions")))
    joined = lambda items: "\n".join(value for value in items if value)
    return joined(timing), joined(names), joined(values), joined(remarks)


def _legacy_rows(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return [
        {
            "Type": clean(row.get("item_type")).title(),
            "Day": int(row.get("day_number") or 0),
            "Slot / Timing": clean(row.get("slot_name") or row.get("scheduled_time")),
            "Item": clean(row.get("reference_label")),
            "Dose / Portion": clean(row.get("dosage_frequency") or row.get("portion")),
            "Instruction": clean(row.get("instruction")),
            "Legacy Row ID": clean(row.get("id")),
            "Source ID": clean(row.get("source_id") or row.get("reference_id")),
        }
        for row in items or []
        if clean(row.get("item_type")).lower() in {"exercise", "supplement"}
    ]


def _build_workbook(
    profile: Dict[str, Any],
    items: List[Dict[str, Any]],
    model: Dict[str, Any] | None,
    events: List[Dict[str, Any]],
) -> bytes:
    summary = [
        {"Field": "Profile ID", "Value": clean(profile.get("id"))},
        {"Field": "Plan Name", "Value": clean(profile.get("profile_name"))},
        {"Field": "Status", "Value": clean(profile.get("status")).title()},
        {"Field": "Member ID", "Value": clean(profile.get("assigned_member_id"))},
        {"Field": "Member", "Value": clean(profile.get("assigned_member_label"))},
        {"Field": "Plan Start Date", "Value": clean(profile.get("start_date"))},
        {"Field": "Region / Food Culture", "Value": clean(profile.get("region"))},
        {"Field": "Diet Type", "Value": clean(profile.get("diet_type"))},
        {"Field": "Health Concerns", "Value": ", ".join(profile.get("health_concerns") or [])},
        {"Field": "Nutritionist Note", "Value": clean(profile.get("profile_note"))},
        {"Field": "Change Note", "Value": clean(profile.get("change_note"))},
        {"Field": "Clone Source Profile ID", "Value": clean(profile.get("clone_source_profile_id"))},
    ]
    exercises = _allocation_rows(model or {}, "exercise") if model else []
    supplements = _allocation_rows(model or {}, "supplement") if model else []
    legacy = _legacy_rows(items)

    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        pd.DataFrame(summary).to_excel(writer, sheet_name="Plan Summary", index=False)
        pd.DataFrame(meal_review_rows(items)).to_excel(writer, sheet_name="Seven Day Meals", index=False)
        pd.DataFrame(exercises).to_excel(writer, sheet_name="Exercise Allocations", index=False)
        pd.DataFrame(supplements).to_excel(writer, sheet_name="Supplement Allocations", index=False)
        pd.DataFrame(events).to_excel(writer, sheet_name="Change Log", index=False)
        if legacy:
            pd.DataFrame(legacy).to_excel(writer, sheet_name="Legacy Profile Rows", index=False)
        for sheet in writer.book.worksheets:
            sheet.freeze_panes = "A2"
            for column_cells in sheet.columns:
                values = [str(cell.value or "") for cell in column_cells]
                width = min(55, max(12, max(len(value) for value in values) + 2))
                sheet.column_dimensions[column_cells[0].column_letter].width = width
    buffer.seek(0)
    return buffer.getvalue()


def render_view_member_plan_compact() -> None:
    _render_view_profiles_css()
    st.markdown(
        "<div class='hm-title'>View Member Plan</div>"
        "<div class='hm-sub'>Review a saved Meal Profile. The active profile is consolidated with the member's independent Exercise and Supplement allocations.</div>",
        unsafe_allow_html=True,
    )

    ok, profiles, message = _cached_inventory()
    if not ok:
        st.error(message)
        return
    profiles = [row for row in profiles if clean(row.get("assigned_member_id"))]
    if not profiles:
        st.info("No member plans are available.")
        return

    grouped: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    member_labels: Dict[str, str] = {}
    for row in profiles:
        member_id = clean(row.get("assigned_member_id"))
        grouped[member_id].append(row)
        member_labels[member_id] = _member_label(row)

    member_ids = list(grouped)
    loaded_member_id = clean((st.session_state.get("pbm_profile") or {}).get("assigned_member_id"))
    default_member = loaded_member_id if loaded_member_id in member_ids else member_ids[0]
    if st.session_state.get("mpb_view_member_id") not in member_ids:
        st.session_state["mpb_view_member_id"] = default_member

    controls = st.columns([0.38, 0.62], gap="small")
    member_id = controls[0].selectbox(
        "Member",
        member_ids,
        format_func=lambda value: member_labels[value],
        key="mpb_view_member_id",
    )

    member_profiles = grouped[member_id]
    active_profiles = [row for row in member_profiles if clean(row.get("status")).lower() == "active"]
    if len(active_profiles) > 1:
        st.error("Integrity check failed: this member has more than one active Meal Profile.")
        return
    active_id = clean(active_profiles[0].get("id")) if active_profiles else ""
    profile_ids = [clean(row.get("id")) for row in member_profiles if clean(row.get("id"))]
    profile_key = f"mpb_view_profile_{member_id}"
    if st.session_state.get(profile_key) not in profile_ids:
        st.session_state[profile_key] = active_id or profile_ids[0]
    profile_map = {clean(row.get("id")): row for row in member_profiles}
    selected_id = controls[1].selectbox(
        "View Existing Profile",
        profile_ids,
        format_func=lambda value: _profile_label(profile_map[value]),
        key=profile_key,
    )

    detail_ok, profile, items, detail_message = _cached_detail(selected_id)
    if not detail_ok:
        st.error(detail_message)
        return

    st.markdown(
        "<div class='mpb-plan-summary-card'>"
        f"<b>{safe(profile.get('profile_name') or 'Untitled')}</b>"
        f"<span>{safe(profile.get('assigned_member_label'))} · {safe(clean(profile.get('status')).title())} · Start {safe(profile.get('start_date'))}</span>"
        "</div>",
        unsafe_allow_html=True,
    )

    is_active = clean(profile.get("status")).lower() == "active"
    model: Dict[str, Any] | None = None
    if is_active:
        try:
            model = _cached_current_plan(member_id)
        except Exception as exc:
            st.error(f"Could not build the consolidated active plan: {exc}")
            return
        model_profile_id = clean((model.get("meal_profile") or {}).get("id"))
        if model_profile_id != selected_id:
            st.error("Integrity check failed: the selected active Meal Profile does not match the member's consolidated current plan.")
            return
    else:
        st.caption("This is a Draft or historical Meal Profile. Current independent allocations are shown only with the member's Active profile.")

    plan_start = clean(profile.get("start_date"))
    _render_weekly_table(
        plan_start,
        "Meal",
        ("Timing", "Meal", "Liquid", "Remarks"),
        lambda day_number: _meal_cells(items, day_number),
    )

    if model:
        _render_weekly_table(
            plan_start,
            "Exercise",
            ("Timing", "Activity", "Duration/Sets", "Remarks"),
            lambda day_number: _allocation_day_cells(
                model, "exercise", plan_start, day_number
            ),
        )
        _render_weekly_table(
            plan_start,
            "Supplement",
            ("Timing", "Supplement", "Dosage", "Remarks"),
            lambda day_number: _allocation_day_cells(
                model, "supplement", plan_start, day_number
            ),
        )
        ignored = dict(model.get("ignored_profile_rows") or {})
        ignored_count = int(ignored.get("exercise", 0)) + int(ignored.get("supplement", 0))
        if ignored_count:
            st.caption(f"{ignored_count} retained legacy non-meal Profile Builder row(s) are excluded from the current plan and retained only for audit history.")

    events_ok, events, _event_message = load_member_plan_events(member_id)
    workbook = _build_workbook(profile, items, model, events if events_ok else [])
    filename = f"{clean(profile.get('profile_name')) or 'member_plan'}_details.xlsx".replace(" ", "_")
    st.download_button(
        "Download Selected Member Plan",
        data=workbook,
        file_name=filename,
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True,
        key=f"mpb_view_download_{selected_id}",
    )
