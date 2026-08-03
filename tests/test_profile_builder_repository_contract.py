from __future__ import annotations

import unittest
from pathlib import Path
from unittest.mock import patch

from components import profile_builder_repository_contract as contract


ROOT = Path(__file__).resolve().parents[1]
CONTRACT_FILE = ROOT / "components" / "profile_builder_repository_contract.py"


class ProfileBuilderRepositoryContractTests(unittest.TestCase):
    def test_recipe_uses_compatibility_repository_and_preserves_numeric_id(self):
        rows = [
            {
                "id": "12",
                "source_id": "12",
                "title": "Balanced Bowl",
                "status": "active",
                "portion_size": "1 bowl",
            }
        ]
        with (
            patch.object(contract, "list_repository_items", return_value=rows) as recipe,
            patch.object(contract, "list_exercise_repository") as exercise,
            patch.object(contract, "list_supplement_repository") as supplement,
        ):
            sources = contract.list_profile_builder_repository_sources("recipe")

        recipe.assert_called_once_with("recipes", active_only=True)
        exercise.assert_not_called()
        supplement.assert_not_called()
        self.assertEqual(sources[0]["source_id"], "12")
        self.assertEqual(sources[0]["identity_key"], "recipe_repository:12")
        self.assertEqual(sources[0]["snapshot"]["portion_size"], "1 bowl")

    def test_exercise_uses_persistent_repository_directly(self):
        rows = [
            {
                "id": "7",
                "title": "Mobility Flow",
                "status": "active",
                "duration_or_reps": "12 minutes",
            }
        ]
        with (
            patch.object(contract, "list_repository_items") as recipe,
            patch.object(
                contract, "list_exercise_repository", return_value=rows
            ) as exercise,
            patch.object(contract, "list_supplement_repository") as supplement,
        ):
            sources = contract.list_profile_builder_repository_sources("exercise")

        exercise.assert_called_once_with(active_only=True)
        recipe.assert_not_called()
        supplement.assert_not_called()
        self.assertEqual(sources[0]["source_id"], "7")
        self.assertEqual(sources[0]["source_type"], "exercise_repository")
        self.assertEqual(
            sources[0]["snapshot"]["duration_or_reps"], "12 minutes"
        )

    def test_supplement_uses_master_repository_and_excludes_member_fields(self):
        rows = [
            {
                "id": "suprepo_ab12cd34",
                "supplement_name": "Vitamin D",
                "dosage": "1 tablet",
                "frequency": "Daily",
                "timing": "After breakfast",
                "instructions": "With water",
                "admin_notes": "historical note",
                "start_date": "2026-08-01",
                "end_date": "2026-08-31",
                "member_id": "member-1",
                "status": "Active",
            }
        ]
        with patch.object(
            contract, "list_supplement_repository", return_value=rows
        ) as supplement:
            source = contract.list_profile_builder_repository_sources("supplement")[0]

        supplement.assert_called_once_with(active_only=True)
        self.assertEqual(source["source_id"], "suprepo_ab12cd34")
        self.assertEqual(source["source_type"], "supplement_repository")
        self.assertEqual(source["display_label"], "Vitamin D")
        for excluded in (
            "admin_notes",
            "start_date",
            "end_date",
            "member_id",
        ):
            self.assertNotIn(excluded, source["snapshot"])

    def test_source_id_not_display_label_is_the_identity(self):
        rows = [
            {"id": "2", "title": "Shared Name", "status": "active"},
            {"id": "9", "title": "Shared Name", "status": "active"},
        ]
        with patch.object(contract, "list_exercise_repository", return_value=rows):
            sources = contract.list_profile_builder_repository_sources("exercise")

        self.assertEqual(len(sources), 2)
        self.assertEqual(
            {source["identity_key"] for source in sources},
            {"exercise_repository:2", "exercise_repository:9"},
        )
        self.assertEqual(
            {source["display_label"] for source in sources}, {"Shared Name"}
        )

    def test_active_only_is_enforced_defensively(self):
        rows = [
            {"id": "1", "title": "Active", "status": "active"},
            {"id": "2", "title": "Inactive", "status": "inactive"},
        ]
        with patch.object(contract, "list_exercise_repository", return_value=rows):
            active = contract.list_profile_builder_repository_sources(
                "exercise", active_only=True
            )
            all_items = contract.list_profile_builder_repository_sources(
                "exercise", active_only=False
            )

        self.assertEqual([item["source_id"] for item in active], ["1"])
        self.assertEqual(
            {item["source_id"] for item in all_items}, {"1", "2"}
        )
        inactive = next(item for item in all_items if item["source_id"] == "2")
        self.assertFalse(inactive["selectable"])

    def test_returned_snapshots_are_defensive_copies(self):
        rows = [
            {
                "id": "4",
                "title": "Strength Basics",
                "status": "active",
                "benefits": "Baseline benefit",
            }
        ]
        with patch.object(contract, "list_exercise_repository", return_value=rows):
            first = contract.list_profile_builder_repository_sources("exercise")
            first[0]["snapshot"]["benefits"] = "mutated"
            second = contract.list_profile_builder_repository_sources("exercise")

        self.assertEqual(second[0]["snapshot"]["benefits"], "Baseline benefit")

    def test_resolve_by_id_ignores_duplicate_labels(self):
        rows = [
            {"id": "3", "title": "Repeated", "status": "active"},
            {"id": "8", "title": "Repeated", "status": "inactive"},
        ]
        with patch.object(contract, "list_exercise_repository", return_value=rows):
            source = contract.profile_builder_repository_source_by_id(
                "exercise", "8", active_only=False
            )

        self.assertIsNotNone(source)
        self.assertEqual(source["source_id"], "8")
        self.assertFalse(source["selectable"])

    def test_manifest_freezes_repository_id_and_history_rules(self):
        manifest = contract.canonical_repository_contract_manifest()
        self.assertEqual(manifest["contract_version"], contract.CONTRACT_VERSION)
        self.assertIn("source_id is authoritative", manifest["identity_rule"])
        self.assertIn("immutable", manifest["history_rule"])
        self.assertIn(
            "physical deletion and reindexing are prohibited",
            manifest["repositories"]["recipe"]["id_strategy"],
        )
        self.assertIn(
            "persistent numeric",
            manifest["repositories"]["exercise"]["id_strategy"],
        )
        self.assertIn(
            "suprepo_*",
            manifest["repositories"]["supplement"]["id_strategy"],
        )
        self.assertIn(
            "admin_notes",
            manifest["repositories"]["supplement"][
                "excluded_from_new_snapshot"
            ],
        )

    def test_missing_identity_or_title_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "missing source_id"):
            contract.normalise_profile_builder_repository_source(
                "recipe", {"title": "No ID"}
            )
        with self.assertRaisesRegex(ValueError, "missing its display title"):
            contract.normalise_profile_builder_repository_source(
                "exercise", {"id": "1"}
            )

    def test_contract_has_no_member_regimen_or_runtime_patch_dependency(self):
        source = CONTRACT_FILE.read_text(encoding="utf-8")
        self.assertNotIn("list_member_supplements", source)
        self.assertNotIn("install_exercise_repository_runtime", source)
        self.assertNotIn("install_profile_builder_supplement_repository_source", source)
        self.assertNotIn("start_date\"", source)
        self.assertNotIn("end_date\"", source)


if __name__ == "__main__":
    unittest.main()
