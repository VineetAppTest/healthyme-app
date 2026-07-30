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
    current_date_input = st.date_input
    current_button = st.button
    current_columns = st.columns
    current_markdown = st.markdown
    if getattr(current_button, _MARKER, False):
        return

    summary_state = {"rendered": False}

    @functools.wraps(current_date_input)
    def date_input_with_visible_saved_filters(label, *args, **kwargs):
        caller = inspect.currentframe().f_back
        key = str(kwargs.get("key") or "")
        if _is_daily_log_frame(caller) and _frame_function(caller) == "_render_saved_days":
            today = _india_today()
            if key == _SAVED_FROM_KEY:
                st.session_state.setdefault(key, today - dt.timedelta(days=6))
            elif key == _SAVED_TO_KEY:
                st.session_state.setdefault(key, today)
        return current_date_input(label, *args, **kwargs)

    @functools.wraps(current_columns)
    def columns_with_full_width_saved_summary(spec, *args, **kwargs):
        caller = inspect.currentframe().f_back
        if _is_daily_log_frame(caller) and _frame_function(caller) == "_render_saved_days":
            count = spec if isinstance(spec, int) else len(spec)
            if count == 4:
                return [st.container(), contextlib.nullcontext(), contextlib.nullcontext(), contextlib.nullcontext()]
        return current_columns(spec, *args, **kwargs)

    @functools.wraps(current_markdown)
    def markdown_with_saved_summary_reset(body, *args, **kwargs):
        caller = inspect.currentframe().f_back
        if (
            _is_daily_log_frame(caller)
            and _frame_function(caller) == "_render_saved_days"
            and str(body or "").strip() == "### View Saved Days"
        ):
            summary_state["rendered"] = False
        return current_markdown(body, *args, **kwargs)

    @functools.wraps(current_button)
    def button_without_saved_day_loading(label, *args, **kwargs):
        caller = inspect.currentframe().f_back
        key = str(kwargs.get("key") or "")
        if not (
            _is_daily_log_frame(caller)
            and _frame_function(caller) == "_render_saved_days"
            and key.startswith(_SAVED_BUTTON_PREFIX)
        ):
            return current_button(label, *args, **kwargs)
        if not summary_state["rendered"]:
            filtered_days = list((caller.f_locals if caller is not None else {}).get("filtered_days") or [])
            _render_filtered_meal_summary(filtered_days)
            summary_state["rendered"] = True
        return False

    setattr(date_input_with_visible_saved_filters, _MARKER, True)
    setattr(columns_with_full_width_saved_summary, _MARKER, True)
    setattr(markdown_with_saved_summary_reset, _MARKER, True)
    setattr(button_without_saved_day_loading, _MARKER, True)
    st.date_input = date_input_with_visible_saved_filters
    st.columns = columns_with_full_width_saved_summary
    st.markdown = markdown_with_saved_summary_reset
    st.button = button_without_saved_day_loading


def _install_member_home_cleanup() -> None:
    from components import ui_common

    current_columns = st.columns
    current_markdown = st.markdown
    current_button = st.button
    current_expander = st.expander
    home_columns = {"pair": None}

    def ensure_home_columns():
        if home_columns["pair"] is None:
            left, right = current_columns([1, 1], gap="large")
            left.markdown("<span class='hm-home-side-col-anchor'></span>", unsafe_allow_html=True)
            right.markdown("<span class='hm-home-side-col-anchor'></span>", unsafe_allow_html=True)
            home_columns["pair"] = (left, right)
        return home_columns["pair"]

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
        def topbar_with_member_home_columns(title, *args, **kwargs):
            if str(title or "").strip() == "Member Home":
                home_columns["pair"] = None
            result = current_topbar(title, *args, **kwargs)
            if str(title or "").strip() == "Member Home":
                current_markdown(
                    """
<style id="hm-member-home-message-schedule-layout-v2">
.hm-home-side-col-anchor{display:none!important;height:0!important;margin:0!important;padding:0!important;}
div[data-testid="stHorizontalBlock"]:has(.hm-home-side-col-anchor){align-items:flex-start!important;gap:1.25rem!important;margin:.42rem 0 .82rem 0!important;}
.hm-b13-message-shell{float:none!important;width:100%!important;max-width:none!important;margin:0!important;padding:0!important;border:0!important;background:transparent!important;box-shadow:none!important;}
.hm-b13-message-title{display:flex!important;align-items:center!important;width:285px!important;min-height:2.45rem!important;padding:.42rem .72rem!important;border:1.35px solid #D8A84E!important;border-radius:999px!important;background:#FFFDF8!important;color:#064E3B!important;font-size:.88rem!important;font-weight:950!important;margin:0 0 .52rem 0!important;white-space:nowrap!important;}
.hm-b13-message-card{width:100%!important;margin:.42rem 0!important;border-radius:15px!important;padding:.66rem .72rem!important;}
div[data-testid="stExpander"]:has(.hm-upcoming-schedule-anchor){float:none!important;width:100%!important;max-width:none!important;margin:0!important;}
div[data-testid="stExpander"]:has(.hm-upcoming-schedule-anchor) .hm-v101-schedule-card{width:100%!important;max-width:none!important;margin:.42rem 0!important;}
@media(max-width:900px){div[data-testid="stHorizontalBlock"]:has(.hm-home-side-col-anchor){display:flex!important;flex-direction:column!important;gap:.8rem!important;}div[data-testid="stHorizontalBlock"]:has(.hm-home-side-col-anchor)>div{width:100%!important;min-width:100%!important}.hm-b13-message-title{width:100%!important}}
</style>
                    """,
                    unsafe_allow_html=True,
                )
            return result

        setattr(topbar_with_member_home_columns, _MARKER, True)
        ui_common.topbar = topbar_with_member_home_columns

    if not getattr(current_markdown, _MARKER, False):
        @functools.wraps(current_markdown)
        def markdown_in_member_home_column(body, *args, **kwargs):
            caller = inspect.currentframe().f_back
            if _is_member_home_frame(caller) and _frame_function(caller) == "_render_messages":
                _, right = ensure_home_columns()
                return right.markdown(body, *args, **kwargs)
            return current_markdown(body, *args, **kwargs)

        setattr(markdown_in_member_home_column, _MARKER, True)
        st.markdown = markdown_in_member_home_column

    if not getattr(current_button, _MARKER, False):
        @functools.wraps(current_button)
        def button_in_member_home_column(label, *args, **kwargs):
            caller = inspect.currentframe().f_back
            if _is_member_home_frame(caller) and _frame_function(caller) == "_render_messages":
                _, right = ensure_home_columns()
                return right.button(label, *args, **kwargs)
            return current_button(label, *args, **kwargs)

        setattr(button_in_member_home_column, _MARKER, True)
        st.button = button_in_member_home_column

    if not getattr(current_expander, _MARKER, False):
        @functools.wraps(current_expander)
        def expander_in_member_home_column(label, *args, **kwargs):
            caller = inspect.currentframe().f_back
            if _is_member_home_frame(caller) and _frame_function(caller) == "_render_upcoming_schedules":
                if home_columns["pair"] is not None:
                    left, _ = ensure_home_columns()
                    return left.expander(label, *args, **kwargs)
            return current_expander(label, *args, **kwargs)

        setattr(expander_in_member_home_column, _MARKER, True)
        st.expander = expander_in_member_home_column


def install_member_saved_days_home_cleanup() -> None:
    _install_saved_days_window()
    _install_member_home_cleanup()
