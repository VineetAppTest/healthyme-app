from __future__ import annotations

import pathlib
import unittest

from components.content_repository_migration import _recipe_rows, repository_checksum


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

RAW_SOURCE_HASHES = {
    "exercise": "fdd4b6945284c46dadcf60b4000a02f2e75daf31efd10b55358cfa4813fa65e0",
    "supplement": "dd25cd82f88ad07afdea2e91cfc80f9ccaca60598566fcc34d9697036408790c",
}


class ContentRepositoryControlledBackfillTests(unittest.TestCase):
    def test_recipe_source_still_matches_frozen_checksum(self) -> None:
        self.assertEqual(
            repository_checksum(_recipe_rows()),
            EXPECTED_CHECKSUMS["recipe"],
        )

    def test_corrected_inventory_and_live_hash_guards_are_recorded(self) -> None:
        sql = MIGRATION.read_text(encoding="utf-8")
        inventory = INVENTORY.read_text(encoding="utf-8")

        for checksum in EXPECTED_CHECKSUMS.values():
            self.assertIn(checksum, sql)
            self.assertIn(checksum, inventory)

        for raw_hash in RAW_SOURCE_HASHES.values():
            self.assertIn(raw_hash, sql)

        self.assertIn("Checksum correction before backfill", inventory)
        self.assertIn("legacy_reference", inventory)

    def test_backfill_is_guarded_and_transaction_verifiable(self) -> None:
        sql = MIGRATION.read_text(encoding="utf-8").lower()

        self.assertIn("destination is not empty", sql)
        self.assertIn("for share", sql)
        self.assertIn("source counts changed after inventory", sql)
        self.assertIn("exercise source changed after inventory", sql)
        self.assertIn("supplement source changed after inventory", sql)
        self.assertIn("jsonb_array_elements", sql)
        self.assertIn(
            "create temporary table hm_content_repository_backfill_expected",
            sql,
        )
        self.assertIn("insert into public.hm_content_repository_items", sql)
        self.assertIn("expected 10 items", sql)
        self.assertIn("expected 10 events", sql)
        self.assertIn("repository counts do not match 2/3/5", sql)
        self.assertIn("content_version <> 1", sql)
        self.assertIn("event_type <> 'created'", sql)
        self.assertIn("count(distinct repository_item_id)", sql)
        self.assertIn("audit identity mismatch", sql)

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
