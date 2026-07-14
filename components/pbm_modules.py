from __future__ import annotations

from typing import Dict, List, Tuple

import streamlit as st

from components.pbm_core import (
    MEAL_SLOTS, SELECT_MEMBER, SELECT_PROFILE, clean, day_label, load_selected,
    member_maps, row_has_content, rows_for, safe, safe_key, source_snapshot,
    storage_rows,
)
from components.pbm_rows import add_row, copy_day, render_row, set_default
from components.profile_builder_module_store import (
    list_draft_profiles_for_member, save_profile_module,
)

LABELS = {"meal": "Meals", "exercise": "Exercise", "supplement": "Supplements"}


def render_selector(kind: str) -> Tuple[bool, str, str]:
    label = LABELS[kind]; member_labels, label_to_id, id_to_label, member_message = member_maps(); member_key = f"pbm_module_member_{kind}"
    default_member = id_to_label.get(st.session_state.get("pbm_loaded_member_id", ""), SELECT_MEMBER); set_default(member_key, default_member)
    if st.session_state[member_key] not in member_labels: st.session_state[member_key] = SELECT_MEMBER
    member_column, profile_column, load_column = st.columns([.40, .42, .18], gap="medium")
    member_label = member_column.selectbox("Member", member_labels, key=member_key); member_id = label_to_id.get(member_label, "")
    profiles: List[dict] = []; profile_message = "Select a member first."
    if member_id:
        ok, profiles, profile_message = list_draft_profiles_for_member(member_id)
        if not ok: profiles = []
    profile_ids = [""] + [clean(row.get("id")) for row in profiles]; by_id = {clean(row.get("id")): row for row in profiles}; profile_key = f"pbm_module_profile_{kind}"
    default_profile = st.session_state.get("pbm_loaded_profile_id", "") if st.session_state.get("pbm_loaded_member_id") == member_id else ""
    if profile_key not in st.session_state or st.session_state[profile_key] not in profile_ids: st.session_state[profile_key] = default_profile if default_profile in profile_ids else ""
    profile_id = profile_column.selectbox("Draft Profile", profile_ids, format_func=lambda value: SELECT_PROFILE if not value else f"{by_id[value].get('profile_name','Untitled')} · {str(by_id[value].get('updated_at',''))[:16]}", key=profile_key)
    load_column.markdown("<div class='hm-load-label'>&nbsp;</div>", unsafe_allow_html=True)
    if load_column.button("Load Profile", key=f"pbm_module_load_{kind}", use_container_width=True, disabled=not bool(profile_id)):
        ok, message = load_selected(profile_id)
        if ok: st.session_state[member_key] = member_label; st.session_state[profile_key] = profile_id; st.success(message); st.rerun()
        st.error(message)
    st.caption(f"Member source: {member_message} {profile_message}")
    ready = bool(member_id and profile_id and st.session_state.get("pbm_loaded_member_id") == member_id and st.session_state.get("pbm_loaded_profile_id") == profile_id)
    if ready:
        profile = st.session_state["pbm_profile"]; st.markdown(f"<div class='hm-readiness-strip hm-ready-ok'><b>{label} profile loaded.</b> {safe(profile.get('profile_name'))} · {safe(member_label)}</div>", unsafe_allow_html=True)
    else: st.info(f"Select Member and Draft Profile, then click Load Profile before editing or saving {label}.")
    return ready, member_id, profile_id

def day_picker(kind: str) -> int:
    key = f"pbm_day_{kind}"; st.session_state.setdefault(key, 1)
    for group in ([1,2,3,4], [5,6,7]):
        columns = st.columns(len(group), gap="small")
        for column, day in zip(columns, group):
            if column.button(day_label(day), key=f"{key}_{day}", type="primary" if st.session_state[key] == day else "secondary", use_container_width=True): st.session_state[key] = day; st.rerun()
    return int(st.session_state[key])

def copy_controls(kind: str, day: int) -> None:
    columns = st.columns(2, gap="medium")
    if columns[0].button("Copy selected day to all other days", key=f"pbm_copy_all_{kind}_{day}", use_container_width=True): copy_day(kind, day, [value for value in range(1,8) if value != day]); st.rerun()
    if columns[1].button("Copy previous day", key=f"pbm_copy_prev_{kind}_{day}", use_container_width=True, disabled=day == 1): copy_day(kind, day-1, [day]); st.rerun()

def render_module(kind: str, options: Dict[str, List[str]]) -> None:
    ready, member_id, profile_id = render_selector(kind)
    if not ready: return
    day = day_picker(kind)
    if kind == "meal":
        st.markdown("<div class='hm-title'>Meal Structure</div><div class='hm-sub'>Recipe, Portion and Instruction are saved only to the selected profile’s Meals module.</div>", unsafe_allow_html=True)
        for slot in MEAL_SLOTS:
            st.markdown(f"<div class='hm-slot'>{safe(slot)}</div>", unsafe_allow_html=True)
            for row in rows_for(kind, day, slot): render_row(kind, row, options)
            if st.button("Add food item", key=f"pbm_add_{kind}_{day}_{safe_key(slot)}", use_container_width=True): add_row(kind, day, slot); st.rerun()
    elif kind == "exercise":
        st.markdown("<div class='hm-title'>Exercise Regime</div><div class='hm-sub'>Exercise, Time of Day and Instruction are saved only to the selected profile’s Exercise module. Repository details open immediately after exercise selection.</div>", unsafe_allow_html=True)
        for row in rows_for(kind, day, "Exercise Regime"): render_row(kind, row, options)
        if st.button("Add workout item", key=f"pbm_add_{kind}_{day}", use_container_width=True): add_row(kind, day, "Exercise Regime"); st.rerun()
    else:
        st.markdown("<div class='hm-title'>Supplement Regime</div><div class='hm-sub'>Supplement, Frequency, Timeline, Dosage and Instruction are saved only to the selected profile’s Supplements module.</div>", unsafe_allow_html=True)
        for row in rows_for(kind, day, "Supplement Regime"): render_row(kind, row, options)
        if st.button("Add supplement item", key=f"pbm_add_{kind}_{day}", use_container_width=True): add_row(kind, day, "Supplement Regime"); st.rerun()
    copy_controls(kind, day); label = LABELS[kind]
    if st.button(f"Save {label}", key=f"pbm_save_{kind}", type="primary", use_container_width=True):
        if kind == "supplement":
            invalid = [row for row in st.session_state["pbm_items"] if row.get("item_type") == kind and int(row.get("frequency") or 0) and len(row.get("timeline") or []) != int(row.get("frequency") or 0)]
            if invalid: st.error("Correct Supplement Frequency and Timeline validation before saving."); return
        ok, message = save_profile_module(profile_id, member_id, kind, storage_rows(kind), created_by_user_id=st.session_state.get("user_id", ""), created_by_email=st.session_state.get("user_email", ""))
        st.success(message) if ok else st.error(message)

def preview_rows(day: int) -> List[Dict]:
    output = []
    for row in st.session_state["pbm_items"]:
        if int(row.get("day_number") or 0) != day or not row_has_content(row): continue
        kind = row.get("item_type")
        if kind == "meal": output.append({"Type":"Meal", "Slot":row.get("slot_name") or "NA", "Recommendation":row.get("reference_label") or "NA", "Portion / Frequency":row.get("portion") or "NA", "Timing":"NA", "Instruction":row.get("instruction") or "NA"})
        elif kind == "exercise":
            snapshot = source_snapshot(kind, row.get("reference_label") or ""); overrides = row.get("source_admin_overrides") or {}; output.append({"Type":"Exercise", "Slot":"Exercise", "Recommendation":row.get("reference_label") or "NA", "Portion / Frequency":overrides.get("difficulty") or snapshot.get("difficulty") or "NA", "Timing":row.get("scheduled_time") or "NA", "Instruction":row.get("instruction") or "NA"})
        else: output.append({"Type":"Supplement", "Slot":"Supplement", "Recommendation":row.get("reference_label") or "NA", "Portion / Frequency":f"{row.get('frequency') or 'NA'} / {row.get('dosage') or 'NA'}", "Timing":", ".join(row.get("timeline") or []) or "NA", "Instruction":row.get("instruction") or "NA"})
    return output

def render_preview() -> None:
    profile = st.session_state["pbm_profile"]
    if not profile.get("id"): st.info("Load a saved Draft Profile from Setup or a recommendation module first."); return
    st.markdown("<div class='hm-title'>Preview & End-to-End Flow Review</div><div class='hm-sub'>Preview aggregates the loaded Setup shell and all saved/loaded module rows. Publish remains controlled through Publish.</div>", unsafe_allow_html=True)
    concerns = profile.get("health_concerns") or []; start = profile.get("start_date"); start_text = start.isoformat() if hasattr(start, "isoformat") else clean(start)
    st.markdown(f"<div class='hm-preview'><b>Profile Summary</b><br><b>Draft ID:</b> {safe(profile.get('id'))}<br><b>Profile:</b> {safe(profile.get('profile_name'))}<br><b>Status:</b> Draft<br><b>Assigned Member:</b> {safe(profile.get('assigned_member_label'))}<br><b>Start Date:</b> {safe(start_text)}<br><b>Tags:</b> {safe(profile.get('region') or 'NA')} — {safe(profile.get('age_band') or 'NA')} — {safe(profile.get('diet_type') or 'NA')} — {safe(', '.join(concerns) if concerns else 'No health concern selected')}<br><b>Profile Note:</b> {safe(profile.get('profile_note') or 'NA')}</div>", unsafe_allow_html=True)
    counts = {kind: len([row for row in st.session_state["pbm_items"] if row.get("item_type") == kind and row_has_content(row)]) for kind in ("meal","exercise","supplement")}
    st.markdown(f"<div class='hm-count-grid'><div class='hm-count-card'><b>{counts['meal']}</b><span>Meal rows</span></div><div class='hm-count-card'><b>{counts['exercise']}</b><span>Exercise rows</span></div><div class='hm-count-card'><b>{counts['supplement']}</b><span>Supplement rows</span></div><div class='hm-count-card'><b>{sum(counts.values())}</b><span>Total rows</span></div></div>", unsafe_allow_html=True)
    day = st.selectbox("Preview Day", list(range(1,8)), format_func=day_label, key="pbm_preview_day"); rows = preview_rows(day)
    st.dataframe(rows, use_container_width=True, hide_index=True) if rows else st.info("No recommendation rows have been added for this day yet.")
    st.markdown("<div class='hm-preview'><b>Publish Readiness Checklist</b><br>Use Publish after Setup and the required recommendation modules have been saved. Use Active after activation to verify the member-facing contract.</div>", unsafe_allow_html=True)
