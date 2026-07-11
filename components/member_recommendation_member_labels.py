from __future__ import annotations

import streamlit as st

from components.member_recommendation_split_display import (
    _esc,
    _chips,
    _inject_styles,
    _load_for_member,
    _render_section,
    _render_weekly_type,
    active_items,
    day_label,
    items_for_day,
    today_day_number,
)

EXPLICIT_PROFILE_GUIDANCE_FIELDS = (
    "nutrition_guidance",
    "nutrition_guidance_note",
    "nutritionist_guidance",
    "nutritionist_note",
    "weekly_guidance",
    "weekly_nutrition_guidance",
    "profile_guidance",
    "profile_level_nutrition_note",
    "nutrition_note",
    "member_guidance",
    "guidance_note",
    "additional_guidance",
    "ancillary_guidance",
)
GUIDANCE_ITEM_TYPES = {"guidance", "nutrition_guidance", "nutrition"}


def _clean(value: object, default: str = "") -> str:
    if value is None:
        return default
    text = str(value).strip()
    return text if text else default


def _safe_int(value: object, default: int = 0) -> int:
    try:
        return int(value or default)
    except Exception:
        return default


def _empty_state() -> None:
    st.markdown(
        "<div class='hm-rec-empty'>No active recommendation has been published for you yet. Your nutritionist will publish it when ready.</div>",
        unsafe_allow_html=True,
    )


def _explicit_guidance_items(profile: dict, items: list[dict], day: int | None = None) -> list[tuple[str, str]]:
    values: list[tuple[str, str]] = []
    for field in EXPLICIT_PROFILE_GUIDANCE_FIELDS:
        text = _clean(profile.get(field))
        if text:
            values.append(("Guidance", text))
    for row in active_items(items):
        if _clean(row.get("item_type")).lower() not in GUIDANCE_ITEM_TYPES:
            continue
        if day is not None and _safe_int(row.get("day_number")) != day:
            continue
        label = _clean(row.get("reference_label"), "Guidance")
        text = _clean(row.get("instruction") or row.get("portion") or row.get("scheduled_time"))
        if text:
            values.append((label, text))
    unique: list[tuple[str, str]] = []
    seen = set()
    for label, text in values:
        marker = (_clean(label).lower(), _clean(text).lower())
        if marker in seen:
            continue
        seen.add(marker)
        unique.append((label, text))
    return unique


def _render_member_guidance(profile: dict, items: list[dict], day: int | None = None, title: str = "Nutrition Guidance") -> None:
    values = _explicit_guidance_items(profile, items, day=day)
    st.markdown(f"<div class='hm-rec-section-title'>{_esc(title)}</div>", unsafe_allow_html=True)
    if not values:
        st.markdown("<div class='hm-rec-empty'>No Guidance shared.</div>", unsafe_allow_html=True)
        return
    chips = _chips([(label, text) for label, text in values[:24]])
    st.markdown(f"<div class='hm-guidance-box'><div class='hm-chip-row'>{chips}</div></div>", unsafe_allow_html=True)


def _render_todays_plan_body(profile: dict, items: list[dict]) -> None:
    today_day = today_day_number(profile)
    st.markdown(
        f"""
        <div class='hm-rec-day-label'>Today - {_esc(day_label(profile, today_day))}</div>
        <div class='hm-rec-sub'>Today's actions are pulled from your active weekly recommendation.</div>
        """,
        unsafe_allow_html=True,
    )
    meal_col, supplement_col, exercise_col = st.columns(3, gap="small")
    with meal_col:
        _render_section("Meals", items_for_day(items, today_day, "meal"), "No meal recommendation added for today.", compact=True)
    with supplement_col:
        _render_section("Supplements", items_for_day(items, today_day, "supplement"), "No supplement recommendation added for today.", compact=True)
    with exercise_col:
        _render_section("Exercises", items_for_day(items, today_day, "exercise"), "No exercise recommendation added for today.", compact=True)
    _render_member_guidance(profile, items, day=today_day, title="Nutrition Guidance")


def _render_weekly_plan_body(profile: dict, items: list[dict]) -> None:
    meal_tab, supplement_tab, exercise_tab, guidance_tab = st.tabs(["Meals", "Supplements", "Exercises", "Nutrition Guidance"])
    with meal_tab:
        _render_weekly_type(profile, items, "meal", "Weekly Meal Recommendation", "No meals scheduled for this day.")
    with supplement_tab:
        _render_weekly_type(profile, items, "supplement", "Weekly Supplement Recommendation", "No supplements scheduled for this day.")
    with exercise_tab:
        _render_weekly_type(profile, items, "exercise", "Weekly Exercise Recommendation", "No exercises scheduled for this day.")
    with guidance_tab:
        _render_member_guidance(profile, items, day=None, title="Weekly Nutrition Guidance")


def render_todays_plan_view() -> None:
    _inject_styles()
    ok, profile, items, message = _load_for_member()
    if not ok:
        st.error(message)
        return
    if not profile:
        _empty_state()
        return
    _render_todays_plan_body(profile, items)


def render_my_weekly_plan_view() -> None:
    _inject_styles()
    ok, profile, items, message = _load_for_member()
    if not ok:
        st.error(message)
        return
    if not profile:
        _empty_state()
        return
    _render_weekly_plan_body(profile, items)
