from __future__ import annotations

import datetime as dt
import html
import json
import re
from collections import OrderedDict
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import streamlit as st

from components.current_member_plan import load_current_member_plan
from components.member_recommendation_member_labels import _render_member_guidance
from components.member_recommendation_split_display import today_day_number
from components.member_timezone import (
    DEFAULT_MEMBER_TIMEZONE,
    member_local_today,
    member_timezone_name,
)


PERIOD_ORDER = ("Morning", "Midday", "Evening", "Night", "Anytime")
DOMAIN_LABELS = {
    "meal": "Meal",
    "supplement": "Supplement",
    "exercise": "Exercise",
}
TIMING_ORDER = (
    "wake-up",
    "wake up",
    "early morning",
    "empty stomach",
    "before breakfast",
    "breakfast",
    "after breakfast",
    "morning",
    "mid-morning",
    "mid morning",
    "before lunch",
    "lunch",
    "after lunch",
    "midday",
    "afternoon",
    "evening snack",
    "before dinner",
    "dinner",
    "after dinner",
    "evening",
    "night",
    "before bed",
    "bedtime",
)


def _clean(value: Any) -> str:
    return str(value or "").strip()


def _esc(value: Any) -> str:
    return html.escape(_clean(value))


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(value or default)
    except Exception:
        return default


def _parse_date(value: Any) -> dt.date | None:
    text = _clean(value)[:10]
    if not text:
        return None
    try:
        return dt.date.fromisoformat(text)
    except ValueError:
        return None


def _snapshot(row: dict[str, Any]) -> dict[str, Any]:
    raw_snapshot = row.get("source_snapshot") or {}
    if isinstance(raw_snapshot, str):
        try:
            raw_snapshot = json.loads(raw_snapshot)
        except (TypeError, ValueError):
            raw_snapshot = {}
    snapshot = dict(raw_snapshot) if isinstance(raw_snapshot, dict) else {}
    raw_original = snapshot.get("source_original_snapshot") or {}
    if isinstance(raw_original, str):
        try:
            raw_original = json.loads(raw_original)
        except (TypeError, ValueError):
            raw_original = {}
    original = dict(raw_original) if isinstance(raw_original, dict) else {}
    return original or snapshot


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


def _member_local_now(member_id: str) -> dt.datetime:
    timezone_name = member_timezone_name(member_id, persist=False)
    try:
        return dt.datetime.now(ZoneInfo(timezone_name))
    except (ZoneInfoNotFoundError, ValueError):
        return dt.datetime.now(ZoneInfo(DEFAULT_MEMBER_TIMEZONE))


def _inject_current_plan_styles() -> None:
    st.markdown(
        """
        <style id="hm-current-member-plan-v2">
        .hm-plan-view-note{display:inline-flex;align-items:center;border:1px solid #D9C28F;border-radius:999px;background:#FFF9EC;color:#72551A;padding:.24rem .56rem;margin:.20rem 0 .58rem;font-size:.72rem;font-weight:850;}
        .hm-plan-day-head{display:flex;align-items:center;justify-content:space-between;gap:.7rem;flex-wrap:wrap;margin:.18rem 0 .58rem;}
        .hm-plan-day-title{color:#064E3B;font-size:1.02rem;font-weight:950;}.hm-plan-day-sub{color:#64748B;font-size:.78rem;font-weight:720;}
        .hm-plan-period{border:1px solid #E7D8BE;border-radius:15px;background:#FFFDF8;padding:.58rem .68rem;margin:.34rem 0 .48rem;}
        .hm-plan-period.current{border-color:#D8A84E;background:linear-gradient(135deg,#FFFDF8,#FFF5DF);box-shadow:0 6px 15px rgba(6,78,59,.05);}
        .hm-plan-period-head{display:flex;align-items:center;justify-content:space-between;gap:.55rem;color:#72551A;font-size:.79rem;font-weight:950;margin:0 0 .30rem;}
        .hm-plan-now{display:inline-flex;border:1px solid #B8DCCF;border-radius:999px;background:#ECFDF5;color:#065F46;padding:.10rem .38rem;font-size:.62rem;font-weight:950;}
        .hm-plan-item{display:grid;grid-template-columns:5.3rem minmax(0,1fr);gap:.48rem;padding:.37rem .08rem;border-top:1px solid #EFE4CE;}
        .hm-plan-item:first-of-type{border-top:0;}.hm-plan-domain{display:inline-flex;align-items:flex-start;color:#72551A;font-size:.67rem;font-weight:950;line-height:1.25;padding-top:.08rem;}
        .hm-plan-item-title{color:#064E3B;font-size:.81rem;font-weight:930;line-height:1.30;}.hm-plan-item-meta{color:#475569;font-size:.70rem;font-weight:720;line-height:1.34;margin-top:.08rem;}.hm-plan-item-instruction{color:#64748B;font-size:.68rem;line-height:1.34;margin-top:.10rem;}
        .hm-plan-empty{border:1px dashed #D9C28F;border-radius:14px;background:#FFFDF8;color:#64748B;padding:.68rem .74rem;margin:.30rem 0 .56rem;font-size:.78rem;font-weight:720;line-height:1.38;}
        .hm-plan-week-intro{color:#475569;font-size:.80rem;font-weight:720;line-height:1.42;margin:.10rem 0 .62rem;}
        div[class*="st-key-hm_member_plan_day_toggle_"]{margin:.34rem 0 .18rem!important;}
        div[class*="st-key-hm_member_plan_day_toggle_"] [data-testid="stButton"]>button{
          width:100%!important;min-height:2.65rem!important;height:auto!important;
          justify-content:flex-start!important;text-align:left!important;padding:.46rem .72rem!important;
          border:1px solid #E3C98E!important;border-radius:14px!important;background:#FFFDF8!important;
          color:#064E3B!important;font-weight:920!important;
        }
        div[class*="st-key-hm_member_plan_day_toggle_"] [data-testid="stButton"]>button p{
          width:100%!important;white-space:nowrap!important;overflow:hidden!important;
          text-overflow:ellipsis!important;word-break:keep-all!important;text-align:left!important;
        }
        div[class*="st-key-hm_member_plan_day_toggle_"][class*="_today"] [data-testid="stButton"]>button{
          border-color:#D8A84E!important;background:#FFF6E5!important;
        }
        div[data-testid="stVerticalBlockBorderWrapper"]:has(.hm-plan-day-body-anchor){
          border:1px solid #E3C98E!important;border-radius:14px!important;background:#FFFFFF!important;
          padding:.36rem .52rem .42rem!important;margin:0 0 .42rem!important;
        }
        .hm-plan-day-body-anchor{display:none!important;height:0!important;margin:0!important;padding:0!important;}
        .hm-plan-action-anchor{display:none!important;height:0!important;margin:0!important;padding:0!important;}
        div[data-testid="stElementContainer"]:has(.hm-plan-action-anchor)+div[data-testid="stHorizontalBlock"]{
          gap:.72rem!important;margin:.12rem 0 .24rem!important;
        }
        div[data-testid="stElementContainer"]:has(.hm-plan-action-anchor)+div[data-testid="stHorizontalBlock"] button{
          min-height:2.48rem!important;height:2.48rem!important;border-radius:12px!important;
        }
        .hm-rec-section-title{color:#72551A;font-size:.92rem;font-weight:950;margin:.70rem 0 .38rem;}
        .hm-rec-empty{border:1px dashed #D9C28F;background:#FFF9EC;border-radius:14px;padding:.72rem;color:#64748B;font-size:.80rem;font-weight:740;line-height:1.4;}
        .hm-guidance-box{border:1px solid #E3C98E;background:#FFFDF8;border-radius:16px;padding:.66rem .72rem;box-shadow:0 6px 15px rgba(15,23,42,.035);}
        .hm-chip-row{display:flex;flex-wrap:wrap;gap:.30rem .34rem;margin:.16rem 0;}
        .hm-chip{display:inline-flex;align-items:center;gap:.28rem;border:1px solid #D9C28F;background:#FFF9EC;color:#334155;border-radius:999px;padding:.20rem .46rem;font-size:.72rem;font-weight:760;line-height:1.25;max-width:100%;}
        .hm-chip b{color:#064E3B;font-weight:950;margin-right:.10rem;}
        @media(max-width:700px){.hm-plan-item{grid-template-columns:4.6rem minmax(0,1fr);gap:.34rem}.hm-plan-period{padding:.52rem .58rem}.hm-plan-item-title{font-size:.78rem}}
        </style>
        """,
        unsafe_allow_html=True,
    )


def _row_effective_on(row: dict[str, Any], target: dt.date) -> bool:
    start = _parse_date(row.get("start_date"))
    end = _parse_date(row.get("end_date"))
    return not ((start and target < start) or (end and target > end))


def _allocation_rows_for_date(
    model: dict[str, Any],
    domain: str,
    target: dt.date,
) -> list[dict[str, Any]]:
    partitions = dict(model.get(domain) or {})
    rows = list(partitions.get("current") or []) + list(
        partitions.get("upcoming") or []
    )
    return [dict(row or {}) for row in rows if _row_effective_on(row, target)]


def _split_timings(value: Any) -> list[str]:
    values = [
        part.strip()
        for part in re.split(r"[,;|]", _clean(value))
        if part.strip()
    ]
    meaningful = [
        value
        for value in values
        if value.casefold() not in {"none", "not set", "n/a", "na"}
    ]
    return meaningful or ["Anytime / as advised"]


def _period_for_timing(value: Any) -> str:
    text = _clean(value).casefold()
    if any(token in text for token in ("bed", "night", "sleep")):
        return "Night"
    if any(
        token in text
        for token in (
            "evening",
            "dinner",
            "sunset",
        )
    ):
        return "Evening"
    if any(
        token in text
        for token in (
            "mid-morning",
            "mid morning",
            "lunch",
            "midday",
            "afternoon",
        )
    ):
        return "Midday"
    if any(
        token in text
        for token in (
            "wake",
            "morning",
            "breakfast",
            "empty stomach",
        )
    ):
        return "Morning"
    return "Anytime"


def _timing_rank(value: Any) -> int:
    text = _clean(value).casefold()
    for index, token in enumerate(TIMING_ORDER):
        if token in text:
            return index
    return len(TIMING_ORDER) + 1


def _meal_items(
    meals: list[dict[str, Any]],
    day_number: int,
) -> list[dict[str, str]]:
    output: list[dict[str, str]] = []
    for row in meals:
        if _safe_int(row.get("day_number")) != day_number:
            continue
        snapshot = _snapshot(row)
        timing = _clean(row.get("slot_name") or row.get("scheduled_time")) or (
            "Anytime / as advised"
        )
        food = _clean(row.get("reference_label")) or "Meal"
        portion = _clean(row.get("portion"))
        title = f"{food} - {portion}" if portion else food
        meta = " · ".join(
            value
            for value in (
                (
                    f"Prep {_clean(snapshot.get('prep_time'))}"
                    if _clean(snapshot.get("prep_time"))
                    else ""
                ),
            )
            if value
        )
        output.append(
            {
                "domain": "meal",
                "title": title,
                "timing": timing,
                "period": _period_for_timing(timing),
                "meta": meta,
                "instruction": _clean(row.get("instruction")),
                "order": f"{_timing_rank(timing):04d}-{_safe_int(row.get('item_order'), 0):04d}",
            }
        )
    return output


def _meal_week_cell(meals: list[dict[str, Any]], day_number: int, slot: str) -> str:
    rows = [
        row
        for row in meals
        if _safe_int(row.get("day_number")) == day_number
        and _clean(row.get("slot_name") or row.get("scheduled_time")) == slot
    ]
    rows.sort(key=lambda row: _safe_int(row.get("item_order"), 0))
    values: list[str] = []
    for row in rows:
        food = _clean(row.get("reference_label"))
        portion = _clean(row.get("portion"))
        label = f"{food} - {portion}" if food and portion else food or portion
        if label and label not in values:
            values.append(label)
    return " + ".join(values)


def _render_meal_week_grid(
    meals: list[dict[str, Any]],
    dates: list[tuple[int, dt.date]],
) -> None:
    slots = (
        "Breakfast",
        "Mid-morning Snack",
        "Lunch",
        "Evening Snack / Tea",
        "Dinner",
        "Bedtime",
    )
    header_html = "".join(f"<th>{_esc(slot)}</th>" for slot in slots)
    row_html = []
    for day_number, target_date in dates:
        cells = "".join(
            f"<td>{_esc(_meal_week_cell(meals, day_number, slot)) or '&mdash;'}</td>"
            for slot in slots
        )
        row_html.append(
            "<tr>"
            f"<td><b>Day {day_number}</b><span>{_esc(target_date.strftime('%a, %d %b'))}</span></td>"
            f"{cells}</tr>"
        )
    st.markdown(
        """
<style id="hm-member-weekly-meal-grid-v1">
.hm-week-meal-title{color:#064E3B;font-size:.96rem;font-weight:950;margin:.62rem 0 .32rem}
.hm-week-meal-wrap{overflow-x:auto;border:1px solid #E3C98E;border-radius:14px;background:#FFFDF8;margin:.20rem 0 .84rem}
.hm-week-meal-table{width:100%;min-width:920px;border-collapse:collapse;font-size:.76rem;line-height:1.34}
.hm-week-meal-table th{background:#FFF4DE;color:#064E3B;font-weight:950;text-align:center;padding:.46rem .48rem;border:1px solid #E3C98E;white-space:nowrap}
.hm-week-meal-table td{color:#334155;font-weight:730;vertical-align:top;padding:.50rem .52rem;border:1px solid #F0E3C5}
.hm-week-meal-table td:first-child{color:#064E3B;font-weight:900;white-space:nowrap;background:#FFFCF5}
.hm-week-meal-table td:first-child span{display:block;color:#64748B;font-size:.68rem;font-weight:720;margin-top:.08rem}
</style>
        """,
        unsafe_allow_html=True,
    )
    st.markdown(
        "<div class='hm-week-meal-title'>Meals</div>"
        "<div class='hm-week-meal-wrap'><table class='hm-week-meal-table'>"
        f"<thead><tr><th>Day</th>{header_html}</tr></thead>"
        f"<tbody>{''.join(row_html)}</tbody></table></div>",
        unsafe_allow_html=True,
    )


def _supplement_items(
    rows: list[dict[str, Any]],
) -> list[dict[str, str]]:
    output: list[dict[str, str]] = []
    for row in rows:
        snapshot = _snapshot(row)
        timing_value = row.get("timing") or snapshot.get("timing")
        for timing in _split_timings(timing_value):
            meta = " · ".join(
                value
                for value in (
                    _clean(row.get("dosage") or snapshot.get("dosage")),
                    _clean(row.get("frequency") or snapshot.get("frequency")),
                )
                if value
            )
            output.append(
                {
                    "domain": "supplement",
                    "title": _clean(
                        row.get("supplement_name")
                        or row.get("title")
                        or snapshot.get("supplement_name")
                        or snapshot.get("title")
                    )
                    or "Supplement",
                    "timing": timing,
                    "period": _period_for_timing(timing),
                    "meta": meta or "Dosage as advised",
                    "instruction": _clean(
                        row.get("instructions") or snapshot.get("instructions")
                    ),
                    "order": f"{_timing_rank(timing):04d}-{_clean(timing).casefold()}",
                }
            )
    return output


def _exercise_items(rows: list[dict[str, Any]]) -> list[dict[str, str]]:
    output: list[dict[str, str]] = []
    for row in rows:
        snapshot = _snapshot(row)
        timing_value = row.get("timing") or snapshot.get("timing")
        for timing in _split_timings(timing_value):
            meta = " · ".join(
                value
                for value in (
                    _clean(snapshot.get("duration_or_reps")),
                    _clean(snapshot.get("equipment")),
                )
                if value
            )
            output.append(
                {
                    "domain": "exercise",
                    "title": _clean(
                        row.get("exercise_name")
                        or row.get("title")
                        or snapshot.get("title")
                    )
                    or "Exercise",
                    "timing": timing,
                    "period": _period_for_timing(timing),
                    "meta": meta or "Duration / repetitions as advised",
                    "instruction": _clean(
                        row.get("instructions") or snapshot.get("instructions")
                    ),
                    "order": f"{_timing_rank(timing):04d}-{_clean(timing).casefold()}",
                }
            )
    return output


def build_day_timeline(
    model: dict[str, Any],
    *,
    day_number: int,
    target_date: dt.date,
    domains: tuple[str, ...] = ("meal", "supplement", "exercise"),
) -> OrderedDict[str, list[dict[str, str]]]:
    """Build one member-safe, chronological day view from the three authorities."""

    items: list[dict[str, str]] = []
    if "meal" in domains:
        items.extend(_meal_items(list(model.get("meals") or []), day_number))
    if "supplement" in domains:
        items.extend(
            _supplement_items(
                _allocation_rows_for_date(model, "supplement", target_date)
            )
        )
    if "exercise" in domains:
        items.extend(
            _exercise_items(_allocation_rows_for_date(model, "exercise", target_date))
        )
    domain_order = {"meal": 0, "supplement": 1, "exercise": 2}
    items.sort(
        key=lambda row: (
            PERIOD_ORDER.index(row["period"]),
            row.get("order", ""),
            domain_order.get(row.get("domain", ""), 9),
            row.get("title", "").casefold(),
        )
    )
    grouped: OrderedDict[str, list[dict[str, str]]] = OrderedDict()
    for period in PERIOD_ORDER:
        period_items = [row for row in items if row.get("period") == period]
        if period_items:
            grouped[period] = period_items
    return grouped


def _current_period(local_now: dt.datetime) -> str:
    hour = local_now.hour
    if hour < 11:
        return "Morning"
    if hour < 16:
        return "Midday"
    if hour < 20:
        return "Evening"
    return "Night"


def _render_timeline_item(row: dict[str, str]) -> str:
    instruction = _clean(row.get("instruction"))
    timing = _clean(row.get("timing"))
    meta = " · ".join(
        value for value in (timing, _clean(row.get("meta"))) if value
    )
    instruction_html = (
        f"<div class='hm-plan-item-instruction'>{_esc(instruction)}</div>"
        if instruction
        else ""
    )
    return (
        "<div class='hm-plan-item'>"
        f"<span class='hm-plan-domain'>{_esc(DOMAIN_LABELS.get(row.get('domain', ''), 'Plan'))}</span>"
        "<div>"
        f"<div class='hm-plan-item-title'>{_esc(row.get('title'))}</div>"
        f"<div class='hm-plan-item-meta'>{_esc(meta)}</div>"
        f"{instruction_html}"
        "</div></div>"
    )


def _render_day_timeline(
    grouped: OrderedDict[str, list[dict[str, str]]],
    *,
    active_period: str = "",
    empty_message: str = "No meal, supplement or exercise is scheduled for this day.",
) -> None:
    if not grouped:
        st.markdown(
            f"<div class='hm-plan-empty'>{_esc(empty_message)}</div>",
            unsafe_allow_html=True,
        )
        return
    for period, rows in grouped.items():
        current_class = " current" if period == active_period else ""
        now_badge = "<span class='hm-plan-now'>Current period</span>" if current_class else ""
        st.markdown(
            (
                f"<div class='hm-plan-period{current_class}'>"
                f"<div class='hm-plan-period-head'><span>{_esc(period)}</span>{now_badge}</div>"
                + "".join(_render_timeline_item(row) for row in rows)
                + "</div>"
            ),
            unsafe_allow_html=True,
        )


def _render_warnings(model: dict[str, Any]) -> None:
    warnings = [str(value) for value in model.get("warnings", []) if value]
    if warnings:
        st.warning(" ".join(warnings))


def _render_view_note() -> None:
    st.markdown(
        "<div class='hm-plan-view-note'>View only · Updates are managed by your nutritionist</div>",
        unsafe_allow_html=True,
    )


def _cycle_dates(
    profile: dict[str, Any],
    today: dt.date,
) -> tuple[int, list[tuple[int, dt.date]]]:
    current_day = today_day_number(profile, today=today) if profile else 1
    cycle_start = today - dt.timedelta(days=current_day - 1)
    return current_day, [
        (day, cycle_start + dt.timedelta(days=day - 1))
        for day in range(1, 8)
    ]


def _toggle_day_disclosure(state_key: str) -> None:
    st.session_state[state_key] = not bool(st.session_state.get(state_key))


def render_current_member_plan_view() -> None:
    _inject_current_plan_styles()
    ok, model, message = _load_model()
    if not ok:
        st.error(message)
        return
    _render_warnings(model)
    _render_view_note()
    if not model.get("has_content"):
        st.markdown(
            "<div class='hm-plan-empty'>No current plan has been allocated yet.</div>",
            unsafe_allow_html=True,
        )
        return

    member_id = _clean(model.get("member_id"))
    today = member_local_today(member_id)
    profile = dict(model.get("meal_profile") or {})
    current_day, dates = _cycle_dates(profile, today)
    st.markdown(
        "<div class='hm-plan-week-intro'>Your weekly meals are shown first. Open any day below to see Supplements and Exercise in the order they apply.</div>",
        unsafe_allow_html=True,
    )
    _render_meal_week_grid(list(model.get("meals") or []), dates)
    st.markdown(
        "<div class='hm-week-meal-title'>Supplements & Exercise</div>",
        unsafe_allow_html=True,
    )

    for day_number, target_date in dates:
        is_today = day_number == current_day
        label = (
            f"Day {day_number} · {target_date.strftime('%a, %d %b')}"
            + (" · Today" if is_today else "")
        )
        state_key = f"hm_member_plan_day_open_{target_date.isoformat()}"
        st.session_state.setdefault(state_key, is_today)
        is_open = bool(st.session_state.get(state_key))
        marker = "−" if is_open else "+"
        toggle_suffix = "_today" if is_today else ""
        with st.container(
            key=(
                f"hm_member_plan_day_toggle_{day_number}_"
                f"{target_date.isoformat()}{toggle_suffix}"
            )
        ):
            st.button(
                f"{marker}  {label}",
                key=f"hm_member_plan_day_button_{target_date.isoformat()}",
                use_container_width=True,
                on_click=_toggle_day_disclosure,
                args=(state_key,),
            )
        if is_open:
            with st.container(border=True):
                st.markdown(
                    "<span class='hm-plan-day-body-anchor'></span>",
                    unsafe_allow_html=True,
                )
                _render_day_timeline(
                    build_day_timeline(
                        model,
                        day_number=day_number,
                        target_date=target_date,
                        domains=("supplement", "exercise"),
                    ),
                    active_period=(
                        _current_period(_member_local_now(member_id))
                        if is_today
                        else ""
                    ),
                    empty_message="No supplement or exercise is scheduled for this day.",
                )

    with st.expander("Nutrition Guidance", expanded=False):
        _render_member_guidance(
            profile,
            list(model.get("guidance_items") or []),
            day=None,
            title="Nutrition Guidance",
        )


def render_todays_current_plan_view() -> None:
    _inject_current_plan_styles()
    ok, model, message = _load_model()
    if not ok:
        st.error(message)
        return
    _render_warnings(model)
    _render_view_note()

    member_id = _clean(model.get("member_id"))
    local_now = _member_local_now(member_id)
    today = local_now.date()
    profile = dict(model.get("meal_profile") or {})
    day_number = today_day_number(profile, today=today) if profile else 1
    grouped = build_day_timeline(
        model,
        day_number=day_number,
        target_date=today,
    )
    st.markdown(
        (
            "<div class='hm-plan-day-head'>"
            f"<div class='hm-plan-day-title'>Today · Day {day_number} · {_esc(today.strftime('%a, %d %b'))}</div>"
            "<div class='hm-plan-day-sub'>Meals, Supplements and Exercise in one daily sequence</div>"
            "</div>"
        ),
        unsafe_allow_html=True,
    )
    _render_day_timeline(grouped, active_period=_current_period(local_now))

    _render_member_guidance(
        profile,
        list(model.get("guidance_items") or []),
        day=day_number,
        title="Nutrition Guidance",
    )
    st.divider()
    st.markdown("<span class='hm-plan-action-anchor'></span>", unsafe_allow_html=True)
    activity_col, dashboard_col = st.columns(2, gap="medium")
    with activity_col:
        if st.button(
            "Today's Activity",
            key="hm_current_plan_log_activity",
            use_container_width=True,
        ):
            st.session_state["hm_daily_log_target_tab"] = "Food Journal"
            st.switch_page("pages/18_Daily_Log.py")
    with dashboard_col:
        if st.button(
            "Dashboard",
            key="hm_current_plan_dashboard",
            use_container_width=True,
        ):
            st.switch_page("pages/02_Member_Home.py")
