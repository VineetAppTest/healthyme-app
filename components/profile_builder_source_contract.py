from __future__ import annotations

import copy
import inspect
from typing import Any, Dict, List, Tuple

from components.db import list_member_supplements
from components.recommendation_contract import list_repository_items

_SOURCE_INSTRUCTION_FIELD_PATCHED = False
_PROFILE_BUILDER_LAYOUT_PATCHED = False


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
    image = _image_reference(row)
    return any(image.get(field) for field in ("image_url", "image_bucket", "image_path"))


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


def _find_profile_builder_page_globals() -> Dict[str, Any]:
    for frame_info in inspect.stack():
        globals_map = frame_info.frame.f_globals
        page_file = str(globals_map.get("__file__", ""))
        if (
            "38_Admin_Recommendation_Profile_Builder" in page_file
            and "SOURCE_DETAIL_FIELDS" in globals_map
            and "render_source_details" in globals_map
            and "apply_source_defaults_to_row" in globals_map
        ):
            return globals_map
    return {}


def _source_field_uses_area_height(kind: str, field: str, field_type: str) -> bool:
    """Only meal long-form fields stay tall.

    Exercise and supplement source-detail fields must visually match the first-row
    compact controls, so even values like Benefits/Admin Notes render as single-height
    text inputs in this admin builder view.
    """
    return field_type == "area" and kind not in {"exercise", "supplement"}


def patch_profile_builder_source_detail_layout() -> None:
    """Apply the Profile Builder source-detail layout directly to page globals.

    Streamlit reruns the page and recreates page-level functions on every interaction.
    The patch checks the current page function identity and reapplies the direct
    renderer whenever the page has been recreated.
    """
    global _PROFILE_BUILDER_LAYOUT_PATCHED

    try:
        import streamlit as st
    except Exception:
        return

    g = _find_profile_builder_page_globals()
    if not g:
        return

    g["SOURCE_DETAIL_FIELDS"]["exercise"] = [
        ("category", "Category", "text"),
        ("difficulty", "Difficulty", "text"),
        ("duration_or_reps", "Duration/Reps", "text"),
        ("equipment", "Equipment", "text"),
        ("benefits", "Benefits", "area"),
        ("image_reference", "Image Reference", "text"),
    ]
    g["SOURCE_DETAIL_FIELDS"]["supplement"] = [
        ("timing", "Source Timing", "text"),
        ("admin_notes", "Admin Notes", "area"),
    ]

    current_render = g.get("render_source_details")
    if getattr(current_render, "_hm_compact_height_source_layout_render", False):
        _PROFILE_BUILDER_LAYOUT_PATCHED = True
        return

    def _set_if_blank(kind, day, slot, idx, field, value):
        value_text = _clean(value)
        if not value_text:
            return
        widget_key = g["item_widget_key"](kind, day, slot, idx, field)
        existing = _clean(st.session_state.get(widget_key) or g["item_value"](kind, day, slot, idx, field, ""))
        if existing:
            return
        g["set_row_value"](kind, day, slot, idx, field, value_text)

    def _patched_apply_source_defaults_to_row(kind, day, slot, idx, selected_label):
        if not selected_label or g["is_select"](selected_label):
            return
        snapshot = source_snapshot_for_label(g["source_lookup_kind"](kind), selected_label)
        if not snapshot:
            return

        marker_key = g["item_key"](kind, day, slot, idx, "source_selected_label")
        already_selected = st.session_state["pb_items"].get(marker_key) == selected_label

        if kind == "meal" and not already_selected:
            source_portion = _clean(snapshot.get("portion_size"))
            if source_portion:
                g["set_row_value"](kind, day, slot, idx, "portion", source_portion)
        elif kind == "supplement" and not already_selected:
            source_frequency = g["frequency_from_source"](snapshot.get("frequency"))
            source_dosage = _clean(snapshot.get("dosage"))
            source_timeline = g["timeline_from_source"](snapshot.get("timing"))
            if source_frequency:
                g["set_row_value"](kind, day, slot, idx, "frequency", source_frequency)
            if source_timeline:
                g["set_row_value"](kind, day, slot, idx, "timeline", source_timeline)
            if source_dosage:
                g["set_row_value"](kind, day, slot, idx, "dose", source_dosage)

        if kind in {"exercise", "supplement"}:
            _set_if_blank(kind, day, slot, idx, "instruction", snapshot.get("instructions"))

        st.session_state["pb_items"][marker_key] = selected_label

    def _render_source_field(col, kind, day, slot, idx, field, label, field_type, defaults):
        key = g["source_detail_widget_key"](kind, day, slot, idx, field)
        g["set_widget_default"](
            key,
            g["source_detail_value"](kind, day, slot, idx, field, defaults.get(field, "")),
        )
        if _source_field_uses_area_height(kind, field, field_type):
            col.text_area(label, height=80, key=key, disabled=(field == "image_reference"))
        else:
            col.text_input(label, key=key, disabled=(field == "image_reference"))

    def _layout_rows_for_kind(kind: str, fields: List[Tuple[str, str, str]]) -> List[List[Tuple[str, str, str]]]:
        if kind == "exercise":
            return [fields[:3], fields[3:6]]
        if kind == "supplement":
            return [fields]
        return [fields[:4], fields[4:]]

    def _patched_render_source_details(kind, day, slot, idx, selected_label):
        if not selected_label or g["is_select"](selected_label):
            return
        snapshot = source_snapshot_for_label(g["source_lookup_kind"](kind), selected_label)
        if not snapshot:
            st.caption("Pulled Source Details: no repository/regimen details were found for this selection.")
            return

        st.markdown(
            "<div class='hm-source-box'><b>Pulled Source Details</b> "
            "<span>Editable non-duplicate source context. First-row fields are populated from source where applicable.</span></div>",
            unsafe_allow_html=True,
        )
        g["render_source_context"](kind, snapshot)
        defaults = g["source_detail_defaults"](kind, snapshot)
        fields = g["SOURCE_DETAIL_FIELDS"].get(kind, [])

        for row_fields in _layout_rows_for_kind(kind, fields):
            if not row_fields:
                continue
            cols = st.columns(len(row_fields), gap="small")
            for col, (field, label, field_type) in zip(cols, row_fields):
                _render_source_field(col, kind, day, slot, idx, field, label, field_type, defaults)

        overrides = g["collect_source_overrides"](kind, day, slot, idx, selected_label)
        for field, value in overrides.items():
            st.session_state["pb_items"][g["item_key"](kind, day, slot, idx, f"source_{field}")] = value
        g["register_source_overrides"](kind, selected_label, overrides)

    _patched_render_source_details._hm_compact_height_source_layout_render = True
    _patched_apply_source_defaults_to_row._hm_compact_height_source_layout_render = True
    g["apply_source_defaults_to_row"] = _patched_apply_source_defaults_to_row
    g["render_source_details"] = _patched_render_source_details
    _PROFILE_BUILDER_LAYOUT_PATCHED = True


def build_profile_builder_source_contract() -> Tuple[Dict[str, List[str]], Dict[str, Dict[str, Any]], str]:
    """Return clean source labels and immutable source snapshots."""
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

    patch_streamlit_source_instruction_fields()
    patch_profile_builder_source_detail_layout()
    return sources, snapshots, " ".join(messages)


def _current_selected_source_label(kind: str) -> str:
    try:
        import streamlit as st
    except Exception:
        return ""

    field_name = "recipe" if kind in {"meal", "recipe"} else kind
    prefix_kind = "meal" if kind in {"meal", "recipe"} else kind
    prefix = f"pbw_{prefix_kind}_"
    suffix = f"_{field_name}"
    for key, value in st.session_state.items():
        key_text = str(key)
        selected = _clean(value)
        if not key_text.startswith(prefix) or not key_text.endswith(suffix):
            continue
        if selected and not selected.startswith("-- Select"):
            return selected
    return ""


def _slot_from_safe_key(value: str) -> str:
    known = {
        "Exercise_Regime": "Exercise Regime",
        "Supplement_Regime": "Supplement Regime",
    }
    return known.get(value, value.replace("_", " "))


def _autofill_first_row_instruction(kind: str, selected_label: str, snapshot: Dict[str, Any]) -> None:
    if kind not in {"exercise", "supplement"}:
        return
    source_instruction = _clean(snapshot.get("instructions"))
    if not source_instruction or not selected_label:
        return

    try:
        import streamlit as st
    except Exception:
        return

    source_suffix = f"_{kind}"
    prefix = f"pbw_{kind}_"
    for key, value in list(st.session_state.items()):
        key_text = str(key)
        if not key_text.startswith(prefix) or not key_text.endswith(source_suffix):
            continue
        if _clean(value) != selected_label:
            continue

        base = key_text[: -len(source_suffix)]
        instruction_widget_key = f"{base}_instruction"
        if _clean(st.session_state.get(instruction_widget_key)):
            continue

        st.session_state[instruction_widget_key] = source_instruction

        remainder = base[len(prefix):]
        parts = remainder.split("_")
        if len(parts) >= 3:
            day = parts[0]
            idx = parts[-1]
            slot = _slot_from_safe_key("_".join(parts[1:-1]))
            st.session_state.setdefault("pb_items", {})
            st.session_state["pb_items"][f"{kind}|{day}|{slot}|{idx}|instruction"] = source_instruction


def source_snapshot_for_label(item_type: str, label: str) -> Dict[str, Any]:
    patch_profile_builder_source_detail_layout()
    _, snapshots, _ = build_profile_builder_source_contract()
    kind = _clean(item_type).lower()
    clean_label = _clean(label)
    if kind in {"meal", "recipe"}:
        return snapshots.get("recipe", {}).get(clean_label, {})
    if kind in {"exercise", "workout"}:
        exact = snapshots.get("exercise", {}).get(clean_label, {})
        if exact:
            _autofill_first_row_instruction("exercise", clean_label, exact)
            return exact
        recovered_label = _current_selected_source_label("exercise")
        recovered = snapshots.get("exercise", {}).get(recovered_label, {})
        if recovered:
            _autofill_first_row_instruction("exercise", recovered_label, recovered)
        return recovered
    if kind == "supplement":
        snapshot = snapshots.get("supplement", {}).get(clean_label, {})
        if snapshot:
            _autofill_first_row_instruction("supplement", clean_label, snapshot)
        return snapshot
    return {}


def _session_overrides_for_snapshot(snapshot: Dict[str, Any], label: str) -> Dict[str, str]:
    try:
        import streamlit as st
    except Exception:
        return {}
    source_type = _clean(snapshot.get("source_type"))
    source_label = _clean(snapshot.get("title") or snapshot.get("supplement_name") or label)
    return dict((st.session_state.get("pb_source_override_map") or {}).get(f"{source_type}:{source_label}", {}) or {})


def _effective_snapshot_with_overrides(label: str, snapshot: Dict[str, Any]) -> Dict[str, Any]:
    original = copy.deepcopy(snapshot)
    overrides = _session_overrides_for_snapshot(snapshot, label)
    effective = copy.deepcopy(snapshot)
    for field, value in overrides.items():
        if field in {"image_reference", "instructions"}:
            continue
        effective[field] = value
    effective["source_original_snapshot"] = original
    effective["admin_source_overrides"] = overrides
    return effective


def source_storage_payload(item_type: str, label: str) -> Dict[str, Any]:
    snapshot = source_snapshot_for_label(item_type, label)
    if not snapshot:
        return {}
    effective_snapshot = _effective_snapshot_with_overrides(label, snapshot)
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


def patch_streamlit_source_instruction_fields() -> None:
    """Hide duplicate Source Instructions fields from the second source-detail row."""
    global _SOURCE_INSTRUCTION_FIELD_PATCHED
    if _SOURCE_INSTRUCTION_FIELD_PATCHED:
        return
    try:
        from streamlit.delta_generator import DeltaGenerator
    except Exception:
        return

    original_text_area = DeltaGenerator.text_area

    def source_instruction_aware_text_area(self, label, *args, **kwargs):
        if _clean(label) == "Source Instructions":
            key = kwargs.get("key")
            try:
                import streamlit as st
                if key and key not in st.session_state:
                    st.session_state[key] = ""
            except Exception:
                pass
            return ""
        return original_text_area(self, label, *args, **kwargs)

    DeltaGenerator.text_area = source_instruction_aware_text_area
    _SOURCE_INSTRUCTION_FIELD_PATCHED = True


patch_streamlit_source_instruction_fields()
