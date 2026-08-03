from __future__ import annotations

import csv
import pathlib

import pytest

from components.content_repository_migration import (
    _recipe_rows,
    build_migration_plan,
    repository_checksum,
)
from components.content_repository_store import (
    normalise_legacy_item,
    repository_identity,
    validate_unique_identities,
)


ROOT = pathlib.Path(__file__).resolve().parents[1]
MIGRATION = (
    ROOT
    / "supabase"
    / "migrations"
    / "20260803094700_create_standard_content_repository.sql"
)


def test_recipe_legacy_id_and_payload_are_preserved() -> None:
    item = normalise_legacy_item(
        "recipe",
        {
            "title": "Moong Chilla",
            "meal_type": "Breakfast",
            "status": "Active",
        },
        fallback_source_id="7",
    )

    assert repository_identity(item) == ("recipe", "7")
    assert item["display_name"] == "Moong Chilla"
    assert item["status"] == "active"
    assert item["payload"]["title"] == "Moong Chilla"
    assert item["payload"]["meal_type"] == "Breakfast"


def test_exercise_numeric_id_is_not_renumbered() -> None:
    item = normalise_legacy_item(
        "exercise",
        {
            "id": "2",
            "source_id": "2",
            "title": "Mobility Flow",
            "status": "inactive",
            "duration_or_reps": "15 minutes",
        },
    )

    assert repository_identity(item) == ("exercise", "2")
    assert item["status"] == "inactive"
    assert item["payload"]["duration_or_reps"] == "15 minutes"


def test_supplement_master_id_is_not_replaced_by_name() -> None:
    item = normalise_legacy_item(
        "supplement",
        {
            "id": "suprepo_abc12345",
            "supplement_name": "Vitamin D",
            "status": "Active",
            "dosage": "1 tablet",
        },
    )

    assert repository_identity(item) == ("supplement", "suprepo_abc12345")
    assert item["display_name"] == "Vitamin D"
    assert item["payload"]["supplement_name"] == "Vitamin D"


def test_same_visible_name_is_safe_across_different_identities() -> None:
    items = [
        normalise_legacy_item(
            "recipe",
            {"id": "1", "title": "Shared Name", "status": "active"},
        ),
        normalise_legacy_item(
            "recipe",
            {"id": "2", "title": "Shared Name", "status": "active"},
        ),
        normalise_legacy_item(
            "exercise",
            {"id": "1", "title": "Shared Name", "status": "active"},
        ),
    ]

    validate_unique_identities(items)
    assert len({repository_identity(item) for item in items}) == 3


def test_duplicate_composite_identity_is_rejected() -> None:
    items = [
        normalise_legacy_item(
            "recipe",
            {"id": "1", "title": "Recipe A", "status": "active"},
        ),
        normalise_legacy_item(
            "recipe",
            {"id": "1", "title": "Recipe B", "status": "active"},
        ),
    ]

    with pytest.raises(ValueError, match="Duplicate Content Repository identity"):
        validate_unique_identities(items)


def test_recipe_csv_row_position_becomes_compatibility_id(tmp_path: pathlib.Path) -> None:
    path = tmp_path / "recipes.csv"
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["title", "status", "meal_type"])
        writer.writeheader()
        writer.writerow({"title": "Recipe A", "status": "active", "meal_type": "Lunch"})
        writer.writerow({"title": "Recipe B", "status": "inactive", "meal_type": "Dinner"})

    items = _recipe_rows(path)

    assert [item["source_id"] for item in items] == ["0", "1"]
    assert items[1]["status"] == "inactive"
    assert items[1]["legacy_reference"].endswith(":1")


def test_migration_plan_is_deterministic() -> None:
    items = [
        normalise_legacy_item(
            "supplement",
            {"id": "suprepo_b", "supplement_name": "B", "status": "active"},
        ),
        normalise_legacy_item(
            "recipe",
            {"id": "0", "title": "A", "status": "active"},
        ),
    ]
    first = build_migration_plan(items)
    second = build_migration_plan(reversed(items))

    assert first["counts"] == {"recipe": 1, "exercise": 0, "supplement": 1}
    assert first["checksums"] == second["checksums"]
    assert repository_checksum(items) == repository_checksum(reversed(items))


def test_schema_uses_one_composite_identity_and_append_only_audit() -> None:
    sql = MIGRATION.read_text(encoding="utf-8")

    assert "create table if not exists public.hm_content_repository_items" in sql
    assert "create table if not exists public.hm_content_repository_events" in sql
    assert "unique (repository_type, source_id)" in sql
    assert "repository_type in ('recipe', 'exercise', 'supplement')" in sql
    assert "status in ('active', 'inactive')" in sql
    assert "content_version := old.content_version + 1" in sql
    assert "Content Repository identity cannot be changed" in sql
    assert "on delete restrict" in sql
    assert "enable row level security" in sql
    assert "revoke all on table public.hm_content_repository_items from public, anon, authenticated" in sql
    assert "grant select, insert, update on table public.hm_content_repository_items to service_role" in sql
    assert "grant delete" not in sql.lower()


def test_phase_a_does_not_wire_live_repository_pages() -> None:
    for relative_path in (
        "pages/15_Admin_Recipe_Manager.py",
        "pages/16_Admin_Exercise_Manager.py",
        "pages/39_Admin_Supplement_Manager.py",
    ):
        page = (ROOT / relative_path).read_text(encoding="utf-8")
        assert "content_repository_store" not in page
        assert "content_repository_migration" not in page
