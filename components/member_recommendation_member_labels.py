from __future__ import annotations

import streamlit as st

from components.member_recommendation_split_display import (
    _esc,
    _chips,
    _inject_styles,
    _load_for_member,
    _render_item,
    _render_section,
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


def _inject_member_label_styles() -> None:
    st.markdown(
        """
        <style>
        .hm-weekly-toggle-anchor + div [data-testid="stButton"] > button,
        .hm-weekly-toggle-anchor + div .stButton > button{
            justify-content:center!important;
            text-align:center!important;
            min-height:2.72rem!important;
            background:linear-gradient(135deg,#FFFDF8 0%,#FFF6E5 100%)!important;
            border:1.45px solid #D8A84E!important;
            border-radius:16px!important;
            box-shadow:0 7px 16px rgba(15,23,42,.045)!important;
            color:#064E3B!important;
            font-weight:950!important;
            margin:.52rem 0 .34rem 0!important;
            padding:.58rem .78rem!important;
            white-space:normal!important;
        }
        .hm-weekly-toggle-anchor + div [data-testid="stButton"] > button *,
        .hm-weekly-toggle-anchor + div .stButton > button *{
            color:#064E3B!important;
            font-size:.90rem!important;
            font-weight:950!important;
            line-height:1.18!important;
            white-space:normal!important;
            overflow-wrap:normal!important;
            word-break:normal!important;
            text-align:center!important;
        }
        .hm-weekly-toggle-body{
            border:1px solid #E7D8BE;
            background:#FFFDF8;
            border-radius:16px;
            padding:.78rem .86rem;
            margin:.10rem 0 .78rem 0;
        }
        </style>
        """,
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


def _toggle_day(label: str, key: str, default_open: bool = False) -> bool:
    state_key = f"hm_weekly_toggle_{key}"
    if state_key not in st.session_state:
        st.session_state[state_key] = default_open
    is_open = bool(st.session_state.get(state_key))
    prefix = "▾" if is_open else "▸"
    st.markdown("<div class='hm-weekly-toggle-anchor'></div>", unsafe_allow_html=True)
    if st.button(f"{prefix} {label}", key=f"{state_key}_btn", use_container_width=True):
        st.session_state[state_key] = not is_open
        st.rerun()
    return bool(st.session_state.get(state_key))


def _render_weekly_type_clean(profile: dict, items: list[dict], item_type: str, title: str, empty: str) -> None:
    st.markdown(f"<div class='hm-rec-section-title'>{_esc(title)}</div>", unsafe_allow_html=True)
    current_day = today_day_number(profile)
    for day in range(1, 8):
        rows = items_for_day(items, day, item_type)
        if _toggle_day(day_label(profile, day), f"{item_type}_{day}", default_open=(day == current_day)):
            st.markdown("<div class='hm-weekly-toggle-body'>", unsafe_allow_html=True)
            if not rows:
                st.markdown(f"<div class='hm-rec-empty'>{_esc(empty)}</div>", unsafe_allow_html=True)
            for row in rows:
                _render_item(row)
            st.markdown("</div>", unsafe_allow_html=True)


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

    st.divider()
    if st.button("Log today's activity", key="hm_todays_plan_log_activity", use_container_width=True):
        st.session_state["hm_daily_log_target_tab"] = "Food Journal"
        st.switch_page("pages/18_Daily_Log.py")


def _render_weekly_plan_body(profile: dict, items: list[dict]) -> None:
    meal_tab, supplement_tab, exercise_tab, guidance_tab = st.tabs(["Meals", "Supplements", "Exercises", "Nutrition Guidance"])
    with meal_tab:
        _render_weekly_type_clean(profile, items, "meal", "Weekly Meal Recommendation", "No meals scheduled for this day.")
    with supplement_tab:
        _render_weekly_type_clean(profile, items, "supplement", "Weekly Supplement Recommendation", "No supplements scheduled for this day.")
    with exercise_tab:
        _render_weekly_type_clean(profile, items, "exercise", "Weekly Exercise Recommendation", "No exercises scheduled for this day.")
    with guidance_tab:
        _render_member_guidance(profile, items, day=None, title="Weekly Nutrition Guidance")


def render_todays_plan_view() -> None:
    _inject_styles()
    _inject_member_label_styles()
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
    _inject_member_label_styles()
    ok, profile, items, message = _load_for_member()
    if not ok:
        st.error(message)
        return
    if not profile:
        _empty_state()
        return
    _render_weekly_plan_body(profile, items)
