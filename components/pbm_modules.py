from __future__ import annotations

from typing import Dict, List, Tuple

import streamlit as st

from components.pbm_core import (
    MEAL_SLOTS,
    SELECT_MEMBER,
    SELECT_PROFILE,
    clean,
    day_label,
    load_selected,
    member_maps,
    row_has_content,
    rows_for,
    safe,
    safe_key,
    source_snapshot,
    storage_rows,
)
from components.pbm_rows import add_row, copy_day, render_row, set_default
from components.profile_builder_module_store import (
    EDIT_SCOPE_ALL,
    EDIT_SCOPE_UNALLOCATED,
    list_profiles_for_editing,
    save_profile_module,
)

LABELS = {"meal": "Meals", "exercise": "Exercise", "supplement": "Supplements"}
ALL_PROFILE_SCOPE = "All editable profiles"
UNALLOCATED_PROFILE_SCOPE = "Unallocated profiles"


def _scope_options(member_labels: List[str]) -> List[str]:
    return [ALL_PROFILE_SCOPE, UNALLOCATED_PROFILE_SCOPE] + [
        label for label in member_labels if label != SELECT_MEMBER
    ]


def _scope_value(scope_label: str, label_to_id: Dict[str, str]) -> str:
    if scope_label == UNALLOCATED_PROFILE_SCOPE:
        return EDIT_SCOPE_UNALLOCATED
    if scope_label == ALL_PROFILE_SCOPE:
        return EDIT_SCOPE_ALL
    return label_to_id.get(scope_label, EDIT_SCOPE_ALL)


def _profile_label(row: Dict) -> str:
    status = clean(row.get("status"), "draft").upper()
    assignment = clean(row.get("assigned_member_label")) or "Unallocated"
    updated = str(row.get("updated_at") or "")[:16]
    return f"{row.get('profile_name', 'Untitled')} · {status} · {assignment} · {updated}"


def render_selector(kind: str) -> Tuple[bool, str, str]:
    label = LABELS[kind]
    member_labels, label_to_id, _id_to_label, member_message = member_maps()
    scope_key = f"pbm_module_scope_{kind}"
    scope_options = _scope_options(member_labels)
    set_default(scope_key, ALL_PROFILE_SCOPE)
    if st.session_state[scope_key] not in scope_options:
        st.session_state[scope_key] = ALL_PROFILE_SCOPE

    scope_column, profile_column, load_column = st.columns(
        [0.30, 0.52, 0.18], gap="medium"
    )
    scope_label = scope_column.selectbox(
        "Profile Scope",
        scope_options,
        key=scope_key,
    )
    scope_value = _scope_value(scope_label, label_to_id)
    ok, profiles, profile_message = list_profiles_for_editing(scope_value)
    if not ok:
        profiles = []

    profile_ids = [""] + [clean(row.get("id")) for row in profiles]
    by_id = {
        clean(row.get("id")): row
        for row in profiles
        if clean(row.get("id"))
    }
    profile_key = f"pbm_module_profile_{kind}"
    loaded_profile_id = clean(st.session_state.get("pbm_loaded_profile_id"))
    default_profile = loaded_profile_id if loaded_profile_id in profile_ids else ""
    if (
        profile_key not in st.session_state
        or st.session_state[profile_key] not in profile_ids
    ):
        st.session_state[profile_key] = default_profile

    profile_id = profile_column.selectbox(
        "Editable Profile",
        profile_ids,
        format_func=lambda value: (
            SELECT_PROFILE if not value else _profile_label(by_id[value])
        ),
        key=profile_key,
    )
    load_column.markdown(
        "<div class='hm-load-label'>&nbsp;</div>", unsafe_allow_html=True
    )
    if load_column.button(
        "Load Profile",
        key=f"pbm_module_load_{kind}",
        use_container_width=True,
        disabled=not bool(profile_id),
    ):
        load_ok, message = load_selected(profile_id, shell_only=False)
        if load_ok:
            st.success(message)
            st.rerun()
        st.error(message)

    st.caption(
        f"Member source: {member_message} {profile_message} Archived and replaced profiles are historical and excluded."
    )
    ready = bool(
        profile_id
        and clean(st.session_state.get("pbm_loaded_profile_id")) == profile_id
    )
    if ready:
        profile = st.session_state["pbm_profile"]
        status = clean(profile.get("status"), "draft").title()
        assignment = clean(profile.get("assigned_member_label")) or "Unallocated"
        st.markdown(
            f"<div class='hm-readiness-strip hm-ready-ok'><b>{label} profile loaded.</b> "
            f"{safe(profile.get('profile_name'))} · {safe(status)} · {safe(assignment)}</div>",
            unsafe_allow_html=True,
        )
        if clean(profile.get("status")).lower() == "active":
            st.warning(
                "This is the member's Active profile. Saving this module updates the same live Profile ID; member allocation remains protected."
            )
    else:
        st.info(
            f"Select Profile Scope and Editable Profile, then click Load Profile before editing or saving {label}."
        )

    loaded_member_id = (
        clean(st.session_state.get("pbm_loaded_member_id")) if ready else ""
    )
    return ready, loaded_member_id, profile_id


def day_picker(kind: str) -> int:
    key = f"pbm_day_{kind}"
    st.session_state.setdefault(key, 1)
    for group in ([1, 2, 3, 4], [5, 6, 7]):
        columns = st.columns(len(group), gap="small")
        for column, day in zip(columns, group):
            if column.button(
                day_label(day),
                key=f"{key}_{day}",
                type="primary" if st.session_state[key] == day else "secondary",
                use_container_width=True,
            ):
                st.session_state[key] = day
                st.rerun()
    return int(st.session_state[key])


def copy_controls(kind: str, day: int) -> None:
    columns = st.columns(2, gap="medium")
    if columns[0].button(
        "Copy selected day to all other days",
        key=f"pbm_copy_all_{kind}_{day}",
        use_container_width=True,
    ):
        copy_day(kind, day, [value for value in range(1, 8) if value != day])
        st.rerun()
    if columns[1].button(
        "Copy previous day",
        key=f"pbm_copy_prev_{kind}_{day}",
        use_container_width=True,
        disabled=day == 1,
    ):
        copy_day(kind, day - 1, [day])
        st.rerun()


def render_module(kind: str, options: Dict[str, List[str]]) -> None:
    ready, member_id, profile_id = render_selector(kind)
    if not ready:
        return
    day = day_picker(kind)
    if kind == "meal":
        st.markdown(
            "<div class='hm-title'>Meal Structure</div><div class='hm-sub'>Recipe, Portion and Instruction are saved only to the loaded profile’s Meals module.</div>",
            unsafe_allow_html=True,
        )
        for slot in MEAL_SLOTS:
            st.markdown(
                f"<div class='hm-slot'>{safe(slot)}</div>", unsafe_allow_html=True
            )
            for row in rows_for(kind, day, slot):
                render_row(kind, row, options)
            if st.button(
                "Add food item",
                key=f"pbm_add_{kind}_{day}_{safe_key(slot)}",
                use_container_width=True,
            ):
                add_row(kind, day, slot)
                st.rerun()
    elif kind == "exercise":
        st.markdown(
            "<div class='hm-title'>Exercise Regime</div><div class='hm-sub'>Exercise, Time of Day and Instruction are saved only to the loaded profile’s Exercise module. Repository details open immediately after exercise selection.</div>",
            unsafe_allow_html=True,
        )
        for row in rows_for(kind, day, "Exercise Regime"):
            render_row(kind, row, options)
        if st.button(
            "Add workout item",
            key=f"pbm_add_{kind}_{day}",
            use_container_width=True,
        ):
            add_row(kind, day, "Exercise Regime")
            st.rerun()
    else:
        st.markdown(
            "<div class='hm-title'>Supplement Regime</div><div class='hm-sub'>Supplement, Frequency, Timeline, Dosage and Instruction are saved only to the loaded profile’s Supplements module.</div>",
            unsafe_allow_html=True,
        )
        for row in rows_for(kind, day, "Supplement Regime"):
            render_row(kind, row, options)
        if st.button(
            "Add supplement item",
            key=f"pbm_add_{kind}_{day}",
            use_container_width=True,
        ):
            add_row(kind, day, "Supplement Regime")
            st.rerun()
    copy_controls(kind, day)
    label = LABELS[kind]
    if st.button(
        f"Save {label}",
        key=f"pbm_save_{kind}",
        type="primary",
        use_container_width=True,
    ):
        if kind == "supplement":
            invalid = [
                row
                for row in st.session_state["pbm_items"]
                if row.get("item_type") == kind
                and int(row.get("frequency") or 0)
                and len(row.get("timeline") or [])
                != int(row.get("frequency") or 0)
            ]
            if invalid:
                st.error(
                    "Correct Supplement Frequency and Timeline validation before saving."
                )
                return
        ok, message = save_profile_module(
            profile_id,
            member_id,
            kind,
            storage_rows(kind),
            created_by_user_id=st.session_state.get("user_id", ""),
            created_by_email=st.session_state.get("user_email", ""),
        )
        st.success(message) if ok else st.error(message)


def preview_rows(day: int) -> List[Dict]:
    output = []
    for row in st.session_state["pbm_items"]:
        if int(row.get("day_number") or 0) != day or not row_has_content(row):
            continue
        kind = row.get("item_type")
        if kind == "meal":
            output.append(
                {
                    "Type": "Meal",
                    "Slot": row.get("slot_name") or "NA",
                    "Recommendation": row.get("reference_label") or "NA",
                    "Portion / Frequency": row.get("portion") or "NA",
                    "Timing": "NA",
                    "Instruction": row.get("instruction") or "NA",
                }
            )
        elif kind == "exercise":
            snapshot = source_snapshot(kind, row.get("reference_label") or "")
            overrides = row.get("source_admin_overrides") or {}
            output.append(
                {
                    "Type": "Exercise",
                    "Slot": "Exercise",
                    "Recommendation": row.get("reference_label") or "NA",
                    "Portion / Frequency": overrides.get("difficulty")
                    or snapshot.get("difficulty")
                    or "NA",
                    "Timing": row.get("scheduled_time") or "NA",
                    "Instruction": row.get("instruction") or "NA",
                }
            )
        else:
            output.append(
                {
                    "Type": "Supplement",
                    "Slot": "Supplement",
                    "Recommendation": row.get("reference_label") or "NA",
                    "Portion / Frequency": f"{row.get('frequency') or 'NA'} / {row.get('dosage') or 'NA'}",
                    "Timing": ", ".join(row.get("timeline") or []) or "NA",
                    "Instruction": row.get("instruction") or "NA",
                }
            )
    return output


def render_preview() -> None:
    profile = st.session_state["pbm_profile"]
    if not profile.get("id"):
        st.info("Load a saved editable profile from Setup or a recommendation module first.")
        return
    st.markdown(
        "<div class='hm-title'>Preview & End-to-End Flow Review</div><div class='hm-sub'>Preview aggregates the loaded Setup shell and all saved/loaded module rows. Publish remains controlled through Publish.</div>",
        unsafe_allow_html=True,
    )
    concerns = profile.get("health_concerns") or []
    start = profile.get("start_date")
    start_text = start.isoformat() if hasattr(start, "isoformat") else clean(start)
    profile_status = clean(profile.get("status"), "draft").title()
    assignment = clean(profile.get("assigned_member_label")) or "Unallocated"
    st.markdown(
        f"<div class='hm-preview'><b>Profile Summary</b><br><b>Profile ID:</b> {safe(profile.get('id'))}<br><b>Profile:</b> {safe(profile.get('profile_name'))}<br><b>Status:</b> {safe(profile_status)}<br><b>Assigned Member:</b> {safe(assignment)}<br><b>Start Date:</b> {safe(start_text)}<br><b>Tags:</b> {safe(profile.get('region') or 'NA')} — {safe(profile.get('age_band') or 'NA')} — {safe(profile.get('diet_type') or 'NA')} — {safe(', '.join(concerns) if concerns else 'No health concern selected')}<br><b>Profile Note:</b> {safe(profile.get('profile_note') or 'NA')}</div>",
        unsafe_allow_html=True,
    )
    counts = {
        kind: len(
            [
                row
                for row in st.session_state["pbm_items"]
                if row.get("item_type") == kind and row_has_content(row)
            ]
        )
        for kind in ("meal", "exercise", "supplement")
    }
    st.markdown(
        f"<div class='hm-count-grid'><div class='hm-count-card'><b>{counts['meal']}</b><span>Meal rows</span></div><div class='hm-count-card'><b>{counts['exercise']}</b><span>Exercise rows</span></div><div class='hm-count-card'><b>{counts['supplement']}</b><span>Supplement rows</span></div><div class='hm-count-card'><b>{sum(counts.values())}</b><span>Total rows</span></div></div>",
        unsafe_allow_html=True,
    )
    day = st.selectbox(
        "Preview Day",
        list(range(1, 8)),
        format_func=day_label,
        key="pbm_preview_day",
    )
    rows = preview_rows(day)
    if rows:
        st.dataframe(rows, use_container_width=True, hide_index=True)
    else:
        st.info("No recommendation rows have been added for this day yet.")
    st.markdown(
        "<div class='hm-preview'><b>Editing and publish boundary</b><br>Draft and Active profiles may be edited in place. Active allocation remains protected. Use Publish to activate a Draft, and Clone Setup when a new version is intended.</div>",
        unsafe_allow_html=True,
    )
