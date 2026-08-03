from __future__ import annotations

import pathlib
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
INVENTORY = ROOT / "docs" / "healthyme_data_architecture_inventory_phase1_2026-08-03.md"


class DataArchitectureInventoryPhase1Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.source = INVENTORY.read_text(encoding="utf-8")

    def test_inventory_is_read_only_and_scoped_to_issue_346(self) -> None:
        self.assertIn("Issue: #346", self.source)
        self.assertIn("This is a read-only architecture inventory", self.source)
        self.assertIn("No production schema, application runtime, app-state data", self.source)

    def test_dedicated_and_shared_authorities_are_inventoryed(self) -> None:
        for required in (
            "hm_users",
            "hm_workflow",
            "hm_streamlit_auth_sessions",
            "hm_content_repository_items",
            "hm_recommendation_profiles",
            "hm_member_package_subscriptions",
            "hm_member_exercise_logs",
            "healthyme_app_state_v1",
            "flutter_laf_draft:982a04f9",
            "member_recipe_allocations",
            "member_exercise_allocations",
            "recommendation_shares",
            "daily_food_journals",
            "schedules",
            "messages",
            "notifications",
        ):
            self.assertIn(required, self.source)

    def test_verified_dual_structure_counts_are_frozen(self) -> None:
        for required in (
            "| Users | 15 | 15 | 15 | 0 | 0 |",
            "| Workflow | 15 | 15 | 15 | 0 | 0 |",
            "| Package catalogue | 3 | 3 | 3 | 0 | 0 |",
            "| Member package subscriptions | 3 | 3 | 3 | 0 | 0 |",
        ):
            self.assertIn(required, self.source)

    def test_cross_cutting_contract_is_explicit(self) -> None:
        for required in (
            "One live write authority per business purpose",
            "Stable IDs that never depend on display names or array positions",
            "Lower-snake-case persisted statuses",
            "Fresh read verification after administrative writes",
            "No silent production fallback to another write authority",
            "Immutable source snapshots",
            "Streamlit remains the behavioural source of truth",
        ):
            self.assertIn(required, self.source)

    def test_migration_order_starts_with_package_trace_not_cutover(self) -> None:
        self.assertIn("Batch 1 — Package catalogue and member subscriptions", self.source)
        self.assertIn("reader/writer trace and authority-freeze document", self.source)
        self.assertIn("It must not cut over writes until all live paths are accounted for", self.source)


if __name__ == "__main__":
    unittest.main()
