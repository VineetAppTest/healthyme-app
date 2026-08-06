from __future__ import annotations

from collections import Counter
import datetime as dt
from typing import Any, Dict, Iterable, List, Tuple

import streamlit as st

from components.db import list_members
from components.pbm_core import as_dict, clean
from components.profile_publish_control import load_active_profiles


def member_label(row: Dict, plan: Dict | None = None) -> str:
    base = f"{row.get('name') or 'Member'} — {row.get('email') or row.get('id')}"
    plan_name = clean((plan or {}).get("profile_name"))
    return f"{base} · {plan_name}" if plan_name else f"{base} · No active Meal Plan"


def render_allocation_member_selector(key: str) -> Tuple[str, str]:
    members: List[Dict] = list_members()
    if not members:
        st.warning("No active members are available.")
        return "", ""

    try:
        plans_ok, active_plans, plan_message = load_active_profiles()
    except Exception as exc:
        plans_ok, active_plans, plan_message = (
            False,
            [],
            f"Meal Profile labels could not be loaded: {exc}",
        )
    plan_by_member = {
        clean(row.get("assigned_member_id")): row
        for row in active_plans
        if clean(row.get("assigned_member_id"))
    } if plans_ok else {}
    if not plans_ok:
        st.caption(
            f"{plan_message} All active members remain visible for allocation."
        )

    options = {
        member_label(row, plan_by_member.get(clean(row.get("id")))): row
        for row in members
    }
    labels = list(options)
    assigned_id = clean((st.session_state.get("pbm_profile") or {}).get("assigned_member_id"))
    default_label = next(
        (label for label in labels if clean(options[label].get("id")) == assigned_id),
        labels[0],
    )
    if st.session_state.get(key) not in labels:
        st.session_state[key] = default_label
    selected_label = st.selectbox(
        "Member",
        labels,
        key=key,
        help=(
            "All active members are visible for Exercise and Supplement allocation. "
            "The active Meal Plan name is shown when one is available."
        ),
    )
    return clean(options[selected_label].get("id")), selected_label


def allocation_choice_map(
    rows: Iterable[Dict],
    *,
    name_fields: Tuple[str, ...],
    detail_fields: Tuple[str, ...] = (),
    include_status: bool = True,
    separator: str = " · ",
    date_format: str = "",
) -> Dict[str, Dict]:
    prepared = []
    for row in rows or []:
        name = next((clean(row.get(field)) for field in name_fields if clean(row.get(field))), "Item")
        start = _format_date(row.get("start_date"), date_format) or "No start"
        end = _format_date(row.get("end_date"), date_format) or "Open"
        status = clean(row.get("status")).title() or "Unknown"
        if not detail_fields and include_status and separator == " · ":
            base = f"{name} · {start} → {end} · {status}"
        else:
            details = [
                value
                for value in (_row_value(row, field) for field in detail_fields)
                if value
            ]
            parts = [name, *details, start, end]
            if include_status:
                parts.append(status)
            base = separator.join(parts)
        prepared.append((base, row))

    counts = Counter(base for base, _row in prepared)
    output: Dict[str, Dict] = {}
    for base, row in prepared:
        label = base
        if counts[base] > 1:
            suffix = clean(row.get("id"))[-8:] or "duplicate"
            label = f"{base} · {suffix}"
        output[label] = row
    return output


def _row_value(row: Dict[str, Any], field: str) -> str:
    direct = clean(row.get(field))
    if direct:
        return direct
    snapshot = as_dict(row.get("source_snapshot"))
    return clean(snapshot.get(field))


def _format_date(value: object, date_format: str) -> str:
    text = clean(value)
    if not text:
        return ""
    if not date_format:
        return text
    try:
        return dt.date.fromisoformat(text[:10]).strftime(date_format)
    except Exception:
        return text


def source_summary(title: str, details: Iterable[str]) -> None:
    detail_text = " · ".join(clean(value) for value in details if clean(value))
    st.markdown(
        "<div class='mpb-source-summary'>"
        f"<b>{title}</b>"
        + (f"<span>{detail_text}</span>" if detail_text else "")
        + "</div>",
        unsafe_allow_html=True,
    )
