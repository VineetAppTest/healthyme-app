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


def _short(value: object, limit: int = 72) -> str:
    text = _clean(value)
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "…"


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


def recipe_display_label(snapshot: Dict[str, Any]) -> str:
    parts = [_clean(snapshot.get("title"))]
    meta = []
    for field in ("meal_type", "portion_size", "prep_time"):
        value = _clean(snapshot.get(field))
        if value:
            meta.append(value)
    calories = _clean(snapshot.get("calories"))
    if calories:
        meta.append(f"{calories} kcal")
    if snapshot.get("has_image_reference"):
        meta.append("image ref")
    return _short(f"{parts[0]} — {' | '.join(meta)}" if meta else parts[0], 110)


def exercise_display_label(snapshot: Dict[str, Any]) -> str:
    title = _clean(snapshot.get("title"))
    meta = []
    for field in ("category", "difficulty", "duration_or_reps", "equipment"):
        value = _clean(snapshot.get(field))
        if value:
            meta.append(value)
    if snapshot.get("has_image_reference"):
        meta.append("image ref")
    return _short(f"{title} — {' | '.join(meta)}" if meta else title, 110)


def supplement_display_label(snapshot: Dict[str, Any]) -> str:
    title = _clean(snapshot.get("title") or snapshot.get("supplement_name"))
    meta = []
    for field in ("dosage", "frequency", "timing"):
        value = _clean(snapshot.get(field))
        if value:
            meta.append(value)
    return _short(f"{title} — {' | '.join(meta)}" if meta else title, 110)


def _index_snapshot(snapshots: Dict[str, Dict[str, Any]], display_label: str, title: str, snapshot: Dict[str, Any]) -> None:
    # Store both the rich display label and the base title so older saved drafts can still resolve.
    if display_label:
        snapshots[display_label] = snapshot
    if title and title not in snapshots:
        snapshots[title] = snapshot


def build_profile_builder_source_contract() -> Tuple[Dict[str, List[str]], Dict[str, Dict[str, Any]], str]:
    """Return source-backed Profile Builder dropdown options and immutable source snapshots.

    H9A.10C expands H9A.10B: the dropdown label now carries lightweight source
    detail, while full details and image references remain in a snapshot for storage.
    Images are referenced only; they are not loaded in normal admin editing.
    """
    sources: Dict[str, List[str]] = {"recipe": [], "exercise": [], "supplement": []}
    snapshots: Dict[str, Dict[str, Any]] = {"recipe": {}, "exercise": {}, "supplement": {}}
    messages = []

    try:
        recipe_rows = list_repository_items("recipes", active_only=True)
        recipe_labels = []
        for row in recipe_rows:
            snap = recipe_snapshot(row)
            title = _clean(snap.get("title"))
            label = recipe_display_label(snap)
            if title:
                recipe_labels.append(label)
                _index_snapshot(snapshots["recipe"], label, title, snap)
        sources["recipe"] = _dedupe(recipe_labels)
        messages.append(f"Recipe source: {len(sources['recipe'])} active repository item(s) with detail labels.")
    except Exception as exc:
        messages.append(f"Recipe source unavailable: {exc}")

    try:
        exercise_rows = list_repository_items("exercises", active_only=True)
        exercise_labels = []
        for row in exercise_rows:
            snap = exercise_snapshot(row)
            title = _clean(snap.get("title"))
            label = exercise_display_label(snap)
            if title:
                exercise_labels.append(label)
                _index_snapshot(snapshots["exercise"], label, title, snap)
        sources["exercise"] = _dedupe(exercise_labels)
        messages.append(f"Exercise source: {len(sources['exercise'])} active repository item(s) with detail labels.")
    except Exception as exc:
        messages.append(f"Exercise source unavailable: {exc}")

    try:
        supplement_rows = list_member_supplements(status="Active")
        supplement_labels = []
        for row in supplement_rows:
            snap = supplement_snapshot(row)
            name = _clean(snap.get("supplement_name"))
            label = supplement_display_label(snap)
            if name:
                supplement_labels.append(label)
                _index_snapshot(snapshots["supplement"], label, name, snap)
        sources["supplement"] = _dedupe(supplement_labels)
        messages.append(f"Supplement source: {len(sources['supplement'])} active regimen name(s) with detail labels.")
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


def source_storage_payload(item_type: str, label: str) -> Dict[str, Any]:
    snapshot = source_snapshot_for_label(item_type, label)
    if not snapshot:
        return {}
    image = snapshot.get("image") or {}
    return {
        "source_type": _clean(snapshot.get("source_type")),
        "source_id": _clean(snapshot.get("source_id")),
        "source_label": _clean(snapshot.get("title") or snapshot.get("supplement_name") or label),
        "source_snapshot": snapshot,
        "source_image_url": _clean(image.get("image_url")),
        "source_image_bucket": _clean(image.get("image_bucket")),
        "source_image_path": _clean(image.get("image_path")),
        "source_image_access_type": _clean(image.get("image_access_type")),
    }
