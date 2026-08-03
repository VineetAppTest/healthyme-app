from __future__ import annotations

import copy
import datetime as dt
from typing import Any, Callable

from components.exercise_member_allocation import (
    ACTIVE_STATUS as EXERCISE_ACTIVE_STATUS,
    list_member_exercise_allocations,
)
from components.storage_backend import load_state
from components import supplement_member_allocation as supplement_allocation


READ_MODEL_VERSION = "2026-08-04-v1"
MEAL_ITEM_TYPE = "meal"
GUIDANCE_ITEM_TYPES = {"guidance", "nutrition_guidance", "nutrition"}


def _default_profile_loader(
    member_id: str,
    email: str,
) -> tuple[bool, dict, list, str]:
    from components.member_recommendation_split_display import (
        load_active_recommendation_profile,
    )

    return load_active_recommendation_profile(member_id, email)


def _profile_row_has_content(row: dict[str, Any]) -> bool:
    return any(
        _clean(row.get(field))
        for field in (
            "reference_label",
            "portion",
            "instruction",
            "scheduled_time",
            "intensity",
            "dosage_frequency",
        )
    )


def _active_profile_items(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        row
        for row in items
        if isinstance(row, dict) and _profile_row_has_content(row)
    ]


def _clean(value: Any) -> str:
    return str(value or "").strip()


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
    except Exception:
        return None


def _effective_state(
    row: dict[str, Any],
    *,
    today: dt.date,
    active_status: str,
) -> str:
    if _clean(row.get("status")).lower() != _clean(active_status).lower():
        return "stopped"
    start = _parse_date(row.get("start_date"))
    end = _parse_date(row.get("end_date"))
    if start and start > today:
        return "upcoming"
    if end and end < today:
        return "expired_pending_stop"
    return "current"


def _read_supplement_allocations(member_id: str) -> list[dict[str, Any]]:
    """Read Supplement allocations without invoking auto-stop or any persistence path."""
    clean_member_id = _clean(member_id)
    if not clean_member_id:
        return []
    state = load_state()
    repository = supplement_allocation._repository_lookup(active_only=False)
    return [
        supplement_allocation._normalise_existing_row(row, repository=repository)
        for row in list(state.get(supplement_allocation.STORE_KEY, []) or [])
        if isinstance(row, dict)
        and _clean(row.get("member_id")) == clean_member_id
    ]


def _profile_read_model(
    profile: dict[str, Any],
    items: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, int]]:
    rows = _active_profile_items(items)
    meals = [
        copy.deepcopy(row)
        for row in rows
        if _clean(row.get("item_type")).lower() == MEAL_ITEM_TYPE
    ]
    guidance = [
        copy.deepcopy(row)
        for row in rows
        if _clean(row.get("item_type")).lower() in GUIDANCE_ITEM_TYPES
    ]
    ignored = {
        "exercise": sum(
            1
            for row in rows
            if _clean(row.get("item_type")).lower() == "exercise"
        ),
        "supplement": sum(
            1
            for row in rows
            if _clean(row.get("item_type")).lower() == "supplement"
        ),
    }
    meals.sort(
        key=lambda row: (
            _safe_int(row.get("day_number"), 0),
            _safe_int(row.get("item_order"), 0),
            _clean(row.get("reference_label")).casefold(),
        )
    )
    return meals, guidance, ignored


def _member_safe_supplement_row(row: dict[str, Any]) -> dict[str, Any]:
    safe = copy.deepcopy(dict(row or {}))
    safe.pop("admin_notes", None)
    snapshot = copy.deepcopy(dict(safe.get("source_snapshot") or {}))
    snapshot.pop("admin_notes", None)
    snapshot.pop("notes", None)
    safe["source_snapshot"] = snapshot
    return safe


def _partition_allocations(
    rows: list[dict[str, Any]],
    *,
    today: dt.date,
    active_status: str,
) -> dict[str, list[dict[str, Any]]]:
    partitions: dict[str, list[dict[str, Any]]] = {
        "current": [],
        "upcoming": [],
        "expired_pending_stop": [],
        "stopped": [],
    }
    for raw in rows:
        row = copy.deepcopy(dict(raw or {}))
        state = _effective_state(row, today=today, active_status=active_status)
        row["effective_state"] = state
        partitions[state].append(row)
    for values in partitions.values():
        values.sort(
            key=lambda row: (
                _clean(row.get("start_date")),
                _clean(
                    row.get("exercise_name")
                    or row.get("supplement_name")
                    or row.get("title")
                ).casefold(),
                _clean(row.get("id")),
            )
        )
    return partitions


def build_current_member_plan(
    member_id: str,
    email: str = "",
    *,
    today: dt.date | None = None,
    profile_loader: Callable[..., tuple[bool, dict, list, str]] = (
        _default_profile_loader
    ),
    exercise_loader: Callable[..., list[dict[str, Any]]] = (
        list_member_exercise_allocations
    ),
    supplement_loader: Callable[[str], list[dict[str, Any]]] = (
        _read_supplement_allocations
    ),
) -> dict[str, Any]:
    """Build one consolidated read model without creating a persistence authority."""
    clean_member_id = _clean(member_id)
    if not clean_member_id:
        raise ValueError("Member identity is required.")
    today = today or dt.date.today()
    warnings: list[str] = []

    profile: dict[str, Any] = {}
    profile_items: list[dict[str, Any]] = []
    try:
        profile_ok, loaded_profile, loaded_items, profile_message = profile_loader(
            clean_member_id,
            _clean(email),
        )
        if profile_ok:
            profile = copy.deepcopy(dict(loaded_profile or {}))
            profile_items = [
                copy.deepcopy(dict(row))
                for row in list(loaded_items or [])
                if isinstance(row, dict)
            ]
        else:
            warnings.append(profile_message or "Meal profile could not be loaded.")
    except Exception as exc:
        warnings.append(f"Meal profile could not be loaded: {exc}")

    try:
        exercise_rows = exercise_loader(
            clean_member_id,
            include_stopped=True,
        )
    except Exception as exc:
        exercise_rows = []
        warnings.append(f"Exercise allocations could not be loaded: {exc}")

    try:
        supplement_rows = supplement_loader(clean_member_id)
    except Exception as exc:
        supplement_rows = []
        warnings.append(f"Supplement allocations could not be loaded: {exc}")

    meals, guidance, ignored_profile_rows = _profile_read_model(
        profile,
        profile_items,
    )
    exercise = _partition_allocations(
        list(exercise_rows or []),
        today=today,
        active_status=EXERCISE_ACTIVE_STATUS,
    )
    supplement = _partition_allocations(
        [
            _member_safe_supplement_row(row)
            for row in list(supplement_rows or [])
            if isinstance(row, dict)
        ],
        today=today,
        active_status=supplement_allocation.ACTIVE_STATUS,
    )

    model = {
        "read_model_version": READ_MODEL_VERSION,
        "read_only": True,
        "member_id": clean_member_id,
        "member_email": _clean(email),
        "as_of_date": today.isoformat(),
        "meal_profile": profile,
        "meals": meals,
        "guidance_items": guidance,
        "exercise": exercise,
        "supplement": supplement,
        "ignored_profile_rows": ignored_profile_rows,
        "warnings": warnings,
        "source_authority": {
            "meal": "active_meal_profile",
            "exercise": "member_exercise_allocations",
            "supplement": "member_supplements",
        },
    }
    model["has_content"] = bool(
        meals
        or guidance
        or exercise["current"]
        or exercise["upcoming"]
        or supplement["current"]
        or supplement["upcoming"]
    )
    model["counts"] = {
        "meals": len(meals),
        "current_exercises": len(exercise["current"]),
        "upcoming_exercises": len(exercise["upcoming"]),
        "current_supplements": len(supplement["current"]),
        "upcoming_supplements": len(supplement["upcoming"]),
        "hidden_expired_exercises": len(exercise["expired_pending_stop"]),
        "hidden_expired_supplements": len(supplement["expired_pending_stop"]),
    }
    return model


def load_current_member_plan(
    member_id: str,
    email: str = "",
    *,
    today: dt.date | None = None,
) -> tuple[bool, dict[str, Any], str]:
    try:
        model = build_current_member_plan(
            member_id,
            email,
            today=today,
        )
        message = "Loaded consolidated read-only Current Member Plan."
        if model.get("warnings"):
            message += " " + " ".join(model["warnings"])
        return True, model, message
    except Exception as exc:
        return False, {}, f"Could not load Current Member Plan: {exc}"
