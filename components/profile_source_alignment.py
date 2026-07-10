from __future__ import annotations

from typing import Any, Dict, List, Set

import pandas as pd
import streamlit as st

from components.db import list_member_supplements
from components.recommendation_contract import EXERCISE_COLUMNS, RECIPE_COLUMNS, list_repository_items
from components.recommendation_profile_store import DEFAULT_SOURCES, load_profile_builder_sources

IMAGE_FIELDS = ["image_url", "image_bucket", "image_path", "image_access_type"]

PROFILE_BUILDER_CAPTURE = {
    "Recipe / Meal": ["reference_label", "portion", "instruction"],
    "Exercise": ["reference_label", "scheduled_time", "intensity", "instruction"],
    "Supplement": ["reference_label", "scheduled_time", "dosage_frequency", "instruction"],
}

SUPPLEMENT_REGIMEN_FIELDS = [
    "supplement_name",
    "dosage",
    "frequency",
    "timing",
    "instructions",
    "start_date",
    "end_date",
    "admin_notes",
    "status",
]


def _clean(value: object) -> str:
    return str(value or "").strip()


def _option_set(values: List[str]) -> Set[str]:
    cleaned = set()
    for value in values or []:
        text = _clean(value)
        if not text or text.startswith("-- Select"):
            continue
        cleaned.add(text.lower())
    return cleaned


def _title_set(rows: List[Dict[str, Any]]) -> Set[str]:
    return {_clean(row.get("title")).lower() for row in rows if _clean(row.get("title"))}


def _missing_labels(repo_rows: List[Dict[str, Any]], options: List[str]) -> List[str]:
    option_lookup = _option_set(options)
    missing = []
    for row in repo_rows:
        title = _clean(row.get("title"))
        if title and title.lower() not in option_lookup:
            missing.append(title)
    return sorted(set(missing), key=str.lower)


def _image_count(rows: List[Dict[str, Any]]) -> int:
    count = 0
    for row in rows:
        if any(_clean(row.get(field)) for field in IMAGE_FIELDS):
            count += 1
    return count


def _unique_active_supplement_names(rows: List[Dict[str, Any]]) -> List[str]:
    names = []
    for row in rows:
        name = _clean(row.get("supplement_name"))
        if name:
            names.append(name)
    return sorted(set(names), key=str.lower)


def build_alignment_snapshot() -> Dict[str, Any]:
    try:
        sources, source_message = load_profile_builder_sources()
    except Exception as exc:
        sources = {key: list(values) for key, values in DEFAULT_SOURCES.items()}
        source_message = f"Using fallback Profile Builder source values because master data could not be loaded: {exc}"

    try:
        recipe_rows = list_repository_items("recipes", active_only=True)
        recipe_error = ""
    except Exception as exc:
        recipe_rows = []
        recipe_error = str(exc)

    try:
        exercise_rows = list_repository_items("exercises", active_only=True)
        exercise_error = ""
    except Exception as exc:
        exercise_rows = []
        exercise_error = str(exc)

    try:
        active_supplements = list_member_supplements(status="Active")
        supplement_error = ""
    except Exception as exc:
        active_supplements = []
        supplement_error = str(exc)

    recipe_options = sources.get("recipe", [])
    exercise_options = sources.get("exercise", [])
    supplement_options = sources.get("supplement", [])
    supplement_names = _unique_active_supplement_names(active_supplements)

    return {
        "source_message": source_message,
        "recipe_rows": recipe_rows,
        "exercise_rows": exercise_rows,
        "active_supplements": active_supplements,
        "recipe_error": recipe_error,
        "exercise_error": exercise_error,
        "supplement_error": supplement_error,
        "recipe_options": recipe_options,
        "exercise_options": exercise_options,
        "supplement_options": supplement_options,
        "recipe_missing_in_builder": _missing_labels(recipe_rows, recipe_options),
        "exercise_missing_in_builder": _missing_labels(exercise_rows, exercise_options),
        "supplement_missing_in_builder": sorted(_title_set([{"title": n} for n in supplement_names]) - _option_set(supplement_options)),
        "recipe_images": _image_count(recipe_rows),
        "exercise_images": _image_count(exercise_rows),
        "supplement_names": supplement_names,
    }


def _count_cards(snapshot: Dict[str, Any]) -> None:
    recipe_count = len(snapshot["recipe_rows"])
    exercise_count = len(snapshot["exercise_rows"])
    supplement_count = len(snapshot["supplement_names"])
    missing_total = (
        len(snapshot["recipe_missing_in_builder"])
        + len(snapshot["exercise_missing_in_builder"])
        + len(snapshot["supplement_missing_in_builder"])
    )
    st.markdown(
        f"""
<div class='hm-count-grid'>
  <div class='hm-count-card'><b>{recipe_count}</b><span>Active recipe repository rows</span></div>
  <div class='hm-count-card'><b>{exercise_count}</b><span>Active exercise repository rows</span></div>
  <div class='hm-count-card'><b>{supplement_count}</b><span>Unique active supplement names</span></div>
  <div class='hm-count-card'><b>{missing_total}</b><span>Source labels missing from builder dropdowns</span></div>
</div>
""",
        unsafe_allow_html=True,
    )


def _coverage_table(snapshot: Dict[str, Any]) -> pd.DataFrame:
    recipe_not_preserved = [field for field in RECIPE_COLUMNS if field not in ["title", "portion_size"]]
    exercise_not_preserved = [field for field in EXERCISE_COLUMNS if field not in ["title"]]
    supplement_not_preserved = [field for field in SUPPLEMENT_REGIMEN_FIELDS if field not in ["supplement_name", "dosage", "frequency", "timing", "instructions"]]
    return pd.DataFrame([
        {
            "Repository": "Recipe Repository",
            "Current Profile Builder capture": ", ".join(PROFILE_BUILDER_CAPTURE["Recipe / Meal"]),
            "Important source fields not preserved yet": ", ".join(recipe_not_preserved),
            "Image references present": snapshot["recipe_images"],
            "Current judgement": "Not aligned — builder captures label and override only, not full recipe snapshot.",
        },
        {
            "Repository": "Exercise Repository",
            "Current Profile Builder capture": ", ".join(PROFILE_BUILDER_CAPTURE["Exercise"]),
            "Important source fields not preserved yet": ", ".join(exercise_not_preserved),
            "Image references present": snapshot["exercise_images"],
            "Current judgement": "Not aligned — integrated exercise details are being re-entered instead of pulled.",
        },
        {
            "Repository": "Supplement Regimen",
            "Current Profile Builder capture": ", ".join(PROFILE_BUILDER_CAPTURE["Supplement"]),
            "Important source fields not preserved yet": ", ".join(supplement_not_preserved),
            "Image references present": "NA",
            "Current judgement": "Partially aligned — supplement name/dose/frequency can match, but active regimen lifecycle is not pulled.",
        },
    ])


def _missing_table(snapshot: Dict[str, Any]) -> pd.DataFrame:
    rows = []
    for source_key, label in [
        ("recipe_missing_in_builder", "Recipe"),
        ("exercise_missing_in_builder", "Exercise"),
        ("supplement_missing_in_builder", "Supplement"),
    ]:
        missing = snapshot[source_key]
        rows.append({
            "Source": label,
            "Missing count": len(missing),
            "Examples": "None" if not missing else ", ".join(missing[:12]),
        })
    return pd.DataFrame(rows)


def render_profile_source_alignment() -> None:
    st.markdown(
        "<div class='hm-title'>Repository-to-Profile Builder Source Alignment</div>"
        "<div class='hm-sub'>Contract-first diagnostic before member recommendation consumption. This checks whether Profile Builder is using the full Recipe, Exercise and Supplement sources, or only partial dropdown labels.</div>",
        unsafe_allow_html=True,
    )

    snapshot = build_alignment_snapshot()
    st.caption(snapshot["source_message"])
    for key, label in [("recipe_error", "Recipe repository"), ("exercise_error", "Exercise repository"), ("supplement_error", "Supplement regimen")]:
        if snapshot.get(key):
            st.warning(f"{label} could not be fully read: {snapshot[key]}")

    _count_cards(snapshot)

    st.markdown("<div class='hm-title'>Coverage Assessment</div>", unsafe_allow_html=True)
    st.dataframe(_coverage_table(snapshot), use_container_width=True, hide_index=True)

    st.markdown("<div class='hm-title'>Dropdown Alignment Check</div>", unsafe_allow_html=True)
    st.dataframe(_missing_table(snapshot), use_container_width=True, hide_index=True)

    st.markdown("<div class='hm-title'>Recommended Member Consumption Contract</div>", unsafe_allow_html=True)
    st.markdown(
        """
<div class='hm-preview'>
<b>Recommended direction before member-facing display:</b><br>
1. Profile Builder should select the repository item, not duplicate it manually.<br>
2. Save the selected source id/name plus a full snapshot of recipe/exercise/supplement details at publish time.<br>
3. Admin override fields should remain available for portion, time, intensity, dosage and instructions.<br>
4. Image references should be preserved in the contract, but images do not need to render in normal admin editing.<br>
5. Member web / Flutter should receive the full snapshot and decide where to show images, instructions and details.
</div>
""",
        unsafe_allow_html=True,
    )

    with st.expander("Field-level source maps", expanded=False):
        st.markdown("**Recipe repository fields**")
        st.write(RECIPE_COLUMNS)
        st.markdown("**Exercise repository fields**")
        st.write(EXERCISE_COLUMNS)
        st.markdown("**Supplement regimen fields**")
        st.write(SUPPLEMENT_REGIMEN_FIELDS)
