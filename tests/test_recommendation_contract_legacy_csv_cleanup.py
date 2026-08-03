from __future__ import annotations

import hashlib
import pathlib
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "components" / "recommendation_contract.py"
ACTIVE_RECIPES_CSV = ROOT / "data" / "recipes.csv"
ACTIVE_EXERCISES_CSV = ROOT / "data" / "exercises.csv"
ARCHIVE_ROOT = ROOT / "docs" / "archive" / "content_repository_legacy"
ARCHIVED_RECIPES_CSV = ARCHIVE_ROOT / "recipes.csv"
ARCHIVED_EXERCISES_CSV = ARCHIVE_ROOT / "exercises.csv"
ARCHIVE_README = ARCHIVE_ROOT / "README.md"
OBSERVATION = ROOT / "docs" / "content_repository_final_observation_2026-08-03.md"


class RecommendationContractLegacyCsvCleanupTests(unittest.TestCase):
    def test_dead_csv_reader_helpers_are_removed(self) -> None:
        source = CONTRACT.read_text(encoding="utf-8")

        for forbidden in (
            "import pathlib",
            "BASE_DIR =",
            "RECIPES_PATH =",
            "EXERCISES_PATH =",
            "RECIPE_COLUMNS =",
            "EXERCISE_COLUMNS =",
            "def _repo_path(",
            "def _expected_columns(",
            "def _read_repository_df(",
            "pd.read_csv(",
            "resolve from CSV",
        ):
            self.assertNotIn(forbidden, source)

    def test_canonical_read_and_allocation_contract_remain(self) -> None:
        source = CONTRACT.read_text(encoding="utf-8")

        for required in (
            "import pandas as pd",
            "pd.isna(value)",
            "list_recipe_repository(active_only=active_only)",
            "list_exercise_repository(active_only=active_only)",
            "def list_repository_items(",
            "def save_member_resource_allocations(",
            "def enrich_recommendation_share_payload(",
            "def save_unified_recommendation_share(",
            "def recommendation_contract_diagnostics(",
        ):
            self.assertIn(required, source)

    def test_obsolete_sync_and_mirror_contracts_are_removed(self) -> None:
        source = CONTRACT.read_text(encoding="utf-8")
        for forbidden in (
            "def sync_repository_to_state(",
            "def sync_all_repositories_to_state(",
            "sync_all_repositories_to_state()",
            '"repo_key":',
            'db.get("recipes", [])',
            'db.get("exercises", [])',
            "repository mirror is empty",
        ):
            self.assertNotIn(forbidden, source)
        self.assertIn("recipe_repo = list_recipe_repository(active_only=False)", source)
        self.assertIn("exercise_repo = list_exercise_repository(active_only=False)", source)
        self.assertIn("canonical Recipe repository is empty", source)
        self.assertIn("canonical Exercise repository is empty", source)

    def test_active_csv_authorities_are_retired_to_checksum_archive(self) -> None:
        self.assertFalse(ACTIVE_RECIPES_CSV.exists())
        self.assertFalse(ACTIVE_EXERCISES_CSV.exists())

        expected_hashes = {
            ARCHIVED_RECIPES_CSV: "9abe0d2023182bfe857381fa81b93263d047cdd706b5042acfcb6f35b83ecc29",
            ARCHIVED_EXERCISES_CSV: "54290d4a89084a280d1b885db486134f6589901405d6b12c55726881543e86df",
        }
        for path, expected_hash in expected_hashes.items():
            self.assertTrue(path.exists())
            content = path.read_bytes()
            self.assertGreater(len(content), 0)
            self.assertEqual(hashlib.sha256(content).hexdigest(), expected_hash)

        self.assertTrue(ARCHIVE_README.exists())
        self.assertTrue(OBSERVATION.exists())

    def test_final_observation_preserves_production_data_boundary(self) -> None:
        source = OBSERVATION.read_text(encoding="utf-8")
        for required in (
            "No production app-state data is deleted",
            "member allocations",
            "recommendation shares",
            "historical source snapshots",
            "separate explicitly approved data migration",
        ):
            self.assertIn(required, source)


if __name__ == "__main__":
    unittest.main()
