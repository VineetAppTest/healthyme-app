from __future__ import annotations

import html
from typing import Any

import streamlit as st

from components.current_member_plan import load_current_member_plan
from components.member_recommendation_member_labels import (
    _inject_member_label_styles,
    _render_member_guidance,
    _render_weekly_type_clean,
)
from components.member_recommendation_split_display import (
    _inject_styles,
    _render_section,
    day_label,
    items_for_day,
    today_day_number,
)
from components.member_timezone import member_local_today


def _clean(value: Any) -> str:
    return str(value or "").strip()


def _esc(value: Any) -> str:
    return html.escape(_clean(value))


def _member_identity() -> tuple[str, str]:
    member_id = _clean(st.session_state.get("user_id"))
    email = _clean(
        st.session_state.get("user_email")
        or st.session_state.get("oidc_email")
        or st.session_state.get("email")
    )
    return member_id, email


def _load_model() -> tuple[bool, dict[str, Any], str]:
    member_id, email = _member_identity()
    if not member_id:
        return False, {}, "Member identity is unavailable."
    return load_current_member_plan(
        member_id,
        email,
        today=member_local_today(member_id),
    )


def _inject_current_plan_styles() -> None:
    st.markdown(
        """
        <style id="hm-current-member-plan-v1">
        .hm-current-plan-note{border:1px solid #D9C28F;border-radius:14px;background:#FFF9EC;color:#5D4A1E;padding:.66rem .78rem;margin:.38rem 0 .72rem 0;font-size:.82rem;font-weight:720;line-height:1.38;}
        .hm-current-card{border:1px solid #E7D8BE;border-radius:16px;background:#FFFDF8;padding:.76rem .84rem;margin:.42rem 0 .62rem 0;box-shadow:0 7px 18px rgba(15,23,42,.045);}
        .hm-current-title{color:#064E3B;font-size:.96rem;font-weight:950;line-height:1.22;margin:0 0 .34rem 0;}
        .hm-current-chip-row{display:flex;flex-wrap:wrap;gap:.32rem;margin:.18rem 0 .30rem 0;}
        .hm-current-chip{display:inline-flex;gap:.22rem;align-items:center;border:1px solid #D9C28F;border-radius:999px;background:#FFF7E6;color:#5D4A1E;padding:.18rem .46rem;font-size:.72rem;font-weight:760;line-height:1.15;}
        .hm-current-line{color:#334155;font-size:.82rem;line-height:1.42;margin:.20rem 0 0 0;}
        .hm-current-provenance{color:#64748B;font-size:.70rem;line-height:1.32;margin:.30rem 0 0 0;}
        .hm-current-section{color:#064E3B;font-size:1rem;font-weight:950;margin:.28rem 0 .42rem 0;}
        .hm-current-empty{border:1px dashed #D9C28F;border-radius:14px;background:#FFFDF8;color:#64748B;padding:.72rem .78rem;margin:.36rem 0 .62rem 0;font-size:.82rem;line-height:1.38;}
        </style>
        """,
        unsafe_allow_html=True,
    )


def _chip(label: str, value: Any) -> str:
    text = _clean(value)
    if not text:
        return ""
    return (
        "<span class='hm-current-chip'>"
        f"<b>{_esc(label)}:</b> {_esc(text)}"
        "</span>"
    )


def _render_allocation_card(row: dict[str, Any], domain: str) -> None:
    snapshot = dict(row.get("source_snapshot") or {})
    if domain == "exercise":
        title = (
            _clean(row.get("exercise_name"))
            or _clean(row.get("title"))
            or _clean(snapshot.get("title"))
            or "Exercise"
        )
        chips = [
            _chip("Start", row.get("start_date") or "Current"),
            _chip("End", row.get("end_date") or "Open"),
            _chip("Category", snapshot.get("category")),
            _chip("Difficulty", snapshot.get("difficulty")),
            _chip("Duration/Reps", snapshot.get("duration_or_reps")),
            _chip("Equipment", snapshot.get("equipment")),
        ]
        instruction = _clean(row.get("instructions") or snapshot.get("instructions"))
        note = _clean(row.get("notes"))
    else:
        title = (
            _clean(row.get("supplement_name"))
            or _clean(row.get("title"))
            or _clean(snapshot.get("supplement_name"))
            or _clean(snapshot.get("title"))
            or "Supplement"
        )
        chips = [
            _chip("Dosage", row.get("dosage") or snapshot.get("dosage")),
            _chip("Frequency", row.get("frequency") or snapshot.get("frequency")),
            _chip("Timing", row.get("timing") or snapshot.get("timing")),
            _chip("Start", row.get("start_date") or "Current"),
            _chip("End", row.get("end_date") or "Open"),
        ]
        instruction = _clean(row.get("instructions") or snapshot.get("instructions"))
        note = ""

    source_id = _clean(row.get("source_id"))
    source_type = _clean(row.get("source_type"))
    body = ""
    if instruction:
        body += "<div class='hm-current-line'>" f"<b>Instructions:</b> {_esc(instruction)}" "</div>"
    if note:
        body += "<div class='hm-current-line'>" f"<b>Notes:</b> {_esc(note)}" "</div>"
    provenance = ""
    if source_type or source_id:
        provenance = (
            "<div class='hm-current-provenance'>"
            f"Source: {_esc(source_type)}"
            + (f" · {_esc(source_id)}" if source_id else "")
            + "</div>"
        )

    st.markdown(
        (
            "<div class='hm-current-card'>"
            f"<div class='hm-current-title'>{_esc(title)}</div>"
            f"<div class='hm-current-chip-row'>{''.join(chips)}</div>"
            f"{body}{provenance}"
            "</div>"
        ),
        unsafe_allow_html=True,
    )


def _render_allocation_group(
    title: str,
    current_rows: list[dict[str, Any]],
    upcoming_rows: list[dict[str, Any]],
    domain: str,
    empty_message: str,
) -> None:
    st.markdown(f"<div class='hm-current-section'>{_esc(title)}</div>", unsafe_allow_html=True)
    if not current_rows:
        st.markdown(f"<div class='hm-current-empty'>{_esc(empty_message)}</div>", unsafe_allow_html=True)
    for row in current_rows:
        _render_allocation_card(row, domain)
    if upcoming_rows:
        with st.expander(f"Upcoming {title.lower()} ({len(upcoming_rows)})"):
            for row in upcoming_rows:
                _render_allocation_card(row, domain)


def _render_warnings(model: dict[str, Any]) -> None:
    warnings = [str(value) for value in model.get("warnings", []) if value]
    if warnings:
        st.warning(" ".join(warnings))


def _render_authority_note(model: dict[str, Any]) -> None:
    ignored = dict(model.get("ignored_profile_rows") or {})
    hidden = int(ignored.get("exercise", 0)) + int(ignored.get("supplement", 0))
    note = (
        "This page is read-only. Meals come from the active Meal Profile; "
        "Exercises and Supplements come from their independent member-allocation workflows."
    )
    if hidden:
        note += (
            f" {hidden} retained legacy non-meal Profile Builder row"
            + ("s are" if hidden != 1 else " is")
            + " intentionally excluded."
        )
    st.markdown(f"<div class='hm-current-plan-note'>{_esc(note)}</div>", unsafe_allow_html=True)


def render_current_member_plan_view() -> None:
    _inject_styles()
    _inject_member_label_styles()
    _inject_current_plan_styles()
    ok, model, message = _load_model()
    if not ok:
        st.error(message)
        return
    _render_warnings(model)
    _render_authority_note(model)
    if not model.get("has_content"):
        st.markdown("<div class='hm-current-empty'>No current plan has been allocated yet.</div>", unsafe_allow_html=True)
        return

    meal_tab, exercise_tab, supplement_tab, guidance_tab = st.tabs(
        ["Meals", "Exercises", "Supplements", "Nutrition Guidance"]
    )
    with meal_tab:
        profile = dict(model.get("meal_profile") or {})
        meals = list(model.get("meals") or [])
        if profile and meals:
            _render_weekly_type_clean(profile, meals, "meal", "Weekly Meal Recommendation", "No meals scheduled for this day.")
        else:
            st.markdown("<div class='hm-current-empty'>No active Meal Profile is published.</div>", unsafe_allow_html=True)
    with exercise_tab:
        exercise = dict(model.get("exercise") or {})
        _render_allocation_group("Current Exercises", list(exercise.get("current") or []), list(exercise.get("upcoming") or []), "exercise", "No current Exercise allocation.")
    with supplement_tab:
        supplement = dict(model.get("supplement") or {})
        _render_allocation_group("Current Supplements", list(supplement.get("current") or []), list(supplement.get("upcoming") or []), "supplement", "No current Supplement allocation.")
    with guidance_tab:
        _render_member_guidance(dict(model.get("meal_profile") or {}), list(model.get("guidance_items") or []), day=None, title="Current Nutrition Guidance")


def render_todays_current_plan_view() -> None:
    _inject_styles()
    _inject_member_label_styles()
    _inject_current_plan_styles()
    ok, model, message = _load_model()
    if not ok:
        st.error(message)
        return
    _render_warnings(model)
    _render_authority_note(model)

    profile = dict(model.get("meal_profile") or {})
    meals = list(model.get("meals") or [])
    today_meals: list[dict[str, Any]] = []
    today_day = None
    if profile:
        today_day = today_day_number(profile, today=member_local_today(model.get("member_id", "")))
        today_meals = items_for_day(meals, today_day, "meal")
        st.markdown("<div class='hm-rec-day-label'>" f"Today - {_esc(day_label(profile, today_day))}" "</div>", unsafe_allow_html=True)

    exercise = dict(model.get("exercise") or {})
    supplement = dict(model.get("supplement") or {})
    meal_col, supplement_col, exercise_col = st.columns(3, gap="small")
    with meal_col:
        _render_section("Meals", today_meals, "No meal recommendation added for today.", compact=True)
    with supplement_col:
        _render_allocation_group("Supplements", list(supplement.get("current") or []), [], "supplement", "No current Supplement allocation.")
    with exercise_col:
        _render_allocation_group("Exercises", list(exercise.get("current") or []), [], "exercise", "No current Exercise allocation.")

    _render_member_guidance(profile, list(model.get("guidance_items") or []), day=today_day, title="Nutrition Guidance")
    st.divider()
    if st.button("Log today's activity", key="hm_current_plan_log_activity", use_container_width=True):
        st.session_state["hm_daily_log_target_tab"] = "Food Journal"
        st.switch_page("pages/18_Daily_Log.py")
