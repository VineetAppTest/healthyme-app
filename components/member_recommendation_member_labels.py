from __future__ import annotations

import streamlit as st

from components.member_recommendation_split_display import (
    _esc,
    _guidance_items,
    _inject_styles,
    _load_for_member,
    _render_refresh,
    _render_today,
    _render_weekly,
    _section_count,
    active_items,
    clear_member_recommendation_cache,
    today_day_number,
)


def _render_member_summary(profile: dict, items: list[dict], message: str, mode: str) -> None:
    """Member-facing summary with final product labels.

    Today's Plan is only today's calculated slice.
    My Weekly Plan is the complete seven-day plan.
    """
    rows = active_items(items)
    today_day = today_day_number(profile)
    is_today = mode == "today"
    title = "Today's Plan" if is_today else "My Weekly Plan"
    subtitle = (
        "Today's action tiles pulled from your active weekly recommendation."
        if is_today
        else "Your complete seven-day recommendation, organised by meals, supplements, exercises and guidance."
    )
    day_arg = today_day if is_today else None
    st.markdown(
        f"""
        <div class='hm-rec-hero'>
          <div class='hm-rec-title'>{_esc(title)}</div>
          <div class='hm-rec-sub'>{_esc(subtitle)}</div>
          <div class='hm-rec-sub'><b>Profile:</b> {_esc(profile.get('profile_name') or 'Active Recommendation')} · <b>Start:</b> {_esc(profile.get('start_date') or 'NA')} · <b>Today:</b> Day {today_day}</div>
          <div class='hm-rec-source'>{_esc(message)}</div>
        </div>
        <div class='hm-rec-count-grid'>
          <div class='hm-rec-count'><b>{_section_count(rows, 'meal', day_arg)}</b><span>Meals</span></div>
          <div class='hm-rec-count'><b>{_section_count(rows, 'supplement', day_arg)}</b><span>Supplements</span></div>
          <div class='hm-rec-count'><b>{_section_count(rows, 'exercise', day_arg)}</b><span>Exercises</span></div>
          <div class='hm-rec-count'><b>{len(_guidance_items(profile, rows, day_arg))}</b><span>Guidance</span></div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_todays_plan_view() -> None:
    _inject_styles()
    _render_refresh()
    ok, profile, items, message = _load_for_member()
    if not ok:
        st.error(message)
        return
    if not profile:
        st.markdown(
            "<div class='hm-rec-empty'>No active recommendation has been published for you yet. Your nutritionist will publish it when ready.</div>",
            unsafe_allow_html=True,
        )
        return
    _render_member_summary(profile, items, message, mode="today")
    if st.button("Open My Weekly Plan", use_container_width=True):
        st.switch_page("pages/37_Member_Plan.py")
    _render_today(profile, items)


def render_my_weekly_plan_view() -> None:
    _inject_styles()
    _render_refresh()
    ok, profile, items, message = _load_for_member()
    if not ok:
        st.error(message)
        return
    if not profile:
        st.markdown(
            "<div class='hm-rec-empty'>No active recommendation has been published for you yet. Your nutritionist will publish it when ready.</div>",
            unsafe_allow_html=True,
        )
        return
    _render_member_summary(profile, items, message, mode="weekly")
    if st.button("Open Today's Plan", use_container_width=True):
        st.switch_page("pages/36_Todays_Journey.py")
    _render_weekly(profile, items)
