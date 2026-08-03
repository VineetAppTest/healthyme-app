"""Controlled backfill utilities for the standard Content Repository.

The migration is dry-run by default. No repository page imports this module and no
backfill runs during normal application rendering. A later approved cutover can
call ``backfill_content_repositories(commit=True)`` after the schema is present.
"""

from __future__ import annotations

import csv
import hashlib
import json
import pathlib
from typing import Any, Dict, Iterable, List, Mapping

from components.content_repository_store import (
    list_repository_items,
    normalise_legacy_item,
    repository_identity,
    save_repository_item,
    validate_unique_identities,
)


BASE_DIR = pathlib.Path(__file__).resolve().parents[1]
LEGACY_RECIPE_PATH = BASE_DIR / "data" / "recipes.csv"


def _recipe_rows(path: pathlib.Path = LEGACY_RECIPE_PATH) -> List[dict]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = [dict(row) for row in csv.DictReader(handle)]

    canonical: List[dict] = []
    for index, row in enumerate(rows):
        enriched = {
            **row,
            "source_system": "recipe_csv",
            "legacy_reference": f"data/recipes.csv:{index}",
        }
        canonical.append(
            normalise_legacy_item("recipe", enriched, fallback_source_id=str(index))
        )
    return canonical


def _legacy_app_state() -> Dict[str, Any]:
    """Read the current Supabase app-state authority without normalising it."""
    from components.storage_backend import (
        get_storage_status,
        load_state,
        supabase_configured,
    )

    state = load_state(force_refresh=True)
    status = get_storage_status()
    if supabase_configured() and status.get("mode") != "SUPABASE":
        raise RuntimeError(
            "Content Repository migration inventory refused the local fallback. "
            "Restore the Supabase connection before planning or committing the backfill."
        )
    return dict(state or {})


def _exercise_rows(state: Mapping[str, Any]) -> List[dict]:
    canonical: List[dict] = []
    for index, row in enumerate(list(state.get("exercises") or [])):
        enriched = {
            **dict(row or {}),
            "source_system": str((row or {}).get("source") or "healthyme_app_state:exercises"),
            "legacy_reference": f"healthyme_app_state.data.exercises:{index}",
        }
        canonical.append(normalise_legacy_item("exercise", enriched))
    return canonical


def _supplement_rows(state: Mapping[str, Any]) -> List[dict]:
    canonical: List[dict] = []
    for index, row in enumerate(list(state.get("supplement_repository") or [])):
        enriched = {
            **dict(row or {}),
            "source_system": str(
                (row or {}).get("source")
                or "healthyme_app_state:supplement_repository"
            ),
            "legacy_reference": (
                f"healthyme_app_state.data.supplement_repository:{index}"
            ),
        }
        canonical.append(normalise_legacy_item("supplement", enriched))
    return canonical


def build_legacy_repository_items() -> List[dict]:
    """Load all three current authorities without writing to any of them."""
    state = _legacy_app_state()
    items = [
        *_recipe_rows(),
        *_exercise_rows(state),
        *_supplement_rows(state),
    ]
    validate_unique_identities(items)
    return items


def _checksum_projection(item: Mapping[str, Any]) -> Dict[str, Any]:
    return {
        "repository_type": str(item.get("repository_type") or ""),
        "source_id": str(item.get("source_id") or ""),
        "display_name": str(item.get("display_name") or ""),
        "status": str(item.get("status") or ""),
        "payload": dict(item.get("payload") or {}),
        "source_system": str(item.get("source_system") or ""),
        "legacy_reference": str(item.get("legacy_reference") or ""),
    }


def repository_checksum(items: Iterable[Mapping[str, Any]]) -> str:
    projected = sorted(
        [_checksum_projection(item) for item in items],
        key=lambda item: (item["repository_type"], item["source_id"]),
    )
    encoded = json.dumps(
        projected,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def build_migration_plan(items: Iterable[Mapping[str, Any]] | None = None) -> Dict[str, Any]:
    canonical = list(items) if items is not None else build_legacy_repository_items()
    validate_unique_identities(canonical)

    by_type: Dict[str, List[dict]] = {
        "recipe": [],
        "exercise": [],
        "supplement": [],
    }
    for item in canonical:
        by_type[item["repository_type"]].append(dict(item))

    return {
        "total": len(canonical),
        "counts": {kind: len(rows) for kind, rows in by_type.items()},
        "checksums": {kind: repository_checksum(rows) for kind, rows in by_type.items()},
        "identities": sorted(
            [f"{kind}:{source_id}" for kind, source_id in map(repository_identity, canonical)]
        ),
        "items": canonical,
    }


def _destination_projection(repository_type: str) -> List[dict]:
    return [
        _checksum_projection(row)
        for row in list_repository_items(repository_type, active_only=False)
    ]


def backfill_content_repositories(
    *,
    commit: bool = False,
    actor_id: str = "system:content_repository_migration",
) -> Dict[str, Any]:
    """Plan or perform the controlled backfill.

    ``commit=False`` is intentionally the default. When committed, every item is
    written through the verified canonical store and then compared by identity and
    checksum. Legacy CSV/app-state authorities remain untouched.
    """
    plan = build_migration_plan()
    result: Dict[str, Any] = {
        "committed": False,
        "source_counts": dict(plan["counts"]),
        "source_checksums": dict(plan["checksums"]),
        "source_identities": list(plan["identities"]),
    }
    if not commit:
        result["message"] = "Dry run complete. No Content Repository rows were written."
        return result

    written: List[dict] = []
    for item in plan["items"]:
        written.append(
            save_repository_item(
                item["repository_type"],
                item["source_id"],
                item["display_name"],
                item["payload"],
                status=item["status"],
                actor_id=actor_id,
                source_system=item.get("source_system") or "legacy",
                legacy_reference=item.get("legacy_reference") or "",
            )
        )

    destination_by_type = {
        kind: _destination_projection(kind)
        for kind in ("recipe", "exercise", "supplement")
    }
    expected_identities = {
        repository_identity(item)
        for item in plan["items"]
    }
    actual_identities = {
        repository_identity(item)
        for rows in destination_by_type.values()
        for item in rows
    }
    missing = sorted(
        f"{kind}:{source_id}"
        for kind, source_id in expected_identities - actual_identities
    )

    destination_checksums: Dict[str, str] = {}
    checksum_mismatches: List[str] = []
    for kind in ("recipe", "exercise", "supplement"):
        expected_rows = [
            item for item in plan["items"] if item["repository_type"] == kind
        ]
        expected_ids = {item["source_id"] for item in expected_rows}
        actual_rows = [
            item
            for item in destination_by_type[kind]
            if item["source_id"] in expected_ids
        ]
        destination_checksums[kind] = repository_checksum(actual_rows)
        if destination_checksums[kind] != plan["checksums"][kind]:
            checksum_mismatches.append(kind)

    if missing or checksum_mismatches:
        detail = []
        if missing:
            detail.append(f"missing identities: {', '.join(missing)}")
        if checksum_mismatches:
            detail.append(
                f"checksum mismatch: {', '.join(checksum_mismatches)}"
            )
        raise RuntimeError(
            "Content Repository backfill verification failed; " + "; ".join(detail)
        )

    result.update(
        {
            "committed": True,
            "written": len(written),
            "destination_counts": {
                kind: len(rows) for kind, rows in destination_by_type.items()
            },
            "destination_checksums": destination_checksums,
            "message": "Backfill completed and all source identities/checksums were verified.",
        }
    )
    return result
