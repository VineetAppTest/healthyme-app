from __future__ import annotations

import contextlib
import datetime as dt
import functools
import html
import inspect
from zoneinfo import ZoneInfo

import streamlit as st


_MARKER = "_hm_member_saved_days_home_cleanup_v2"
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


def _frame_file(frame) -> str:
    return str((frame.f_globals if frame is not None else {}).get("__file__") or "").replace("\\", "/")


def _frame_function(frame) -> str:
    return str((frame.f_code.co_name if frame is not None else "") or "")


def _is_daily_log_frame(frame) -> bool:
    page_file = _frame_file(frame)
    return page_file.endswith("/pages/18_Daily_Log.py") or page_file.endswith("pages/18_Daily_Log.py")


def _is_member_home_frame(frame) -> bool:
    page_file = _frame_file(frame)
    return page_file.endswith("/pages/02_Member_Home.py") or page_file.endswith("pages/02_Member_Home.py")


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

    snack_items: list[str] = []
    for key, meal in meals.items():
        key_text = str(key or "").lower()
        if not (key_text.startswith("snacking_") or key_text.startswith("snack_")):
            continue
        for item in _food_items(meal):
            if item not in snack_items:
                snack_items.append(item)
    if snack_items:
        rows.append(("Snacking", ", ".join(snack_items)))
    return rows


def _render_filtered_meal_summary(days: list[dict]) -> None:
    dated_days = sorted(
        (
            (day_date, row)
            for row in days
            if isinstance(row, dict)
            for day_date in [_saved_date(row)]
            if day_date is not None
        ),
        key=lambda item: item[0],
        reverse=True,
    )

    st.markdown(
        """
<style id="hm-filtered-meal-summary-v2">
.hm-saved-meal-section-title{color:#064E3B;font-size:.96rem;font-weight:950;margin:.18rem 0 .48rem 0;}
.hm-saved-meal-window{display:grid;grid-template-columns:1fr;gap:.46rem;margin:.05rem 0 .25rem 0;}
.hm-saved-meal-day{border:1px solid #E3C98E;background:linear-gradient(180deg,#FFFDF8,#FFF9EC);border-radius:14px;padding:.62rem .72rem;}
.hm-saved-meal-date{color:#064E3B;font-size:.87rem;font-weight:950;margin-bottom:.26rem;}
.hm-saved-meal-line{display:grid;grid-template-columns:8.4rem minmax(0,1fr);gap:.55rem;color:#334155;font-size:.80rem;line-height:1.36;margin:.10rem 0;}
.hm-saved-meal-label{color:#72551A;font-weight:850;}
.hm-saved-meal-empty{color:#64748B;font-size:.79rem;font-weight:720;}
@media(max-width:640px){.hm-saved-meal-line{grid-template-columns:1fr;gap:.05rem}.hm-saved-meal-day{padding:.58rem .62rem}}
</style>
<div class="hm-saved-meal-section-title">Meal Section</div>
        """,
        unsafe_allow_html=True,
    )

    cards: list[str] = []
    for day_date, day in dated_days:
        rows = _meal_rows(day)
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
    """Retired compatibility hook.

    Saved Days now owns its date defaults, four-column cards, hydration rows and
    Open saved day action directly in ``pages/18_Daily_Log.py``. The former runtime
    wrapper injected a second Meal Section, forced the four-column grid into one
    column and intercepted the Open action. Keep this function as a no-op because
    older bootstraps still import and call it.
    """

    return None


def _install_member_home_cleanup() -> None:
    """Suppress only the retired KPI strip; page sections own their layout."""

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



def install_member_saved_days_home_cleanup() -> None:
    _install_saved_days_window()
    _install_member_home_cleanup()
