from __future__ import annotations

from datetime import date, datetime
import html
import re
from typing import Any, MutableMapping


SAVED_DAYS_DEFAULT_REVISION = "food-saved-days-today-hydration-grid-v1"
SAVED_FROM_KEY = "hm_h9a4c_saved_from"
SAVED_TO_KEY = "hm_h9a4c_saved_to"
SAVED_REVISION_KEY = "_hm_food_saved_days_default_revision"

_STRUCTURED_MEALS = (
    ("Breakfast", "breakfast"),
    ("Lunch", "lunch"),
    ("Evening Snack", "evening_snack"),
    ("Dinner", "dinner"),
    ("Bedtime", "bedtime"),
)


def _text(value: object) -> str:
    return "" if value is None else str(value).strip()


def _clean(value: object) -> str:
    text = _text(value)
    normalized = re.sub(r"[\s_-]+", " ", text.lower())
    if normalized in {
        "",
        "select",
        "selected",
        "please select",
        "select option",
        "choose",
        "choose one",
        "hh",
        "mm",
        "am/pm",
    }:
        return ""
    return text


def _as_dict(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, dict) else {}


def _parse_date(value: object) -> date | None:
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    raw = _text(value)
    if not raw:
        return None
    raw = raw.split("T")[0].split(" ")[0]
    for fmt in (
        "%Y-%m-%d",
        "%Y/%m/%d",
        "%d-%m-%Y",
        "%d/%m/%Y",
        "%d %b %Y",
        "%d-%b-%Y",
    ):
        try:
            return datetime.strptime(raw, fmt).date()
        except ValueError:
            pass
    try:
        return date.fromisoformat(raw)
    except ValueError:
        return None


def initialise_food_saved_days_range(
    session_state: MutableMapping[str, object],
    today: date,
) -> None:
    """Reset stale defaults once, then preserve deliberate same-page filter changes."""

    if session_state.get(SAVED_REVISION_KEY) != SAVED_DAYS_DEFAULT_REVISION:
        session_state[SAVED_FROM_KEY] = today
        session_state[SAVED_TO_KEY] = today
        session_state[SAVED_REVISION_KEY] = SAVED_DAYS_DEFAULT_REVISION
        return

    session_state.setdefault(SAVED_FROM_KEY, today)
    session_state.setdefault(SAVED_TO_KEY, today)


def _food_items(meal: object) -> list[str]:
    meal_row = _as_dict(meal)
    items: list[str] = []
    raw_items = meal_row.get("food_items")
    if isinstance(raw_items, list):
        for raw_item in raw_items:
            item = _as_dict(raw_item)
            food = _clean(item.get("food") or item.get("name"))
            portion = _clean(
                item.get("portion_size")
                or item.get("portion")
                or item.get("quantity")
            )
            detail = ", ".join(value for value in (food, portion) if value)
            if detail:
                items.append(detail)

    if not items:
        food = _clean(
            meal_row.get("food")
            or meal_row.get("food_log")
            or meal_row.get("name")
        )
        portion = _clean(
            meal_row.get("portion_size")
            or meal_row.get("portion")
            or meal_row.get("quantity")
        )
        detail = ", ".join(value for value in (food, portion) if value)
        if detail:
            items.append(detail)
    return items


def _meal_summary(meal: object) -> str:
    meal_row = _as_dict(meal)
    items = _food_items(meal_row)
    shown_items = items[:3]
    item_text = "; ".join(shown_items)
    if len(items) > len(shown_items):
        item_text = f"{item_text} + {len(items) - len(shown_items)} more"

    time_text = _clean(meal_row.get("time"))
    if item_text and time_text:
        return f"{item_text} · {time_text}"
    if item_text:
        return item_text
    if time_text:
        return f"Recorded · {time_text}"
    if any(_clean(meal_row.get(key)) for key in ("mood", "energy", "mood_energy")):
        return "Recorded"
    return ""


def _meal_for_key(meals: dict[str, Any], key: str) -> dict[str, Any]:
    if key == "evening_snack":
        return _as_dict(
            meals.get("evening_snack")
            or meals.get("evening_snacks")
            or meals.get("evening")
        )
    if key == "bedtime":
        return _as_dict(meals.get("bedtime") or meals.get("pre_bed"))
    return _as_dict(meals.get(key))


def _other_liquids(day: dict[str, Any]) -> str:
    values: list[str] = []
    for raw_fluid in day.get("other_fluids") or []:
        fluid = _as_dict(raw_fluid)
        detail = " · ".join(
            value
            for value in (
                _clean(fluid.get("type") or fluid.get("name") or fluid.get("fluid_type")),
                _clean(fluid.get("quantity") or fluid.get("qty")),
                _clean(fluid.get("time")),
                _clean(fluid.get("notes")),
            )
            if value
        )
        if detail:
            values.append(detail)
    return "; ".join(values) if values else "No entry"


def saved_day_card_rows(day: object) -> list[tuple[str, str]]:
    """Return compact read-only meal and hydration rows for one saved day."""

    day_row = _as_dict(day)
    meals = _as_dict(day_row.get("meals"))
    rows: list[tuple[str, str]] = []

    for label, key in _STRUCTURED_MEALS:
        summary = _meal_summary(_meal_for_key(meals, key))
        if summary:
            rows.append((label, summary))

    snack_rows = []
    for key, value in meals.items():
        key_text = str(key or "").lower()
        if not (
            key_text.startswith("snacking_")
            or key_text.startswith("snack_")
            or key_text.startswith("other_snack")
        ):
            continue
        summary = _meal_summary(value)
        if summary:
            snack_rows.append((key_text, summary))
    for index, (_key, summary) in enumerate(sorted(snack_rows), start=1):
        rows.append((f"Snacking {index}", summary))

    if not rows:
        rows.append(("Meals", "No entry"))

    rows.append(("Water", _clean(day_row.get("water_litres")) or "No entry"))
    rows.append(("Other Liquids", _other_liquids(day_row)))
    return rows


def saved_day_date(day: object) -> date | None:
    day_row = _as_dict(day)
    for key in (
        "_journal_date_key",
        "date",
        "log_date",
        "journal_date",
        "food_journal_date",
    ):
        parsed = _parse_date(day_row.get(key))
        if parsed:
            return parsed
    return None


def saved_day_sort_key(day: object) -> tuple[int, str]:
    parsed = saved_day_date(day)
    return (parsed.toordinal() if parsed else 0, _text(day))


def saved_day_card_html(day: object, date_text: object = "") -> str:
    parsed = _parse_date(date_text) or saved_day_date(day)
    date_label = parsed.strftime("%a, %d %b %Y") if parsed else _text(date_text)
    row_html = "".join(
        "<div class='hm-saved-day-row'>"
        f"<span>{html.escape(label)}</span>"
        f"<strong>{html.escape(value)}</strong>"
        "</div>"
        for label, value in saved_day_card_rows(day)
    )
    return (
        "<span class='hm-saved-day-card-anchor'></span>"
        "<div class='hm-saved-day-card'>"
        f"<div class='hm-saved-day-date'>{html.escape(date_label)}</div>"
        f"{row_html}"
        "</div>"
    )


def saved_days_card_css() -> str:
    return """
    <style id="hm-food-saved-days-cards-v1">
    div[data-testid="stElementContainer"]:has(style#hm-food-saved-days-cards-v1){
      display:none!important;height:0!important;min-height:0!important;
      margin:0!important;padding:0!important;overflow:hidden!important;
    }
    .hm-saved-day-card-anchor{display:none!important;height:0!important;margin:0!important;padding:0!important;}
    div[data-testid="stVerticalBlockBorderWrapper"]:has(.hm-saved-day-card-anchor){
      height:100%!important;min-height:12rem!important;padding:.66rem .72rem!important;
      border:1px solid #E1B95E!important;border-radius:14px!important;
      background:#FFFDF8!important;box-shadow:none!important;
    }
    div[data-testid="stVerticalBlockBorderWrapper"]:has(.hm-saved-day-card-anchor)>div{
      gap:.36rem!important;padding:0!important;
    }
    .hm-saved-day-card{display:flex;flex-direction:column;gap:.27rem;min-height:8.8rem;}
    .hm-saved-day-date{color:#064E3B;font-size:.86rem;font-weight:950;margin:0 0 .18rem 0;}
    .hm-saved-day-row{display:grid;grid-template-columns:minmax(4.8rem,.42fr) minmax(0,.58fr);gap:.40rem;align-items:start;font-size:.74rem;line-height:1.30;}
    .hm-saved-day-row span{color:#7A5A16;font-weight:900;}
    .hm-saved-day-row strong{color:#334155;font-weight:520;overflow-wrap:anywhere;}
    div[data-testid="stVerticalBlockBorderWrapper"]:has(.hm-saved-day-card-anchor) button{
      min-height:2rem!important;height:2rem!important;padding:.24rem .42rem!important;
      border-radius:9px!important;font-size:.72rem!important;font-weight:850!important;
    }
    @media(max-width:900px){
      .hm-saved-day-row{grid-template-columns:minmax(4.4rem,.40fr) minmax(0,.60fr);}
    }
    </style>
    """
