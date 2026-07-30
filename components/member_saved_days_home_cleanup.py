from __future__ import annotations

import contextlib
import datetime as dt
import functools
import html
import inspect
from zoneinfo import ZoneInfo

import streamlit as st


_MARKER = "_hm_member_saved_days_home_cleanup_v1"
_SAVED_FROM_KEY = "hm_h9a4c_saved_from"
_SAVED_TO_KEY = "hm_h9a4c_saved_to"
_SAVED_BUTTON_PREFIX = "hm_h9a4c_load_"
_STRUCTURED_MEALS = (
    ("Breakfast", "breakfast"),
    ("Lunch", "lunch"),
    ("Evening Snack", "evening_snack"),
    ("Dinner", "dinner"),
    ("Bedtime", "bedtime"),
)


def _caller_file(depth: int = 1) -> str:
    frame = inspect.currentframe()
    for _ in range(max(depth, 0) + 1):
        frame = frame.f_back if frame is not None else None
    return str((frame.f_globals if frame is not None else {}).get("__file__") or "").replace("\\", "/")


def _is_daily_log_frame(frame) -> bool:
    page_file = str((frame.f_globals if frame is not None else {}).get("__file__") or "").replace("\\", "/")
    return page_file.endswith("/pages/18_Daily_Log.py") or page_file.endswith("pages/18_Daily_Log.py")


def _india_today() -> dt.date:
    return dt.datetime.now(ZoneInfo("Asia/Kolkata")).date()


def _saved_date(row: object) -> dt.date | None:
    if not isinstance(row, dict):
        return None
    for key in ("_journal_date_key", "date", "log_date", "journal_date", "food_journal_date"):
        raw = str(row.get(key) or "").strip()
        if not raw:
            continue
        try:
            return dt.date.fromisoformat(raw[:10])
        except ValueError:
            continue
    return None


def _food_items(meal: object) -> list[str]:
    if not isinstance(meal, dict):
        return []
    values: list[str] = []
    raw_items = meal.get("food_items")
    if isinstance(raw_items, list):
        for item in raw_items:
            if not isinstance(item, dict):
                continue
            name = str(item.get("food") or item.get("name") or "").strip()
            if name and name not in values:
                values.append(name)
    if not values:
        raw = str(meal.get("food") or meal.get("food_log") or meal.get("name") or "").strip()
        for part in raw.replace(";", ",").split(","):
            clean = part.strip()
            if clean and clean not in values:
                values.append(clean)
    return values


def _meal_rows(day: dict) -> list[tuple[str, str]]:
    meals = day.get("meals") if isinstance(day.get("meals"), dict) else {}
    rows: list[tuple[str, str]] = []
    for label, key in _STRUCTURED_MEALS:
        meal = meals.get(key) or meals.get(f"{key}s") or {}
        items = _food_items(meal)
        if items:
            rows.append((label, ", ".join(items)))
    snack_rows: list[str] = []
    for key, meal in meals.items():
        key_text = str(key or "").lower()
        if not (key_text.startswith("snacking_") or key_text.startswith("snack_")):
            continue
        for item in _food_items(meal):
            if item not in snack_rows:
                snack_rows.append(item)
    if snack_rows:
        rows.append(("Snacking", ", ".join(snack_rows)))
    return rows


def _render_seven_day_meal_summary(days: list[dict]) -> None:
    today = _india_today()
    start = today - dt.timedelta(days=6)
    by_date = {
        day_date: row
        for row in days
        if isinstance(row, dict)
        for day_date in [_saved_date(row)]
        if day_date is not None and start <= day_date <= today
    }
    st.markdown(
        """
<style id="hm-seven-day-meal-summary-v1">
.hm-saved-meal-window{display:grid;grid-template-columns:1fr;gap:.46rem;margin:.15rem 0 .25rem 0;}
.hm-saved-meal-day{border:1px solid #E3C98E;background:linear-gradient(180deg,#FFFDF8,#FFF9EC);border-radius:14px;padding:.62rem .72rem;}
.hm-saved-meal-date{color:#064E3B;font-size:.87rem;font-weight:950;margin-bottom:.22rem;}
.hm-saved-meal-line{display:grid;grid-template-columns:8.4rem minmax(0,1fr);gap:.55rem;color:#334155;font-size:.80rem;line-height:1.36;margin:.10rem 0;}
.hm-saved-meal-label{color:#72551A;font-weight:850;}
.hm-saved-meal-empty{color:#64748B;font-size:.79rem;font-weight:720;}
@media(max-width:640px){.hm-saved-meal-line{grid-template-columns:1fr;gap:.05rem}.hm-saved-meal-day{padding:.58rem .62rem}}
</style>
        """,
        unsafe_allow_html=True,
    )
    cards: list[str] = []
    for offset in range(7):
        day_date = today - dt.timedelta(days=offset)
        day = by_date.get(day_date, {})
        rows = _meal_rows(day) if day else []
        if rows:
            content = "".join(
                "<div class='hm-saved-meal-line'>"
                f"<div class='hm-saved-meal-label'>{html.escape(label)}</div>"
                f"<div>{html.escape(items)}</div></div>"
                for label, items in rows
            )
        else:
            content = "<div class='hm-saved-meal-empty'>No meal entry saved.</div>"
        cards.append(
            "<div class='hm-saved-meal-day'>"
            f"<div class='hm-saved-meal-date'>{day_date.strftime('%a, %d %b %Y')}</div>"
            f"{content}</div>"
        )
    st.markdown(
        "<div class='hm-saved-meal-window'>" + "".join(cards) + "</div>",
        unsafe_allow_html=True,
    )


def _install_saved_days_window() -> None:
    current_date_input = st.date_input
    current_button = st.button
    current_columns = st.columns
    current_caption = st.caption
    if getattr(current_button, _MARKER, False):
        return

    @functools.wraps(current_date_input)
    def date_input_without_saved_filters(label, *args, **kwargs):
        caller = inspect.currentframe().f_back
        key = str(kwargs.get("key") or "")
        if _is_daily_log_frame(caller) and key in {_SAVED_FROM_KEY, _SAVED_TO_KEY}:
            today = _india_today()
            return today - dt.timedelta(days=6) if key == _SAVED_FROM_KEY else today
        return current_date_input(label, *args, **kwargs)

    @functools.wraps(current_columns)
    def columns_without_saved_filter_layout(spec, *args, **kwargs):
        caller = inspect.currentframe().f_back
        function_name = str((caller.f_code.co_name if caller is not None else "") or "")
        if _is_daily_log_frame(caller) and function_name == "_render_saved_days":
            count = spec if isinstance(spec, int) else len(spec)
            if count == 2:
                return [contextlib.nullcontext(), contextlib.nullcontext()]
            if count == 4:
                return [st.container(), contextlib.nullcontext(), contextlib.nullcontext(), contextlib.nullcontext()]
        return current_columns(spec, *args, **kwargs)

    @functools.wraps(current_caption)
    def caption_without_loading_copy(body, *args, **kwargs):
        caller = inspect.currentframe().f_back
        text = str(body or "")
        if _is_daily_log_frame(caller) and text.startswith("Showing ") and "saved day" in text:
            return None
        return current_caption(body, *args, **kwargs)

    @functools.wraps(current_button)
    def button_with_static_saved_summary(label, *args, **kwargs):
        caller = inspect.currentframe().f_back
        key = str(kwargs.get("key") or "")
        if not (_is_daily_log_frame(caller) and key.startswith(_SAVED_BUTTON_PREFIX)):
            return current_button(label, *args, **kwargs)
        filtered_days = list((caller.f_locals if caller is not None else {}).get("filtered_days") or [])
        first_date = _saved_date(filtered_days[0]) if filtered_days else None
        button_date = None
        try:
            button_date = dt.date.fromisoformat(key[len(_SAVED_BUTTON_PREFIX):][:10])
        except ValueError:
            pass
        if first_date is not None and button_date == first_date:
            _render_seven_day_meal_summary(filtered_days)
        return False

    setattr(date_input_without_saved_filters, _MARKER, True)
    setattr(columns_without_saved_filter_layout, _MARKER, True)
    setattr(caption_without_loading_copy, _MARKER, True)
    setattr(button_with_static_saved_summary, _MARKER, True)
    st.date_input = date_input_without_saved_filters
    st.columns = columns_without_saved_filter_layout
    st.caption = caption_without_loading_copy
    st.button = button_with_static_saved_summary


def _install_member_home_cleanup() -> None:
    from components import ui_common

    current_stat_grid = ui_common.stat_grid
    if not getattr(current_stat_grid, _MARKER, False):
        @functools.wraps(current_stat_grid)
        def stat_grid_without_member_home(*args, **kwargs):
            caller = inspect.currentframe().f_back
            if _is_member_home_frame(caller):
                return None
            return current_stat_grid(*args, **kwargs)

        setattr(stat_grid_without_member_home, _MARKER, True)
        ui_common.stat_grid = stat_grid_without_member_home

    current_topbar = ui_common.topbar
    if not getattr(current_topbar, _MARKER, False):
        @functools.wraps(current_topbar)
        def topbar_with_member_home_two_column_content(title, *args, **kwargs):
            result = current_topbar(title, *args, **kwargs)
            if str(title or "").strip() == "Member Home":
                st.markdown(
                    """
<style id="hm-member-home-message-schedule-layout-v1">
.hm-b13-message-shell{float:right!important;width:47%!important;max-width:460px!important;margin:.45rem 0 .85rem 0!important;padding:0!important;border:0!important;background:transparent!important;box-shadow:none!important;}
.hm-b13-message-title{display:flex!important;align-items:center!important;width:285px!important;min-height:2.45rem!important;padding:.42rem .72rem!important;border:1.35px solid #D8A84E!important;border-radius:999px!important;background:#FFFDF8!important;color:#064E3B!important;font-size:.88rem!important;font-weight:950!important;margin:0 0 .52rem 0!important;white-space:nowrap!important;}
.hm-b13-message-card{width:100%!important;margin:.42rem 0!important;border-radius:15px!important;padding:.66rem .72rem!important;}
div[data-testid="stExpander"]:has(.hm-upcoming-schedule-anchor){float:left!important;width:47%!important;max-width:460px!important;margin:.45rem 0 .85rem 0!important;}
div[data-testid="stExpander"]:has(.hm-upcoming-schedule-anchor) .hm-v101-schedule-card{width:100%!important;max-width:none!important;margin:.42rem 0!important;}
div[data-testid="stHorizontalBlock"]:has(.hm-member-home-balanced-card){clear:both!important;}
@media(max-width:780px){.hm-b13-message-shell,div[data-testid="stExpander"]:has(.hm-upcoming-schedule-anchor){float:none!important;width:100%!important;max-width:none!important}.hm-b13-message-title{width:100%!important}}
</style>
                    """,
                    unsafe_allow_html=True,
                )
            return result

        setattr(topbar_with_member_home_two_column_content, _MARKER, True)
        ui_common.topbar = topbar_with_member_home_two_column_content


def _is_member_home_frame(frame) -> bool:
    page_file = str((frame.f_globals if frame is not None else {}).get("__file__") or "").replace("\\", "/")
    return page_file.endswith("/pages/02_Member_Home.py") or page_file.endswith("pages/02_Member_Home.py")


def install_member_saved_days_home_cleanup() -> None:
    _install_saved_days_window()
    _install_member_home_cleanup()
