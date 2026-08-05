from __future__ import annotations

from collections import Counter
from typing import Dict, Iterable, List, Tuple

import streamlit as st

from components.db import list_members
from components.pbm_core import clean
from components.profile_publish_control import load_active_profiles


def member_label(row: Dict, plan: Dict | None = None) -> str:
    base = f"{row.get('name') or 'Member'} — {row.get('email') or row.get('id')}"
    plan_name = clean((plan or {}).get("profile_name"))
    return f"{base} · {plan_name}" if plan_name else base


def render_allocation_member_selector(key: str) -> Tuple[str, str]:
    members: List[Dict] = list_members()
    if not members:
        st.warning("No active members are available.")
        return "", ""

    plans_ok, active_plans, plan_message = load_active_profiles()
    if not plans_ok:
        st.warning(plan_message)
        return "", ""
    plan_by_member = {
        clean(row.get("assigned_member_id")): row
        for row in active_plans
        if clean(row.get("assigned_member_id"))
    }
    members = [row for row in members if clean(row.get("id")) in plan_by_member]
    if not members:
        st.warning(
            "No member has an active Meal Plan. Publish a Meal Profile from Meals before "
            "allocating Exercise or Supplement."
        )
        return "", ""

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
        help="Exercise and Supplement allocations attach through the member's active Meal Plan.",
    )
    return clean(options[selected_label].get("id")), selected_label


def allocation_choice_map(
    rows: Iterable[Dict],
    *,
    name_fields: Tuple[str, ...],
) -> Dict[str, Dict]:
    prepared = []
    for row in rows or []:
        name = next((clean(row.get(field)) for field in name_fields if clean(row.get(field))), "Item")
        start = clean(row.get("start_date")) or "No start"
        end = clean(row.get("end_date")) or "Open"
        status = clean(row.get("status")).title() or "Unknown"
        base = f"{name} · {start} → {end} · {status}"
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


def source_summary(title: str, details: Iterable[str]) -> None:
    detail_text = " · ".join(clean(value) for value in details if clean(value))
    st.markdown(
        "<div class='mpb-source-summary'>"
        f"<b>{title}</b>"
        + (f"<span>{detail_text}</span>" if detail_text else "")
        + "</div>",
        unsafe_allow_html=True,
    )
