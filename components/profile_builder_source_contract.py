from __future__ import annotations

from typing import Any, Dict, List, Tuple

from components.db import list_member_supplements
from components.recommendation_contract import list_repository_items


def _clean(value: object) -> str:
    return str(value or "").strip()


def _dedupe(values: List[str]) -> List[str]:
    seen = set()
    out = []
    for value in values or []:
        text = _clean(value)
        if not text or text.startswith("-- Select"):
            continue
        key = text.lower()
        if key not in seen:
            seen.add(key)
            out.append(text)
    return sorted(out, key=str.lower)


def _image_reference(row: Dict[str, Any]) -> Dict[str, str]:
    return {
        "image_url": _clean(row.get("image_url")),
        "image_bucket": _clean(row.get("image_bucket")),
        "image_path": _clean(row.get("image_path")),
        "image_access_type": _clean(row.get("image_access_type")),
    }


def _has_image_reference(row: Dict[str, Any]) -> bool:
    return any(_image_reference(row).values())


def recipe_snapshot(row: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "source_type": "recipe_repository",
        "source_id": _clean(row.get("source_id") or row.get("id")),
        "title": _clean(row.get("title")),
        "description": _clean(row.get("description")),
        "meal_type": _clean(row.get("meal_type")),
        "diet_type": _clean(row.get("diet_type")),
        "goal_tags": _clean(row.get("goal_tags")),
        "condition_tags": _clean(row.get("condition_tags")),
        "prep_time": _clean(row.get("prep_time")),
        "calories": _clean(row.get("calories")),
        "protein": _clean(row.get("protein")),
        "fat": _clean(row.get("fat")),
        "carbohydrates": _clean(row.get("carbohydrates")),
        "additional_nutrition": _clean(row.get("additional_nutrition")),
        "servings": _clean(row.get("servings")),
        "portion_size": _clean(row.get("portion_size")),
        "ingredients": _clean(row.get("ingredients")),
        "steps": _clean(row.get("steps")),
        "nutrition": _clean(row.get("nutrition")),
        "status": _clean(row.get("status")),
        "image": _image_reference(row),
        "has_image_reference": _has_image_reference(row),
    }


def exercise_snapshot(row: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "source_type": "exercise_repository",
        "source_id": _clean(row.get("source_id") or row.get("id")),
        "title": _clean(row.get("title")),
        "description": _clean(row.get("description")),
        "category": _clean(row.get("category")),
        "difficulty": _clean(row.get("difficulty")),
        "goal_tags": _clean(row.get("goal_tags")),
        "condition_tags": _clean(row.get("condition_tags")),
        "duration_or_reps": _clean(row.get("duration_or_reps")),
        "equipment": _clean(row.get("equipment")),
        "instructions": _clean(row.get("instructions")),
        "benefits": _clean(row.get("benefits")),
        "status": _clean(row.get("status")),
        "image": _image_reference(row),
        "has_image_reference": _has_image_reference(row),
    }


def supplement_snapshot(row: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "source_type": "active_supplement_regimen",
        "source_id": _clean(row.get("id") or row.get("supplement_id")),
        "title": _clean(row.get("supplement_name")),
        "supplement_name": _clean(row.get("supplement_name")),
        "dosage": _clean(row.get("dosage")),
        "frequency": _clean(row.get("frequency")),
        "timing": _clean(row.get("timing")),
        "instructions": _clean(row.get("instructions")),
        "start_date": _clean(row.get("start_date")),
        "end_date": _clean(row.get("end_date")),
        "admin_notes": _clean(row.get("admin_notes")),
        "status": _clean(row.get("status")),
    }


def build_profile_builder_source_contract() -> Tuple[Dict[str, List[str]], Dict[str, Dict[str, Any]], str]:
    """Return source-backed Profile Builder dropdown options and immutable source snapshots.

    This is the H9A.10B bridge. It keeps Profile Builder selection source-backed while
    preserving admin override fields separately. Images are preserved as references in
    snapshots, not loaded in normal admin editing.
    """
    sources: Dict[str, List[str]] = {"recipe": [], "exercise": [], "supplement": []}
    snapshots: Dict[str, Dict[str, Any]] = {"recipe": {}, "exercise": {}, "supplement": {}}
    messages = []

    try:
        recipe_rows = list_repository_items("recipes", active_only=True)
        sources["recipe"] = _dedupe([_clean(row.get("title")) for row in recipe_rows])
        for row in recipe_rows:
            title = _clean(row.get("title"))
            if title:
                snapshots["recipe"][title] = recipe_snapshot(row)
        messages.append(f"Recipe source: {len(sources['recipe'])} active repository item(s).")
    except Exception as exc:
        messages.append(f"Recipe source unavailable: {exc}")

    try:
        exercise_rows = list_repository_items("exercises", active_only=True)
        sources["exercise"] = _dedupe([_clean(row.get("title")) for row in exercise_rows])
        for row in exercise_rows:
            title = _clean(row.get("title"))
            if title:
                snapshots["exercise"][title] = exercise_snapshot(row)
        messages.append(f"Exercise source: {len(sources['exercise'])} active repository item(s).")
    except Exception as exc:
        messages.append(f"Exercise source unavailable: {exc}")

    try:
        supplement_rows = list_member_supplements(status="Active")
        names = _dedupe([_clean(row.get("supplement_name")) for row in supplement_rows])
        sources["supplement"] = names
        for row in supplement_rows:
            name = _clean(row.get("supplement_name"))
            if name and name not in snapshots["supplement"]:
                snapshots["supplement"][name] = supplement_snapshot(row)
        messages.append(f"Supplement source: {len(sources['supplement'])} active regimen name(s).")
    except Exception as exc:
        messages.append(f"Supplement source unavailable: {exc}")

    return sources, snapshots, " ".join(messages)


def source_snapshot_for_label(item_type: str, label: str) -> Dict[str, Any]:
    _, snapshots, _ = build_profile_builder_source_contract()
    kind = _clean(item_type).lower()
    if kind in {"meal", "recipe"}:
        return snapshots.get("recipe", {}).get(_clean(label), {})
    if kind in {"exercise", "workout"}:
        return snapshots.get("exercise", {}).get(_clean(label), {})
    if kind == "supplement":
        return snapshots.get("supplement", {}).get(_clean(label), {})
    return {}
