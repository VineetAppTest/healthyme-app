from __future__ import annotations

import copy
from typing import Any, Callable

from components.exercise_repository import list_exercise_repository
from components.recommendation_contract import list_repository_items
from components.supplement_repository import list_supplement_repository


CONTRACT_VERSION = "2026-08-03-v1"
SUPPORTED_KINDS = ("recipe", "exercise", "supplement")

_CONTRACT_MANIFEST: dict[str, Any] = {
    "contract_version": CONTRACT_VERSION,
    "identity_rule": "source_id is authoritative; display_label is presentation only",
    "selection_rule": "only active repository items are selectable for new recommendations",
    "history_rule": (
        "saved recommendation source snapshots remain immutable and readable after "
        "repository edits or deactivation"
    ),
    "repositories": {
        "recipe": {
            "source_type": "recipe_repository",
            "storage_authority": "data/recipes.csv compatibility repository",
            "id_strategy": (
                "numeric compatibility row ID; physical deletion and reindexing are prohibited "
                "until the durable Recipe migration"
            ),
        },
        "exercise": {
            "source_type": "exercise_repository",
            "storage_authority": "Supabase-backed application state: exercises",
            "id_strategy": "persistent numeric repository ID",
        },
        "supplement": {
            "source_type": "supplement_repository",
            "storage_authority": "Supabase-backed application state: supplement_repository",
            "id_strategy": "persistent suprepo_* repository ID",
            "excluded_from_new_snapshot": [
                "member allocation",
                "member-specific start_date",
                "member-specific end_date",
                "admin_notes",
            ],
        },
    },
}


def _clean(value: Any) -> str:
    text = str(value or "").strip()
    return "" if text.lower() in {"nan", "none", "null"} else text


def _status(value: Any) -> str:
    return (
        "inactive"
        if _clean(value).lower() in {"inactive", "stopped", "archived"}
        else "active"
    )


def _image_reference(row: dict[str, Any]) -> dict[str, str]:
    return {
        "image_url": _clean(row.get("image_url")),
        "image_bucket": _clean(row.get("image_bucket")),
        "image_path": _clean(row.get("image_path")),
        "image_access_type": _clean(row.get("image_access_type")),
    }


def _required_source_id(row: dict[str, Any], kind: str) -> str:
    source_id = _clean(row.get("source_id") or row.get("id"))
    if not source_id:
        raise ValueError(f"{kind.title()} repository item is missing source_id.")
    return source_id


def _required_title(row: dict[str, Any], kind: str) -> str:
    if kind == "supplement":
        title = _clean(
            row.get("supplement_name") or row.get("title") or row.get("name")
        )
    else:
        title = _clean(row.get("title"))
    if not title:
        raise ValueError(f"{kind.title()} repository item is missing its display title.")
    return title


def _recipe_snapshot(row: dict[str, Any], source_id: str, title: str) -> dict[str, Any]:
    return {
        "contract_version": CONTRACT_VERSION,
        "source_type": "recipe_repository",
        "source_id": source_id,
        "title": title,
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
        "status": _status(row.get("status")),
        "image": _image_reference(row),
    }


def _exercise_snapshot(
    row: dict[str, Any], source_id: str, title: str
) -> dict[str, Any]:
    return {
        "contract_version": CONTRACT_VERSION,
        "source_type": "exercise_repository",
        "source_id": source_id,
        "title": title,
        "description": _clean(row.get("description")),
        "category": _clean(row.get("category")),
        "difficulty": _clean(row.get("difficulty")),
        "goal_tags": _clean(row.get("goal_tags")),
        "condition_tags": _clean(row.get("condition_tags")),
        "duration_or_reps": _clean(row.get("duration_or_reps")),
        "equipment": _clean(row.get("equipment")),
        "instructions": _clean(row.get("instructions")),
        "benefits": _clean(row.get("benefits")),
        "status": _status(row.get("status")),
        "image": _image_reference(row),
    }


def _supplement_snapshot(
    row: dict[str, Any], source_id: str, title: str
) -> dict[str, Any]:
    # Member allocation, regimen dates and Admin Notes deliberately do not belong to
    # the reusable repository source contract. They are member-plan concerns.
    return {
        "contract_version": CONTRACT_VERSION,
        "source_type": "supplement_repository",
        "source_id": source_id,
        "title": title,
        "supplement_name": title,
        "dosage": _clean(row.get("dosage")),
        "frequency": _clean(row.get("frequency")),
        "timing": _clean(row.get("timing")),
        "instructions": _clean(row.get("instructions")),
        "status": _status(row.get("status")),
    }


_SNAPSHOT_BUILDERS: dict[
    str, Callable[[dict[str, Any], str, str], dict[str, Any]]
] = {
    "recipe": _recipe_snapshot,
    "exercise": _exercise_snapshot,
    "supplement": _supplement_snapshot,
}


def canonical_repository_contract_manifest() -> dict[str, Any]:
    """Return a defensive copy of the frozen repository rules."""
    return copy.deepcopy(_CONTRACT_MANIFEST)


def normalise_profile_builder_repository_source(
    kind: str, row: dict[str, Any]
) -> dict[str, Any]:
    """Normalise one repository row into the common Profile Builder envelope."""
    kind = _clean(kind).lower()
    if kind not in SUPPORTED_KINDS:
        raise ValueError(
            "kind must be one of: recipe, exercise or supplement"
        )

    source = dict(row or {})
    source_id = _required_source_id(source, kind)
    title = _required_title(source, kind)
    status = _status(source.get("status"))
    snapshot = _SNAPSHOT_BUILDERS[kind](source, source_id, title)
    source_type = str(snapshot["source_type"])

    return {
        "contract_version": CONTRACT_VERSION,
        "kind": kind,
        "source_type": source_type,
        "source_id": source_id,
        "identity_key": f"{source_type}:{source_id}",
        "display_label": title,
        "status": status,
        "selectable": status == "active",
        "snapshot": copy.deepcopy(snapshot),
    }


def _load_repository_rows(kind: str, active_only: bool) -> list[dict[str, Any]]:
    if kind == "recipe":
        return list_repository_items("recipes", active_only=active_only)
    if kind == "exercise":
        return list_exercise_repository(active_only=active_only)
    if kind == "supplement":
        return list_supplement_repository(active_only=active_only)
    raise ValueError("Unsupported repository kind.")


def list_profile_builder_repository_sources(
    kind: str, *, active_only: bool = True
) -> list[dict[str, Any]]:
    """Read one repository directly and return canonical, defensive source objects."""
    kind = _clean(kind).lower()
    if kind not in SUPPORTED_KINDS:
        raise ValueError(
            "kind must be one of: recipe, exercise or supplement"
        )

    rows = _load_repository_rows(kind, active_only)
    sources: list[dict[str, Any]] = []
    identities: set[str] = set()
    for row in rows:
        source = normalise_profile_builder_repository_source(kind, dict(row or {}))
        if active_only and not source["selectable"]:
            continue
        identity = str(source["identity_key"])
        if identity in identities:
            raise ValueError(f"Duplicate canonical repository identity: {identity}")
        identities.add(identity)
        sources.append(source)

    sources.sort(
        key=lambda source: (
            str(source.get("display_label", "")).casefold(),
            str(source.get("source_id", "")),
        )
    )
    return copy.deepcopy(sources)


def profile_builder_repository_source_by_id(
    kind: str, source_id: str, *, active_only: bool = False
) -> dict[str, Any] | None:
    """Resolve a source by canonical ID; labels are never used as identity."""
    expected_id = _clean(source_id)
    if not expected_id:
        return None
    for source in list_profile_builder_repository_sources(
        kind, active_only=active_only
    ):
        if str(source.get("source_id")) == expected_id:
            return copy.deepcopy(source)
    return None
