from __future__ import annotations

from collections import Counter
from typing import Dict, Iterable, List, Tuple

import streamlit as st

from components.db import list_members
from components.pbm_core import clean


def member_label(row: Dict) -> str:
    return f"{row.get('name') or 'Member'} — {row.get('email') or row.get('id')}"


def render_allocation_member_selector(key: str) -> Tuple[str, str]:
    members: List[Dict] = list_members()
    if not members:
        st.warning("No active members are available.")
        return "", ""

    options = {member_label(row): row for row in members}
    labels = list(options)
    assigned_id = clean((st.session_state.get("pbm_profile") or {}).get("assigned_member_id"))
    default_label = next(
        (label for label in labels if clean(options[label].get("id")) == assigned_id),
        labels[0],
    )
    if st.session_state.get(key) not in labels:
        st.session_state[key] = default_label
    selected_label = st.selectbox("Member", labels, key=key)
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
