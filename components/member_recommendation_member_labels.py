from __future__ import annotations

import streamlit as st

from components.member_recommendation_split_display import (
    _esc,
    _guidance_items,
    _inject_styles,
    _load_for_member,
    _render_guidance,
    _render_section,
    _render_weekly,
    _section_count,
    active_items,
    day_label,
    items_for_day,
    today_day_number,
)


def _empty_state() -> None:
    st.markdown(
        "<div class='hm-rec-empty'>No active recommendation has been published for you yet. Your nutritionist will publish it when ready.</div>",
        unsafe_allow_html=True,
    )


def _render_weekly_summary(profile: dict, items: list[dict]) -> None:
    """Compact weekly summary for the full seven-day plan."""
    rows = active_items(items)
    today_day = today_day_number(profile)
    st.markdown(
        f"""
        <div class='hm-rec-hero'>
          <div class='hm-rec-title'>My Weekly Plan</div>
          <div class='hm-rec-sub'>Your complete seven-day recommendation, organised by meals, supplements, exercises and guidance.</div>
          <div class='hm-rec-sub'><b>Profile:</b> {_esc(profile.get('profile_name') or 'Active Recommendation')} · <b>Start:</b> {_esc(profile.get('start_date') or 'NA')} · <b>Today:</b> Day {today_day}</div>
        </div>
        <div class='hm-rec-count-grid'>
          <div class='hm-rec-count'><b>{_section_count(rows, 'meal')}</b><span>Meals</span></div>
          <div class='hm-rec-count'><b>{_section_count(rows, 'supplement')}</b><span>Supplements</span></div>
          <div class='hm-rec-count'><b>{_section_count(rows, 'exercise')}</b><span>Exercises</span></div>
          <div class='hm-rec-count'><b>{len(_guidance_items(profile, rows, None))}</b><span>Guidance</span></div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_todays_plan_body(profile: dict, items: list[dict]) -> None:
    """Action-only today view. No refresh button, no counters, no cross-navigation."""
    today_day = today_day_number(profile)
    st.markdown(
        f"""
        <div class='hm-rec-day-label'>Today · {_esc(day_label(profile, today_day))}</div>
        <div class='hm-rec-sub'>Today’s actions are pulled from your active weekly recommendation.</div>
        """,
        unsafe_allow_html=True,
    )

    meal_col, supplement_col, exercise_col = st.columns(3, gap="small")
    with meal_col:
        _render_section(
            "Meals",
            items_for_day(items, today_day, "meal"),
            "No meal recommendation added for today.",
            compact=True,
        )
    with supplement_col:
        _render_section(
            "Supplements",
            items_for_day(items, today_day, "supplement"),
            "No supplement recommendation added for today.",
            compact=True,
        )
    with exercise_col:
        _render_section(
            "Exercises",
            items_for_day(items, today_day, "exercise"),
            "No exercise recommendation added for today.",
            compact=True,
        )

    _render_guidance(profile, items, day=today_day, title="Nutrition Guidance")


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
    _render_weekly_summary(profile, items)
    _render_weekly(profile, items)
