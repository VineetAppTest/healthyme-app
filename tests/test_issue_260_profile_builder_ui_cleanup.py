from __future__ import annotations

import pathlib
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
DASHBOARD = ROOT / "pages" / "10_Admin_Dashboard.py"
BUILDER = ROOT / "components" / "profile_builder_modular.py"
CONTRACT = ROOT / "components" / "meal_profile_builder_phase_b.py"
SETUP = ROOT / "components" / "member_plan_builder_setup.py"
MEALS = ROOT / "components" / "member_plan_builder_meals.py"
ALLOCATION = ROOT / "components" / "member_plan_builder_allocations.py"
EXPORT = ROOT / "components" / "member_plan_builder_export.py"


class Issue260ProfileBuilderUICleanupTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.dashboard_source = DASHBOARD.read_text(encoding="utf-8")
        cls.builder_source = BUILDER.read_text(encoding="utf-8")
        cls.contract_source = CONTRACT.read_text(encoding="utf-8")
        cls.setup_source = SETUP.read_text(encoding="utf-8")
        cls.meals_source = MEALS.read_text(encoding="utf-8")
        cls.allocation_source = ALLOCATION.read_text(encoding="utf-8")
        cls.export_source = EXPORT.read_text(encoding="utf-8")

    def test_dashboard_keeps_one_builder_entry(self) -> None:
        self.assertNotIn('nav_cell("View Profiles"', self.dashboard_source)
        self.assertIn("Recommendation Profile Builder", self.dashboard_source)
        self.assertNotIn('"Exercise Member Allocation"', self.dashboard_source)
        self.assertNotIn('"Supplement Member Allocation"', self.dashboard_source)

    def test_builder_navigation_is_task_based_and_compact(self) -> None:
        self.assertIn('"Profile Setup": "Setup"', self.builder_source)
        self.assertIn('"Meal Structure": "Meals"', self.builder_source)
        self.assertIn('"Exercise & Supplement"', self.builder_source)
        self.assertIn('"View Member Plan"', self.builder_source)
        self.assertNotIn("Recommendation Profile lifecycle", self.builder_source)
        self.assertNotIn("Preview Meal Plan", self.builder_source)

    def test_setup_removes_manual_load_and_keeps_complete_clone(self) -> None:
        self.assertNotIn('"Load Profile"', self.setup_source)
        self.assertIn("load_selected(selected_id, shell_only=False)", self.setup_source)
        self.assertIn('"Clone Complete Plan"', self.setup_source)
        self.assertIn("save_profile_module", self.setup_source)

    def test_meal_workflow_is_fixed_and_review_driven(self) -> None:
        self.assertIn("MEAL_SLOTS", self.meals_source)
        self.assertIn('"Portion Guidance"', self.meals_source)
        self.assertIn('"More details', self.meals_source)
        self.assertIn('"Save Meal Plan"', self.meals_source)
        self.assertIn("st.dataframe", self.meals_source)
        self.assertIn('"Publish & Allocate to Member"', self.meals_source)

    def test_allocation_workflows_are_embedded_not_redirected(self) -> None:
        self.assertIn('st.tabs(["Exercise", "Supplement"])', self.allocation_source)
        self.assertIn("save_exercise_member_allocation", self.allocation_source)
        self.assertIn("save_supplement_member_allocation", self.allocation_source)
        self.assertNotIn("st.switch_page", self.allocation_source)

    def test_view_member_plan_keeps_existing_view_and_adds_download(self) -> None:
        self.assertIn('VIEW_PROFILES_SECTION = "View Member Plan"', self.contract_source)
        self.assertIn("render_view_member_plan()", self.builder_source)
        self.assertIn("render_view_profiles()", self.export_source)
        self.assertIn('"Download Selected Member Plan"', self.export_source)


if __name__ == "__main__":
    unittest.main()
