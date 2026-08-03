from __future__ import annotations

import pathlib
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "components" / "recommendation_contract.py"
RECIPES_CSV = ROOT / "data" / "recipes.csv"
EXERCISES_CSV = ROOT / "data" / "exercises.csv"


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
            "def save_unified_recommendation_share(",
        ):
            self.assertIn(required, source)

    def test_obsolete_sync_and_mirror_contracts_are_removed(self) -> None:
        source = CONTRACT.read_text(encoding="utf-8")
        for forbidden in (
            "def list_repository_items(",
            "def sync_all_repositories_to_state(",
            "sync_all_repositories_to_state()",
            '"repo_key":',
            "repository mirror is empty",
        ):
            self.assertNotIn(forbidden, source)
        self.assertIn("recipe_repo = list_recipe_repository(active_only=False)", source)
        self.assertIn("exercise_repo = list_exercise_repository(active_only=False)", source)

    def test_rollback_evidence_files_are_not_deleted(self) -> None:
        for path in (RECIPES_CSV, EXERCISES_CSV):
            self.assertTrue(path.exists())
            self.assertGreater(path.stat().st_size, 0)


if __name__ == "__main__":
    unittest.main()
