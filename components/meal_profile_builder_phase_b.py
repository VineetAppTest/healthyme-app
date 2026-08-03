from __future__ import annotations

import copy
from typing import Any, Iterable


CONTRACT_VERSION = "2026-08-04-acceptance-v1"
MEAL_EDITABLE_ITEM_TYPES = ("meal",)
LEGACY_READ_ONLY_ITEM_TYPES = ("exercise", "supplement")
ALLOCATION_WORKSPACE_SECTION = "Allocate Exercise & Supplement"
VIEW_PROFILES_SECTION = "View Profiles"
MEAL_PROFILE_BUILDER_SECTIONS = (
    "Profile Setup",
    "Meal Structure",
    ALLOCATION_WORKSPACE_SECTION,
    VIEW_PROFILES_SECTION,
)


def _clean(value: Any) -> str:
    return str(value or "").strip().lower()


def is_meal_profile_builder_editable_type(item_type: object) -> bool:
    return _clean(item_type) in MEAL_EDITABLE_ITEM_TYPES


def is_legacy_read_only_type(item_type: object) -> bool:
    return _clean(item_type) in LEGACY_READ_ONLY_ITEM_TYPES


def split_profile_items(items: Iterable[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    """Classify loaded rows without mutating historical profile content."""
    output = {
        "meal": [],
        "legacy_exercise": [],
        "legacy_supplement": [],
        "other": [],
    }
    for source in items or []:
        row = copy.deepcopy(dict(source or {}))
        item_type = _clean(row.get("item_type"))
        if item_type == "meal":
            output["meal"].append(row)
        elif item_type == "exercise":
            output["legacy_exercise"].append(row)
        elif item_type == "supplement":
            output["legacy_supplement"].append(row)
        else:
            output["other"].append(row)
    return output


def meal_profile_builder_manifest() -> dict[str, Any]:
    return {
        "contract_version": CONTRACT_VERSION,
        "editable_item_types": list(MEAL_EDITABLE_ITEM_TYPES),
        "legacy_read_only_item_types": list(LEGACY_READ_ONLY_ITEM_TYPES),
        "visible_sections": list(MEAL_PROFILE_BUILDER_SECTIONS),
        "route": "pages/38_Admin_Recommendation_Profile_Builder.py",
        "write_rule": "only meal rows may be replaced from Meal Profile Builder",
        "history_rule": (
            "existing Exercise and Supplement rows remain readable and publishable; "
            "Setup and Meal saves must not rewrite or delete them"
        ),
        "navigation_rule": (
            "Preview and Publish render inside Meal Structure; Exercise and Supplement "
            "allocation launch from one compact workspace while retaining independent stores"
        ),
        "allocation_routes": [
            "pages/42_Admin_Exercise_Member_Allocation.py",
            "pages/43_Admin_Supplement_Member_Allocation.py",
        ],
        "next_workflows": [
            "production_acceptance",
            "flutter_after_production_acceptance",
        ],
    }
