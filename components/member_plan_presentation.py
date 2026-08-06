from __future__ import annotations

import json
import re
from datetime import date, datetime, timedelta
from typing import Any, Dict, Iterable, List, Sequence


MEAL_TIMINGS = (
    "Breakfast",
    "Mid-morning Snack",
    "Lunch",
    "Evening Snack / Tea",
    "Dinner",
    "Bedtime",
)

_TIMING_ORDER = (
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
    "evening",
    "before dinner",
    "dinner",
    "after dinner",
    "night",
    "bedtime",
    "before bed",
    "with food",
    "after meals",
    "as advised",
    "none",
)

_LIQUID_TOKENS = ("liquid", "beverage", "drink", "fluid")


def _clean(value: object) -> str:
    return str(value or "").strip()


def _as_dict(value: object) -> Dict[str, Any]:
    if isinstance(value, dict):
        return dict(value)
    if isinstance(value, str) and value.strip():
        try:
            parsed = json.loads(value)
            return dict(parsed) if isinstance(parsed, dict) else {}
        except Exception:
            return {}
    return {}


def _snapshot(row: Dict[str, Any]) -> Dict[str, Any]:
    snapshot = _as_dict(row.get("source_snapshot"))
    original = _as_dict(snapshot.get("source_original_snapshot"))
    return original or snapshot


def _parse_date(value: object) -> date | None:
    raw = _clean(value)
    if not raw:
        return None
    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%d-%m-%Y", "%d/%m/%Y"):
        try:
            return datetime.strptime(raw[:10], fmt).date()
        except ValueError:
            pass
    return None


def timing_sort_key(value: object) -> tuple[int, str]:
    text = _clean(value)
    lowered = text.lower()
    meal_lookup = {label.lower(): index for index, label in enumerate(MEAL_TIMINGS)}
    if lowered in meal_lookup:
        return meal_lookup[lowered], lowered
    for index, token in enumerate(_TIMING_ORDER):
        if token in lowered:
            return len(MEAL_TIMINGS) + index, lowered
    return 10_000, lowered


def split_timings(value: object) -> List[str]:
    if isinstance(value, (list, tuple, set)):
        candidates: Iterable[object] = value
    else:
        candidates = re.split(r"[,;|]", _clean(value))
    output: List[str] = []
    for candidate in candidates:
        timing = _clean(candidate)
        if timing and timing not in output:
            output.append(timing)
    return sorted(output or ["As advised"], key=timing_sort_key)


def _join(values: Iterable[object], separator: str = "\n") -> str:
    output: List[str] = []
    for value in values:
        text = _clean(value)
        if text and text not in output:
            output.append(text)
    return separator.join(output)


def _meal_label(row: Dict[str, Any]) -> str:
    item = _clean(row.get("reference_label"))
    portion = _clean(row.get("portion"))
    return f"{item} - {portion}" if item and portion else item or portion


def _is_liquid(row: Dict[str, Any]) -> bool:
    snapshot = _snapshot(row)
    source_type = " ".join(
        _clean(snapshot.get(field)) for field in ("meal_type", "category", "type")
    ).lower()
    return any(token in source_type for token in _LIQUID_TOKENS)


def meal_day_groups(items: Sequence[Dict[str, Any]], day_number: int) -> List[Dict[str, str]]:
    grouped: Dict[str, List[Dict[str, Any]]] = {}
    for row in items or []:
        if _clean(row.get("item_type")).lower() != "meal":
            continue
        if int(row.get("day_number") or 0) != day_number:
            continue
        timing = _clean(row.get("slot_name")) or "As advised"
        grouped.setdefault(timing, []).append(dict(row))

    output: List[Dict[str, str]] = []
    for timing in sorted(grouped, key=timing_sort_key):
        rows = sorted(grouped[timing], key=lambda row: int(row.get("item_order") or 1))
        output.append(
            {
                "Timing": timing,
                "Meal": _join(
                    (_meal_label(row) for row in rows if not _is_liquid(row)),
                    " + ",
                ),
                "Liquid": _join(
                    (_meal_label(row) for row in rows if _is_liquid(row)),
                    " + ",
                ),
                "Remarks": _join(row.get("instruction") for row in rows),
            }
        )
    return output


def _model_rows(model: Dict[str, Any], domain: str) -> List[Dict[str, Any]]:
    partitions = dict(model.get(domain) or {})
    output: List[Dict[str, Any]] = []
    for state in ("current", "upcoming"):
        output.extend(dict(row or {}) for row in partitions.get(state) or [])
    return output


def _row_applies_on(row: Dict[str, Any], target: date | None) -> bool:
    if target is None:
        return True
    start = _parse_date(row.get("start_date"))
    end = _parse_date(row.get("end_date"))
    return not ((start and target < start) or (end and target > end))


def allocation_day_groups(
    model: Dict[str, Any],
    domain: str,
    plan_start: object,
    day_number: int,
) -> List[Dict[str, str]]:
    parsed_start = _parse_date(plan_start)
    target = parsed_start + timedelta(days=day_number - 1) if parsed_start else None
    grouped: Dict[str, List[Dict[str, str]]] = {}

    for row in _model_rows(model, domain):
        if not _row_applies_on(row, target):
            continue
        snapshot = _snapshot(row)
        timing_value = row.get("timing") or snapshot.get("timing")
        for timing in split_timings(timing_value):
            if domain == "exercise":
                detail = {
                    "Activity": _clean(
                        row.get("exercise_name") or row.get("title") or snapshot.get("title")
                    ),
                    "Duration/Sets": _clean(snapshot.get("duration_or_reps")),
                    "Remarks": _clean(row.get("instructions") or snapshot.get("instructions")),
                }
            else:
                dosage = _clean(row.get("dosage") or snapshot.get("dosage"))
                frequency = _clean(row.get("frequency") or snapshot.get("frequency"))
                detail = {
                    "Supplement": _clean(
                        row.get("supplement_name")
                        or row.get("title")
                        or snapshot.get("supplement_name")
                        or snapshot.get("title")
                    ),
                    "Dosage": " · ".join(value for value in (dosage, frequency) if value),
                    "Remarks": _clean(row.get("instructions") or snapshot.get("instructions")),
                }
            grouped.setdefault(timing, []).append(detail)

    output: List[Dict[str, str]] = []
    for timing in sorted(grouped, key=timing_sort_key):
        rows = grouped[timing]
        if domain == "exercise":
            output.append(
                {
                    "Timing": timing,
                    "Activity": _join(row.get("Activity") for row in rows),
                    "Duration/Sets": _join(row.get("Duration/Sets") for row in rows),
                    "Reps/Duration": _join(row.get("Duration/Sets") for row in rows),
                    "Remarks": _join(row.get("Remarks") for row in rows),
                }
            )
        else:
            output.append(
                {
                    "Timing": timing,
                    "Supplement": _join(row.get("Supplement") for row in rows),
                    "Dosage": _join(row.get("Dosage") for row in rows),
                    "Remarks": _join(row.get("Remarks") for row in rows),
                }
            )
    return output


def section_rows(
    *,
    start_date: object,
    section_type: str,
    headers: Sequence[str],
    day_groups,
) -> List[Dict[str, str]]:
    output: List[Dict[str, str]] = []
    for day_number in range(1, 8):
        groups = list(day_groups(day_number) or [{}])
        for group in groups:
            output.append(
                {
                    "Start Date": _clean(start_date),
                    "Type": section_type,
                    "Day": f"Day {day_number}",
                    **{header: _clean(group.get(header)) for header in headers},
                }
            )
    return output


def profile_matches_or_filters(
    profile: Dict[str, Any],
    *,
    profile_id: object = "",
    member_id: object = "",
    health_concerns: Sequence[object] = (),
) -> bool:
    selected_profile = _clean(profile_id)
    selected_member = _clean(member_id)
    selected_concerns = {_clean(value).lower() for value in health_concerns if _clean(value)}
    tests: List[bool] = []
    if selected_profile:
        tests.append(_clean(profile.get("id")) == selected_profile)
    if selected_member:
        tests.append(_clean(profile.get("assigned_member_id")) == selected_member)
    if selected_concerns:
        row_concerns = {
            _clean(value).lower()
            for value in profile.get("health_concerns") or []
            if _clean(value)
        }
        tests.append(bool(row_concerns & selected_concerns))
    return any(tests) if tests else True
