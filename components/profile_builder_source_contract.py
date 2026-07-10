from __future__ import annotations

import copy
import re
from typing import Any, Dict, List, Tuple

from components.db import list_member_supplements
from components.recommendation_contract import list_repository_items


_SOURCE_FIELDS_PATCHED = False


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


def _safe_key(value: object) -> str:
    return re.sub(r"[^A-Za-z0-9]+", "_", str(value or "")).strip("_") or "blank"


def _image_reference(row: Dict[str, Any]) -> Dict[str, str]:
    return {
        "image_url": _clean(row.get("image_url")),
        "image_bucket": _clean(row.get("image_bucket")),
        "image_path": _clean(row.get("image_path")),
        "image_access_type": _clean(row.get("image_access_type")),
    }


def _has_image_reference(row: Dict[str, Any]) -> bool:
    image = _image_reference(row)
    return any(image.get(field) for field in ("image_url", "image_bucket", "image_path"))


def _image_reference_text(snapshot: Dict[str, Any]) -> str:
    image = snapshot.get("image") or {}
    if _clean(image.get("image_url")):
        return _clean(image.get("image_url"))
    if _clean(image.get("image_bucket")) or _clean(image.get("image_path")):
        return " / ".join(part for part in [_clean(image.get("image_bucket")), _clean(image.get("image_path"))] if part)
    return "No image reference"


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
    return _clean(snapshot.get("title"))


def exercise_display_label(snapshot: Dict[str, Any]) -> str:
    return _clean(snapshot.get("title"))


def supplement_display_label(snapshot: Dict[str, Any]) -> str:
    return _clean(snapshot.get("title") or snapshot.get("supplement_name"))


def _index_snapshot(snapshots: Dict[str, Dict[str, Any]], display_label: str, title: str, snapshot: Dict[str, Any]) -> None:
    if display_label:
        snapshots[display_label] = snapshot
    if title and title not in snapshots:
        snapshots[title] = snapshot


def build_profile_builder_source_contract() -> Tuple[Dict[str, List[str]], Dict[str, Dict[str, Any]], str]:
    """Return source-backed Profile Builder dropdown options and source snapshots.

    Dropdown labels stay clean. Repository/regimen details are surfaced as compact
    editable source-detail fields and are preserved in source_snapshot.
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
        messages.append(f"Recipe source: {len(sources['recipe'])} active repository item(s) with clean labels and full snapshots.")
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
        messages.append(f"Exercise source: {len(sources['exercise'])} active repository item(s) with clean labels and full snapshots.")
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
        messages.append(f"Supplement source: {len(sources['supplement'])} active regimen name(s) with clean labels and full snapshots.")
    except Exception as exc:
        messages.append(f"Supplement source unavailable: {exc}")

    patch_streamlit_source_detail_fields()
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


def _source_detail_defaults(kind: str, snapshot: Dict[str, Any]) -> Dict[str, str]:
    if kind in {"meal", "recipe"}:
        return {
            "meal_type": _clean(snapshot.get("meal_type")),
            "diet_type": _clean(snapshot.get("diet_type")),
            "prep_time": _clean(snapshot.get("prep_time")),
            "calories": _clean(snapshot.get("calories")),
            "portion_size": _clean(snapshot.get("portion_size")),
            "ingredients": _clean(snapshot.get("ingredients")),
            "steps": _clean(snapshot.get("steps")),
            "image_reference": _image_reference_text(snapshot),
        }
    if kind == "exercise":
        return {
            "category": _clean(snapshot.get("category")),
            "difficulty": _clean(snapshot.get("difficulty")),
            "duration_or_reps": _clean(snapshot.get("duration_or_reps")),
            "equipment": _clean(snapshot.get("equipment")),
            "instructions": _clean(snapshot.get("instructions")),
            "benefits": _clean(snapshot.get("benefits")),
            "image_reference": _image_reference_text(snapshot),
        }
    if kind == "supplement":
        return {
            "dosage": _clean(snapshot.get("dosage")),
            "frequency": _clean(snapshot.get("frequency")),
            "timing": _clean(snapshot.get("timing")),
            "instructions": _clean(snapshot.get("instructions")),
            "start_date": _clean(snapshot.get("start_date")),
            "end_date": _clean(snapshot.get("end_date")),
            "admin_notes": _clean(snapshot.get("admin_notes")),
        }
    return {}


def _selection_key_parts(button_key: str):
    key = _clean(button_key)
    if key.startswith("add_meal_"):
        return "meal", key.replace("add_meal_", "", 1), "recipe"
    if key.startswith("add_exercise_"):
        return "exercise", key.replace("add_exercise_", "", 1), "exercise"
    if key.startswith("add_supplement_"):
        return "supplement", key.replace("add_supplement_", "", 1), "supplement"
    return "", "", ""


def _row_selection_keys(button_key: str) -> List[Tuple[str, str, str]]:
    try:
        import streamlit as st
    except Exception:
        return []

    kind, suffix, field = _selection_key_parts(button_key)
    if not kind or not suffix:
        return []
    prefix = f"pbw_{kind}_{suffix}_"
    matches = []
    pattern = re.compile(rf"^pbw_{kind}_{re.escape(suffix)}_(\d+)_{field}$")
    for key, value in st.session_state.items():
        key_text = str(key)
        if not key_text.startswith(prefix):
            continue
        if pattern.match(key_text) and _clean(value) and not _clean(value).startswith("-- Select"):
            matches.append((key_text, _clean(value), kind))
    return sorted(matches, key=lambda item: item[0])


def _field_key(selection_key: str, field: str) -> str:
    return f"{selection_key}_src_{field}"


def _set_source_defaults(selection_key: str, label: str, kind: str, snapshot: Dict[str, Any]) -> Dict[str, str]:
    import streamlit as st

    defaults = _source_detail_defaults(kind, snapshot)
    marker_key = _field_key(selection_key, "selected_label")
    if st.session_state.get(marker_key) != label:
        for field, value in defaults.items():
            st.session_state[_field_key(selection_key, field)] = value
        st.session_state[marker_key] = label
    return defaults


def _render_source_detail_block(container, selection_key: str, label: str, kind: str) -> None:
    snapshot = source_snapshot_for_label(kind, label)
    if not snapshot:
        return
    import streamlit as st

    _set_source_defaults(selection_key, label, kind, snapshot)
    container.markdown(
        "<div style='border:1px solid #E3C98E;background:#FFFDF8;border-radius:14px;padding:.58rem .7rem;margin:.2rem 0 .62rem 0;'>"
        "<b style='color:#064E3B;'>Pulled Source Details</b> "
        "<span style='color:#64748B;font-size:.78rem;font-weight:700;'>editable baseline from repository/regimen; admin override fields remain above.</span>"
        "</div>",
        unsafe_allow_html=True,
    )

    if kind == "meal":
        c1, c2, c3, c4, c5 = container.columns([0.18, 0.18, 0.15, 0.14, 0.20], gap="small")
        c1.text_input("Source Meal Type", key=_field_key(selection_key, "meal_type"))
        c2.text_input("Source Diet Type", key=_field_key(selection_key, "diet_type"))
        c3.text_input("Source Prep Time", key=_field_key(selection_key, "prep_time"))
        c4.text_input("Source Calories", key=_field_key(selection_key, "calories"))
        c5.text_input("Source Portion", key=_field_key(selection_key, "portion_size"))
        d1, d2, d3 = container.columns([0.34, 0.42, 0.24], gap="small")
        d1.text_area("Source Ingredients", height=74, key=_field_key(selection_key, "ingredients"))
        d2.text_area("Source Steps", height=74, key=_field_key(selection_key, "steps"))
        d3.text_input("Image Reference", key=_field_key(selection_key, "image_reference"), disabled=True)
    elif kind == "exercise":
        c1, c2, c3, c4 = container.columns([0.22, 0.18, 0.20, 0.20], gap="small")
        c1.text_input("Source Category", key=_field_key(selection_key, "category"))
        c2.text_input("Source Difficulty", key=_field_key(selection_key, "difficulty"))
        c3.text_input("Source Duration/Reps", key=_field_key(selection_key, "duration_or_reps"))
        c4.text_input("Source Equipment", key=_field_key(selection_key, "equipment"))
        d1, d2, d3 = container.columns([0.40, 0.36, 0.24], gap="small")
        d1.text_area("Source Instructions", height=74, key=_field_key(selection_key, "instructions"))
        d2.text_area("Source Benefits", height=74, key=_field_key(selection_key, "benefits"))
        d3.text_input("Image Reference", key=_field_key(selection_key, "image_reference"), disabled=True)
    elif kind == "supplement":
        c1, c2, c3, c4, c5 = container.columns([0.20, 0.18, 0.18, 0.18, 0.18], gap="small")
        c1.text_input("Source Dosage", key=_field_key(selection_key, "dosage"))
        c2.text_input("Source Frequency", key=_field_key(selection_key, "frequency"))
        c3.text_input("Source Timing", key=_field_key(selection_key, "timing"))
        c4.text_input("Start Date", key=_field_key(selection_key, "start_date"))
        c5.text_input("End Date", key=_field_key(selection_key, "end_date"))
        d1, d2 = container.columns([0.52, 0.48], gap="small")
        d1.text_area("Source Instructions", height=74, key=_field_key(selection_key, "instructions"))
        d2.text_area("Source Admin Notes", height=74, key=_field_key(selection_key, "admin_notes"))


def _render_source_details_before_add_button(container, button_key: str) -> None:
    for selection_key, label, kind in _row_selection_keys(button_key):
        _render_source_detail_block(container, selection_key, label, kind)


def _session_overrides_for_label(item_type: str, label: str) -> Dict[str, str]:
    try:
        import streamlit as st
    except Exception:
        return {}

    kind = "meal" if _clean(item_type).lower() in {"meal", "recipe"} else _clean(item_type).lower()
    clean_label = _clean(label)
    for key, value in st.session_state.items():
        key_text = str(key)
        if not key_text.startswith(f"pbw_{kind}_"):
            continue
        field_name = "recipe" if kind == "meal" else kind
        if not key_text.endswith(f"_{field_name}"):
            continue
        if _clean(value) != clean_label:
            continue
        defaults = _source_detail_defaults(kind, source_snapshot_for_label(kind, clean_label))
        overrides = {}
        for field, default_value in defaults.items():
            if field == "image_reference":
                continue
            current_value = _clean(st.session_state.get(_field_key(key_text, field)))
            if current_value != _clean(default_value):
                overrides[field] = current_value
        return overrides
    return {}


def _effective_snapshot_with_overrides(item_type: str, label: str, snapshot: Dict[str, Any]) -> Dict[str, Any]:
    original = copy.deepcopy(snapshot)
    overrides = _session_overrides_for_label(item_type, label)
    effective = copy.deepcopy(snapshot)
    for field, value in overrides.items():
        effective[field] = value
    effective["source_original_snapshot"] = original
    effective["admin_source_overrides"] = overrides
    return effective


def source_storage_payload(item_type: str, label: str) -> Dict[str, Any]:
    snapshot = source_snapshot_for_label(item_type, label)
    if not snapshot:
        return {}
    effective_snapshot = _effective_snapshot_with_overrides(item_type, label, snapshot)
    image = snapshot.get("image") or {}
    return {
        "source_type": _clean(snapshot.get("source_type")),
        "source_id": _clean(snapshot.get("source_id")),
        "source_label": _clean(snapshot.get("title") or snapshot.get("supplement_name") or label),
        "source_snapshot": effective_snapshot,
        "source_image_url": _clean(image.get("image_url")),
        "source_image_bucket": _clean(image.get("image_bucket")),
        "source_image_path": _clean(image.get("image_path")),
        "source_image_access_type": _clean(image.get("image_access_type")),
    }


def patch_streamlit_source_detail_fields() -> None:
    """Patch Streamlit buttons so source details render just above Add Row buttons.

    This avoids changing the Profile Builder page layout directly while keeping the
    detail UI in the correct second-row position under each selected source row.
    """
    global _SOURCE_FIELDS_PATCHED
    if _SOURCE_FIELDS_PATCHED:
        return
    try:
        from streamlit.delta_generator import DeltaGenerator
    except Exception:
        return

    original_button = DeltaGenerator.button

    def source_detail_button(self, label, *args, **kwargs):
        key = _clean(kwargs.get("key"))
        if key.startswith(("add_meal_", "add_exercise_", "add_supplement_")):
            _render_source_details_before_add_button(self, key)
        return original_button(self, label, *args, **kwargs)

    DeltaGenerator.button = source_detail_button
    _SOURCE_FIELDS_PATCHED = True


patch_streamlit_source_detail_fields()
