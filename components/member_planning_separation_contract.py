from __future__ import annotations

import copy
from typing import Any, Iterable


CONTRACT_VERSION = "2026-08-03-v1"

_DOMAIN_ALIASES = {
    "meal": "meal",
    "meals": "meal",
    "recipe": "meal",
    "recipes": "meal",
    "exercise": "exercise",
    "exercises": "exercise",
    "workout": "exercise",
    "workouts": "exercise",
    "supplement": "supplement",
    "supplements": "supplement",
}

_CONTRACT_MANIFEST: dict[str, Any] = {
    "contract_version": CONTRACT_VERSION,
    "objective": (
        "Separate meal-profile design from Exercise and Supplement member allocation "
        "while keeping Current Member Plan as a consolidated read model."
    ),
    "identity_rule": (
        "member allocations reference canonical repository source_type + source_id; "
        "display labels are never identity"
    ),
    "history_rule": (
        "existing allocations, recommendation shares and immutable source snapshots "
        "remain readable throughout migration"
    ),
    "current_inventory": {
        "meal_structure": {
            "store_key": "meal_type_repository",
            "shape": "array",
            "observed_rows": 6,
        },
        "meal_allocations": {
            "store_key": "member_recipe_allocations",
            "shape": "object keyed by member_id containing allocation arrays",
            "canonical_source_type": "recipe_repository",
            "source_id_field": "recipe_id",
            "observed_member_buckets": 1,
        },
        "exercise_allocations": {
            "store_key": "member_exercise_allocations",
            "shape": "object keyed by member_id containing allocation arrays",
            "canonical_source_type": "exercise_repository",
            "source_id_field": "exercise_id",
            "observed_member_buckets": 1,
        },
        "supplement_allocations": {
            "store_key": "member_supplements",
            "shape": "array",
            "canonical_source_type": "supplement_repository",
            "source_id_field": None,
            "observed_rows": 6,
            "migration_gap": (
                "current member_supplements rows do not expose a dedicated canonical "
                "supplement repository source_id field; Phase D must add a compatibility "
                "mapping without replacing existing allocation IDs"
            ),
        },
        "published_member_plan": {
            "store_key": "recommendation_shares",
            "shape": "object keyed by member_id",
            "observed_member_buckets": 1,
        },
    },
    "target_workflows": {
        "meal_profile_builder": {
            "owns": ["profile_setup", "meal_structure", "meal_source_snapshots"],
            "allowed_domains": ["meal"],
            "excluded_domains": ["exercise", "supplement"],
            "write_authority": True,
        },
        "exercise_member_allocation": {
            "owns": [
                "member_id",
                "exercise_source_reference",
                "start_date",
                "end_date",
                "instructions",
                "notes",
                "allocation_status",
            ],
            "allowed_domains": ["exercise"],
            "write_authority": True,
        },
        "supplement_member_allocation": {
            "owns": [
                "member_id",
                "supplement_source_reference",
                "dosage",
                "frequency",
                "timing",
                "start_date",
                "end_date",
                "instructions",
                "allocation_status",
            ],
            "allowed_domains": ["supplement"],
            "write_authority": True,
            "excluded_repository_fields": ["admin_notes"],
        },
        "current_member_plan": {
            "owns": ["meal_read_model", "exercise_read_model", "supplement_read_model"],
            "allowed_domains": ["meal", "exercise", "supplement"],
            "write_authority": False,
            "rule": "consolidated read model only; never another persistence authority",
        },
    },
    "delivery_sequence": [
        "contract_and_inventory_freeze",
        "meal_profile_builder_meals_only",
        "exercise_member_allocation",
        "supplement_member_allocation",
        "current_member_plan_consolidation",
    ],
}


def _clean(value: Any) -> str:
    return str(value or "").strip()


def normalise_member_planning_domain(value: str) -> str:
    domain = _DOMAIN_ALIASES.get(_clean(value).lower())
    if not domain:
        raise ValueError("domain must be meal, exercise or supplement")
    return domain


def member_planning_separation_manifest() -> dict[str, Any]:
    """Return a defensive copy of the frozen Member Planning separation contract."""
    return copy.deepcopy(_CONTRACT_MANIFEST)


def workflow_for_domain(domain: str) -> str:
    normalised = normalise_member_planning_domain(domain)
    return {
        "meal": "meal_profile_builder",
        "exercise": "exercise_member_allocation",
        "supplement": "supplement_member_allocation",
    }[normalised]


def allocation_store_for_domain(domain: str) -> str:
    normalised = normalise_member_planning_domain(domain)
    inventory_key = {
        "meal": "meal_allocations",
        "exercise": "exercise_allocations",
        "supplement": "supplement_allocations",
    }[normalised]
    return str(
        _CONTRACT_MANIFEST["current_inventory"][inventory_key]["store_key"]
    )


def canonical_source_type_for_domain(domain: str) -> str:
    normalised = normalise_member_planning_domain(domain)
    inventory_key = {
        "meal": "meal_allocations",
        "exercise": "exercise_allocations",
        "supplement": "supplement_allocations",
    }[normalised]
    return str(
        _CONTRACT_MANIFEST["current_inventory"][inventory_key][
            "canonical_source_type"
        ]
    )


def validate_meal_profile_builder_domains(domains: Iterable[str]) -> tuple[str, ...]:
    """Reject Exercise or Supplement ownership inside Meal Profile Builder."""
    normalised = tuple(normalise_member_planning_domain(domain) for domain in domains)
    forbidden = sorted({domain for domain in normalised if domain != "meal"})
    if forbidden:
        raise ValueError(
            "Meal Profile Builder may own meal concerns only; remove: "
            + ", ".join(forbidden)
        )
    return normalised


def validate_canonical_source_reference(
    domain: str, source_type: str, source_id: str
) -> dict[str, str]:
    """Validate a repository reference without creating a new allocation identity."""
    normalised = normalise_member_planning_domain(domain)
    expected_source_type = canonical_source_type_for_domain(normalised)
    actual_source_type = _clean(source_type)
    actual_source_id = _clean(source_id)
    if actual_source_type != expected_source_type:
        raise ValueError(
            f"{normalised.title()} allocation must reference {expected_source_type}."
        )
    if not actual_source_id:
        raise ValueError(f"{normalised.title()} allocation source_id is required.")
    return {
        "domain": normalised,
        "source_type": actual_source_type,
        "source_id": actual_source_id,
        "identity_key": f"{actual_source_type}:{actual_source_id}",
    }


def current_member_plan_is_read_only() -> bool:
    return not bool(
        _CONTRACT_MANIFEST["target_workflows"]["current_member_plan"][
            "write_authority"
        ]
    )
