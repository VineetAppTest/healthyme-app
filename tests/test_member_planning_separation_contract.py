from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTRACT_FILE = ROOT / "components" / "member_planning_separation_contract.py"
DOC = ROOT / "docs" / "member_planning_separation_contract_2026-08-03.md"

_SPEC = importlib.util.spec_from_file_location(
    "member_planning_separation_contract", CONTRACT_FILE
)
if _SPEC is None or _SPEC.loader is None:
    raise RuntimeError("Unable to load Member Planning separation contract.")
contract = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(contract)


class MemberPlanningSeparationContractTests(unittest.TestCase):
    def test_manifest_freezes_independent_workflow_ownership(self) -> None:
        manifest = contract.member_planning_separation_manifest()
        workflows = manifest["target_workflows"]

        self.assertEqual(
            workflows["meal_profile_builder"]["allowed_domains"], ["meal"]
        )
        self.assertEqual(
            workflows["meal_profile_builder"]["excluded_domains"],
            ["exercise", "supplement"],
        )
        self.assertEqual(
            workflows["exercise_member_allocation"]["allowed_domains"],
            ["exercise"],
        )
        self.assertEqual(
            workflows["supplement_member_allocation"]["allowed_domains"],
            ["supplement"],
        )
        self.assertFalse(workflows["current_member_plan"]["write_authority"])

    def test_current_inventory_uses_confirmed_store_keys(self) -> None:
        inventory = contract.member_planning_separation_manifest()[
            "current_inventory"
        ]
        self.assertEqual(
            inventory["meal_structure"]["store_key"], "meal_type_repository"
        )
        self.assertEqual(
            inventory["meal_allocations"]["store_key"],
            "member_recipe_allocations",
        )
        self.assertEqual(
            inventory["exercise_allocations"]["store_key"],
            "member_exercise_allocations",
        )
        self.assertEqual(
            inventory["supplement_allocations"]["store_key"],
            "member_supplements",
        )
        self.assertEqual(
            inventory["published_member_plan"]["store_key"],
            "recommendation_shares",
        )

    def test_domain_routing_is_explicit(self) -> None:
        self.assertEqual(contract.workflow_for_domain("recipe"), "meal_profile_builder")
        self.assertEqual(
            contract.workflow_for_domain("exercise"),
            "exercise_member_allocation",
        )
        self.assertEqual(
            contract.workflow_for_domain("supplement"),
            "supplement_member_allocation",
        )
        self.assertEqual(
            contract.allocation_store_for_domain("meal"),
            "member_recipe_allocations",
        )
        self.assertEqual(
            contract.allocation_store_for_domain("exercise"),
            "member_exercise_allocations",
        )
        self.assertEqual(
            contract.allocation_store_for_domain("supplement"),
            "member_supplements",
        )

    def test_meal_profile_builder_rejects_other_domains(self) -> None:
        self.assertEqual(
            contract.validate_meal_profile_builder_domains(["meal", "recipe"]),
            ("meal", "meal"),
        )
        with self.assertRaisesRegex(ValueError, "meal concerns only"):
            contract.validate_meal_profile_builder_domains(
                ["meal", "exercise", "supplement"]
            )

    def test_canonical_source_reference_uses_source_identity(self) -> None:
        reference = contract.validate_canonical_source_reference(
            "exercise", "exercise_repository", "12"
        )
        self.assertEqual(reference["identity_key"], "exercise_repository:12")

        supplement = contract.validate_canonical_source_reference(
            "supplement", "supplement_repository", "suprepo_ab12"
        )
        self.assertEqual(
            supplement["identity_key"], "supplement_repository:suprepo_ab12"
        )

        with self.assertRaisesRegex(ValueError, "must reference recipe_repository"):
            contract.validate_canonical_source_reference(
                "meal", "exercise_repository", "1"
            )
        with self.assertRaisesRegex(ValueError, "source_id is required"):
            contract.validate_canonical_source_reference(
                "supplement", "supplement_repository", ""
            )

    def test_supplement_legacy_mapping_gap_is_explicit(self) -> None:
        supplement = contract.member_planning_separation_manifest()[
            "current_inventory"
        ]["supplement_allocations"]
        self.assertIsNone(supplement["source_id_field"])
        self.assertIn("compatibility mapping", supplement["migration_gap"])
        self.assertIn(
            "without replacing existing allocation IDs", supplement["migration_gap"]
        )

    def test_current_member_plan_is_read_only(self) -> None:
        self.assertTrue(contract.current_member_plan_is_read_only())
        manifest = contract.member_planning_separation_manifest()
        self.assertIn(
            "never another persistence authority",
            manifest["target_workflows"]["current_member_plan"]["rule"],
        )

    def test_manifest_is_a_defensive_copy(self) -> None:
        first = contract.member_planning_separation_manifest()
        first["target_workflows"]["meal_profile_builder"]["allowed_domains"].append(
            "exercise"
        )
        second = contract.member_planning_separation_manifest()
        self.assertEqual(
            second["target_workflows"]["meal_profile_builder"]["allowed_domains"],
            ["meal"],
        )

    def test_phase_a_has_no_runtime_or_storage_dependency(self) -> None:
        source = CONTRACT_FILE.read_text(encoding="utf-8")
        for forbidden in (
            "load_state",
            "save_state",
            "supabase",
            "streamlit",
            "list_recipe_repository",
            "list_exercise_repository",
            "list_supplement_repository",
        ):
            self.assertNotIn(forbidden, source)

    def test_documented_safety_boundary_is_present(self) -> None:
        source = DOC.read_text(encoding="utf-8")
        for required in (
            "must never become another persistence authority",
            "do not expose a dedicated canonical Supplement repository `source_id` field consistently",
            "does not:\n\n- modify live pages",
            "Existing active and historical member plans remain untouched",
        ):
            self.assertIn(required, source)


if __name__ == "__main__":
    unittest.main()
