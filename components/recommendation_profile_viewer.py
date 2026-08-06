from __future__ import annotations

import datetime as dt
import html
import json
import re
from typing import Any, Dict, List, Optional, Tuple

import streamlit as st

from components.recommendation_profile_store import (
    ITEM_TABLE,
    PROFILE_TABLE,
    _client,
    _rows,
    check_profile_builder_store,
)


PROFILE_SCOPE_OPTIONS = (
    "All Profiles",
    "All Editable Profiles",
    "All Allocated Profiles",
    "Member Profiles",
)
EDITABLE_PROFILE_STATUSES = {"draft", "active"}
PROFILE_STATUSES = ("draft", "active", "replaced", "archived")
STATUS_LABELS = {
    "draft": "Draft",
    "active": "Active",
    "replaced": "Removed from allocation",
    "archived": "Archived",
}
LIQUID_SOURCE_TOKENS = ("liquid", "beverage", "drink", "fluid")


def _clean(value: object, default: str = "") -> str:
    if value is None:
        return default
    return str(value).strip()


def _safe(value: object, default: str = "") -> str:
    text = _clean(value, default)
    return html.escape(text, quote=True)


def _date_value(value: object) -> Optional[dt.date]:
    if isinstance(value, dt.datetime):
        return value.date()
    if isinstance(value, dt.date):
        return value
    text = _clean(value)
    if not text:
        return None
    try:
        return dt.date.fromisoformat(text[:10])
    except Exception:
        return None


def _as_dict(value: object) -> Dict[str, Any]:
    if isinstance(value, dict):
        return dict(value)
    if isinstance(value, str) and value.strip():
        try:
            parsed = json.loads(value)
            return dict(parsed) if isinstance(parsed, dict) else {}
        except Exception:
            return {}
    return {}


def _source_snapshot(row: dict) -> Dict[str, Any]:
    snapshot = _as_dict(row.get("source_snapshot"))
    original = _as_dict(snapshot.get("source_original_snapshot"))
    return original or snapshot


def _source_value(row: dict, field: str) -> str:
    snapshot = _source_snapshot(row)
    return _clean(snapshot.get(field))


def _is_liquid_meal(row: dict) -> bool:
    explicit_type = " ".join(
        [
            _source_value(row, "meal_type"),
            _source_value(row, "category"),
            _source_value(row, "type"),
        ]
    ).lower()
    return any(token in explicit_type for token in LIQUID_SOURCE_TOKENS)


def _clear_selected_profile() -> None:
    st.session_state.pop("view_profiles_profile_id", None)


def load_profile_inventory(limit: int = 500) -> Tuple[bool, List[dict], str]:
    """Load every saved recommendation profile without changing any record."""
    status = check_profile_builder_store()
    if not status.get("ok"):
        return False, [], status.get("message", "Profile Builder tables are not ready.")
    try:
        result = (
            _client()
            .table(PROFILE_TABLE)
            .select(
                "id,profile_name,status,assigned_member_id,assigned_member_label,"
                "start_date,health_concerns,updated_at"
            )
            .order("updated_at", desc=True)
            .limit(limit)
            .execute()
        )
        return True, _rows(result), "Loaded all created recommendation profiles."
    except Exception as exc:
        return False, [], f"Could not load recommendation profiles: {exc}"


def load_profile_detail_readonly(
    profile_id: str,
) -> Tuple[bool, Dict[str, Any], List[dict], str]:
    """Read one profile and all saved recommendation rows."""
    clean_id = _clean(profile_id)
    if not clean_id:
        return False, {}, [], "Select an existing profile."
    try:
        client = _client()
        profile_result = (
            client.table(PROFILE_TABLE)
            .select("*")
            .eq("id", clean_id)
            .limit(1)
            .execute()
        )
        profiles = _rows(profile_result)
        if not profiles:
            return False, {}, [], "Selected profile was not found."
        item_result = (
            client.table(ITEM_TABLE)
            .select("*")
            .eq("profile_id", clean_id)
            .order("day_number")
            .order("item_type")
            .order("item_order")
            .execute()
        )
        return True, profiles[0], _rows(item_result), "Loaded selected profile."
    except Exception as exc:
        return False, {}, [], f"Could not load selected profile: {exc}"


def render_profile_lifecycle_guide() -> None:
    st.markdown(
        """
<style id="hm-profile-lifecycle-guide-v2">
.hm-profile-lifecycle{border:1px solid #E3C98E;background:linear-gradient(135deg,#FFFDF8,#FFF7E7);border-radius:17px;padding:.78rem .86rem;margin:.40rem 0 .86rem;box-shadow:0 8px 20px rgba(15,23,42,.045)}
.hm-profile-lifecycle-title{color:#064E3B;font-size:.92rem;font-weight:950;margin:0 0 .50rem}
.hm-profile-lifecycle-grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:.55rem}
.hm-profile-life-card{border:1px solid rgba(216,168,78,.55);background:#fff;border-radius:13px;padding:.58rem .62rem;color:#475569;font-size:.76rem;line-height:1.38;font-weight:680}
.hm-profile-life-card b{display:block;color:#064E3B;font-size:.82rem;font-weight:950;margin-bottom:.18rem}
.hm-profile-life-card strong{color:#7A4F00}
@media(max-width:900px){.hm-profile-lifecycle-grid{grid-template-columns:1fr 1fr}}
@media(max-width:560px){.hm-profile-lifecycle-grid{grid-template-columns:1fr}}
</style>
<div class="hm-profile-lifecycle">
  <div class="hm-profile-lifecycle-title">Recommendation Profile lifecycle</div>
  <div class="hm-profile-lifecycle-grid">
    <div class="hm-profile-life-card"><b>Preview</b>Reviews the profile currently loaded in the Builder. It may include unsaved on-screen edits. Preview does not save or change profile status.</div>
    <div class="hm-profile-life-card"><b>Publish</b>Admin/Super Admin activates a <strong>saved Draft</strong> that has a member and recommendation rows. The member's previous Active profile becomes Replaced.</div>
    <div class="hm-profile-life-card"><b>Active</b>Read-only check of the member's current live consumption contract. Existing Builder module saves to an Active Profile ID update that live profile in place.</div>
    <div class="hm-profile-life-card"><b>View Profiles</b>Profile Scope selects the population, Existing Profile selects one created profile, and the optional date range narrows profiles by Start Date.</div>
  </div>
</div>
""",
        unsafe_allow_html=True,
    )


def _scope_profiles(rows: List[dict], scope: str) -> List[dict]:
    if scope == "All Editable Profiles":
        return [
            row
            for row in rows
            if _clean(row.get("status"), "draft").lower() in EDITABLE_PROFILE_STATUSES
        ]
    if scope == "All Allocated Profiles":
        # Active represents the profile currently allocated/live for a member.
        return [
            row
            for row in rows
            if _clean(row.get("status")).lower() == "active"
        ]
    if scope == "Member Profiles":
        # Includes current and historical profiles linked to a member.
        return [row for row in rows if _clean(row.get("assigned_member_id"))]
    return list(rows)


def _date_filtered_profiles(
    rows: List[dict],
    date_from: Optional[dt.date],
    date_to: Optional[dt.date],
) -> List[dict]:
    output: List[dict] = []
    for row in rows:
        start_date = _date_value(row.get("start_date"))
        if date_from is not None and (start_date is None or start_date < date_from):
            continue
        if date_to is not None and (start_date is None or start_date > date_to):
            continue
        output.append(row)
    return output


def _profile_label(row: dict) -> str:
    status_raw = _clean(row.get("status"), "draft").lower()
    status = STATUS_LABELS.get(status_raw, status_raw.title() or "Unknown")
    member = _clean(row.get("assigned_member_label"), "Unallocated")
    start_date = _clean(row.get("start_date"), "No start date")
    return (
        f"{_clean(row.get('profile_name'), 'Untitled')} · {status} · "
        f"{member} · {start_date}"
    )


def _ordered_items(items: List[dict], item_type: str, day: int) -> List[dict]:
    rows = [
        row
        for row in items
        if _clean(row.get("item_type")).lower() == item_type
        and int(row.get("day_number") or 0) == day
    ]
    return sorted(rows, key=lambda row: int(row.get("item_order") or 1))


def _unique_lines(values: List[str]) -> str:
    output: List[str] = []
    for value in values:
        cleaned = _clean(value)
        if cleaned and cleaned not in output:
            output.append(cleaned)
    return "<br>".join(_safe(value) for value in output)


def _unique_join(values: List[str], separator: str = " + ") -> str:
    output: List[str] = []
    for value in values:
        cleaned = _clean(value)
        if cleaned and cleaned not in output:
            output.append(cleaned)
    return separator.join(_safe(value) for value in output)


def _item_and_quantity(row: dict) -> str:
    item = _clean(row.get("reference_label"))
    quantity = _clean(row.get("portion"))
    if item and quantity:
        return f"{item} - {quantity}"
    return item or quantity


def _supplement_dosage(row: dict) -> str:
    raw = _clean(row.get("dosage_frequency"))
    if not raw:
        return ""
    match = re.match(r"^Frequency:\s*\d+\s*;\s*Dosage:\s*(.*)$", raw)
    return _clean(match.group(1)) if match else raw


def _meal_cells(items: List[dict], day: int) -> Tuple[str, str, str, str]:
    rows = _ordered_items(items, "meal", day)
    timing = _unique_lines([_clean(row.get("slot_name")) for row in rows])
    meal = _unique_join(
        [_item_and_quantity(row) for row in rows if not _is_liquid_meal(row)]
    )
    liquid = _unique_join(
        [_item_and_quantity(row) for row in rows if _is_liquid_meal(row)]
    )
    remarks = _unique_lines([_clean(row.get("instruction")) for row in rows])
    return timing, meal, liquid, remarks


def _exercise_cells(items: List[dict], day: int) -> Tuple[str, str, str, str]:
    rows = _ordered_items(items, "exercise", day)
    timing = _unique_lines(
        [
            _clean(row.get("scheduled_time")) or _clean(row.get("slot_name"))
            for row in rows
        ]
    )
    activity = _unique_lines([_clean(row.get("reference_label")) for row in rows])
    duration = _unique_lines([_source_value(row, "duration_or_reps") for row in rows])
    remarks = _unique_lines([_clean(row.get("instruction")) for row in rows])
    return timing, activity, duration, remarks


def _supplement_cells(items: List[dict], day: int) -> Tuple[str, str, str, str]:
    rows = _ordered_items(items, "supplement", day)
    timing = _unique_lines(
        [
            _clean(row.get("scheduled_time")) or _clean(row.get("slot_name"))
            for row in rows
        ]
    )
    supplement = _unique_lines([_clean(row.get("reference_label")) for row in rows])
    dosage = _unique_lines([_supplement_dosage(row) for row in rows])
    remarks = _unique_lines([_clean(row.get("instruction")) for row in rows])
    return timing, supplement, dosage, remarks


def _render_profile_table(
    *,
    start_date: str,
    section_type: str,
    headers: Tuple[str, str, str, str],
    day_cells,
) -> None:
    table_headers = ("Start Date", "Type", "Day") + headers
    header_html = "".join(f"<th>{_safe(header)}</th>" for header in table_headers)
    body_rows: List[str] = []
    for day in range(1, 8):
        timing, first_value, second_value, remarks = day_cells(day)
        prefix = ""
        if day == 1:
            prefix = (
                f"<td rowspan='7' class='hm-vp-rowspan'>{_safe(start_date)}</td>"
                f"<td rowspan='7' class='hm-vp-rowspan'>{_safe(section_type)}</td>"
            )
        body_rows.append(
            "<tr>"
            f"{prefix}"
            f"<td class='hm-vp-day'>Day {day}</td>"
            f"<td>{timing}</td>"
            f"<td>{first_value}</td>"
            f"<td>{second_value}</td>"
            f"<td>{remarks}</td>"
            "</tr>"
        )
    st.markdown(
        f"""
<div class="hm-vp-table-wrap">
<table class="hm-vp-table">
<thead><tr>{header_html}</tr></thead>
<tbody>{''.join(body_rows)}</tbody>
</table>
</div>
""",
        unsafe_allow_html=True,
    )


def _render_view_profiles_css() -> None:
    st.markdown(
        """
<style id="hm-view-profiles-excel-ssot-v1">
.hm-vp-table-wrap{overflow-x:auto;margin:.58rem 0 1.18rem;border:1px solid #D8A84E;border-radius:14px;background:#fff}
.hm-vp-table{width:100%;border-collapse:collapse;table-layout:fixed;font-size:.79rem;line-height:1.38}
.hm-vp-table th{background:#FFF9EC;color:#064E3B;font-weight:950;text-align:center;padding:.52rem .46rem;border:1px solid #D8A84E;white-space:nowrap}
.hm-vp-table td{color:#334155;font-weight:680;padding:.50rem .48rem;border:1px solid #E3C98E;vertical-align:top;white-space:normal;overflow-wrap:anywhere}
.hm-vp-table .hm-vp-rowspan,.hm-vp-table .hm-vp-day{text-align:center;vertical-align:middle;color:#064E3B;font-weight:900}
.hm-vp-table th:nth-child(1),.hm-vp-table td:nth-child(1){width:11%}
.hm-vp-table th:nth-child(2),.hm-vp-table td:nth-child(2){width:11%}
.hm-vp-table th:nth-child(3),.hm-vp-table td:nth-child(3){width:8%}
.hm-vp-table th:nth-child(4),.hm-vp-table td:nth-child(4){width:17%}
.hm-vp-table th:nth-child(5),.hm-vp-table td:nth-child(5){width:18%}
.hm-vp-table th:nth-child(6),.hm-vp-table td:nth-child(6){width:17%}
.hm-vp-table th:nth-child(7),.hm-vp-table td:nth-child(7){width:18%}
@media(max-width:760px){.hm-vp-table{min-width:820px}}
</style>
""",
        unsafe_allow_html=True,
    )


def render_view_profiles() -> None:
    """Render the Excel-defined read-only profile review tab."""
    _render_view_profiles_css()

    ok, profiles, message = load_profile_inventory()
    if not ok:
        st.error(message)
        return

    filter_columns = st.columns([0.28, 0.38, 0.17, 0.17], gap="medium")
    scope = filter_columns[0].selectbox(
        "Profile Scope",
        list(PROFILE_SCOPE_OPTIONS),
        key="view_profiles_scope",
        on_change=_clear_selected_profile,
    )
    date_from = filter_columns[2].date_input(
        "Date - From",
        value=None,
        key="view_profiles_date_from",
        on_change=_clear_selected_profile,
    )
    date_to = filter_columns[3].date_input(
        "Date - To",
        value=None,
        key="view_profiles_date_to",
        on_change=_clear_selected_profile,
    )

    if date_from is not None and date_to is not None and date_from > date_to:
        filter_columns[1].selectbox(
            "View Existing Profile",
            [""],
            format_func=lambda _value: "-- Select profile --",
            key="view_profiles_profile_id",
            disabled=True,
        )
        st.error("Date - From cannot be later than Date - To.")
        return

    eligible = _scope_profiles(profiles, scope)
    eligible = _date_filtered_profiles(eligible, date_from, date_to)
    profile_by_id = {
        _clean(row.get("id")): row
        for row in eligible
        if _clean(row.get("id"))
    }
    profile_ids = [""] + list(profile_by_id.keys())
    selected_profile_id = filter_columns[1].selectbox(
        "View Existing Profile",
        profile_ids,
        format_func=lambda value: (
            "-- Select profile --"
            if not value
            else _profile_label(profile_by_id[value])
        ),
        key="view_profiles_profile_id",
    )

    if not selected_profile_id:
        if not eligible:
            st.info("No created profiles match the selected scope and optional date range.")
        return

    detail_ok, profile, items, detail_message = load_profile_detail_readonly(
        selected_profile_id
    )
    if not detail_ok:
        st.error(detail_message)
        return

    start_date = _clean(profile.get("start_date"))
    _render_profile_table(
        start_date=start_date,
        section_type="Meal",
        headers=("Timing", "Meal", "Liquid", "Remarks"),
        day_cells=lambda day: _meal_cells(items, day),
    )
    _render_profile_table(
        start_date=start_date,
        section_type="Exercise",
        headers=("Timing", "Activity", "Reps/Duration", "Remarks"),
        day_cells=lambda day: _exercise_cells(items, day),
    )
    _render_profile_table(
        start_date=start_date,
        section_type="Supplement",
        headers=("Timing", "Supplement", "Dosage", "Remarks"),
        day_cells=lambda day: _supplement_cells(items, day),
    )
