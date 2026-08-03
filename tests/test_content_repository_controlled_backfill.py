from __future__ import annotations

import json
import pathlib
import re
import unittest

from components.content_repository_migration import (
    _exercise_rows,
    _recipe_rows,
    _supplement_rows,
    build_migration_plan,
    repository_checksum,
)


ROOT = pathlib.Path(__file__).resolve().parents[1]
MIGRATION = (
    ROOT
    / "supabase"
    / "migrations"
    / "20260803102500_backfill_standard_content_repository.sql"
)
INVENTORY = ROOT / "docs" / "content_repository_source_inventory_2026-08-03.md"

EXPECTED_CHECKSUMS = {
    "recipe": "a61af93dec4052ed2b3c8160657be594e5bab68a8e63b554fbd6eb745edce48f",
    "exercise": "585764b996d1952226405966efada936b87eae4cfa0f2a6120433f5f560e4716",
    "supplement": "4bb7bcb320b0cb1c83981d38531f14db9c020b0a61b1d74b3765f0b09865bf96",
    "total": "52ac68b76032cfdacba2686cf85c7d3b4d954f8d54589ba67890a0af11c40f5e",
}

EXPECTED_IDENTITIES = [
    "exercise:0",
    "exercise:1",
    "exercise:2",
    "recipe:0",
    "recipe:1",
    "supplement:suprepo_2ceffd32",
    "supplement:suprepo_4b3c1e53",
    "supplement:suprepo_c88d2def",
    "supplement:suprepo_e36aa236",
    "supplement:suprepo_f687a40a",
]


def _embedded_source(sql: str, tag: str) -> list[dict]:
    match = re.search(
        rf"\${tag}\$(.*?)\${tag}\$::jsonb",
        sql,
        flags=re.DOTALL,
    )
    if not match:
        raise AssertionError(f"Missing embedded {tag} source snapshot.")
    return list(json.loads(match.group(1)))


class ContentRepositoryControlledBackfillTests(unittest.TestCase):
    def test_revalidated_source_projection_matches_corrected_inventory(self) -> None:
        sql = MIGRATION.read_text(encoding="utf-8")
        exercises = _embedded_source(sql, "exercise_source")
        supplements = _embedded_source(sql, "supplement_source")

        items = [
            *_recipe_rows(),
            *_exercise_rows({"exercises": exercises}),
            *_supplement_rows({"supplement_repository": supplements}),
        ]
        plan = build_migration_plan(items)

        self.assertEqual(
            plan["counts"],
            {"recipe": 2, "exercise": 3, "supplement": 5},
        )
        self.assertEqual(plan["identities"], EXPECTED_IDENTITIES)
        self.assertEqual(plan["checksums"]["recipe"], EXPECTED_CHECKSUMS["recipe"])
        self.assertEqual(plan["checksums"]["exercise"], EXPECTED_CHECKSUMS["exercise"])
        self.assertEqual(
            plan["checksums"]["supplement"],
            EXPECTED_CHECKSUMS["supplement"],
        )
        self.assertEqual(repository_checksum(items), EXPECTED_CHECKSUMS["total"])

        inventory = INVENTORY.read_text(encoding="utf-8")
        for checksum in EXPECTED_CHECKSUMS.values():
            self.assertIn(checksum, inventory)

    def test_backfill_is_guarded_and_transaction_verifiable(self) -> None:
        sql = MIGRATION.read_text(encoding="utf-8").lower()

        self.assertIn("destination is not empty", sql)
        self.assertIn("exercise source changed after inventory", sql)
        self.assertIn("supplement source changed after inventory", sql)
        self.assertIn(
            "create temporary table hm_content_repository_backfill_expected",
            sql,
        )
        self.assertIn(
            "insert into public.hm_content_repository_items",
            sql,
        )
        self.assertIn("expected 10 items", sql)
        self.assertIn("expected 10 events", sql)
        self.assertIn("repository counts do not match 2/3/5", sql)
        self.assertIn("content_version <> 1", sql)
        self.assertIn("event_type <> 'created'", sql)
        self.assertIn("count(distinct repository_item_id)", sql)

    def test_backfill_preserves_legacy_sources_and_does_not_cut_over_pages(self) -> None:
        sql = MIGRATION.read_text(encoding="utf-8").lower()

        self.assertNotIn("update public.healthyme_app_state", sql)
        self.assertNotIn("delete from public.healthyme_app_state", sql)
        self.assertNotIn("truncate public.healthyme_app_state", sql)

        for relative_path in (
            "pages/15_Admin_Recipe_Manager.py",
            "pages/16_Admin_Exercise_Manager.py",
            "pages/39_Admin_Supplement_Manager.py",
        ):
            page = (ROOT / relative_path).read_text(encoding="utf-8")
            self.assertNotIn("content_repository_store", page)
            self.assertNotIn("content_repository_migration", page)


if __name__ == "__main__":
    unittest.main()
