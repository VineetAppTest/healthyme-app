from __future__ import annotations

import pathlib
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
DASHBOARD = ROOT / "pages" / "10_Admin_Dashboard.py"
BUILDER = ROOT / "components" / "profile_builder_modular.py"
CONTRACT = ROOT / "components" / "meal_profile_builder_phase_b.py"
SETUP = ROOT / "components" / "member_plan_builder_setup.py"
MEALS = ROOT / "components" / "member_plan_builder_meals_compact.py"
EXERCISE = ROOT / "components" / "member_plan_builder_exercise.py"
SUPPLEMENT = ROOT / "components" / "member_plan_builder_supplement.py"
VIEW = ROOT / "components" / "member_plan_builder_view_compact.py"


class Issue260ProfileBuilderUICleanupTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.dashboard_source = DASHBOARD.read_text(encoding="utf-8")
        cls.builder_source = BUILDER.read_text(encoding="utf-8")
        cls.contract_source = CONTRACT.read_text(encoding="utf-8")
        cls.setup_source = SETUP.read_text(encoding="utf-8")
        cls.meals_source = MEALS.read_text(encoding="utf-8")
        cls.exercise_source = EXERCISE.read_text(encoding="utf-8")
        cls.supplement_source = SUPPLEMENT.read_text(encoding="utf-8")
        cls.view_source = VIEW.read_text(encoding="utf-8")

    def test_dashboard_keeps_one_builder_entry(self) -> None:
        self.assertNotIn('nav_cell("View Profiles"', self.dashboard_source)
        self.assertIn("Recommendation Profile Builder", self.dashboard_source)
        self.assertNotIn('"Exercise Member Allocation"', self.dashboard_source)
        self.assertNotIn('"Supplement Member Allocation"', self.dashboard_source)

    def test_builder_navigation_is_task_based_and_compact(self) -> None:
        self.assertIn('"Profile Setup": "Setup"', self.builder_source)
        self.assertIn('"Meal Structure": "Meals"', self.builder_source)
        self.assertIn('EXERCISE_SECTION: "Exercise"', self.builder_source)
        self.assertIn('SUPPLEMENT_SECTION: "Supplement"', self.builder_source)
        self.assertIn('VIEW_PROFILES_SECTION: "View Member Plan"', self.builder_source)
        self.assertNotIn("Recommendation Profile lifecycle", self.builder_source)
        self.assertNotIn("Preview Meal Plan", self.builder_source)

    def test_setup_removes_manual_load_and_keeps_meal_only_clone(self) -> None:
        self.assertNotIn('"Load Profile"', self.setup_source)
        self.assertIn("load_selected(selected_id, shell_only=False)", self.setup_source)
        self.assertIn('"Clone Meal Profile"', self.setup_source)
        self.assertIn("save_profile_module", self.setup_source)
        self.assertNotIn('selectbox(\n        "Member"', self.setup_source)

    def test_meal_workflow_is_fixed_and_review_driven(self) -> None:
        self.assertIn("MEAL_SLOTS", self.meals_source)
        self.assertIn('"Portion Guidance"', self.meals_source)
        self.assertIn('with st.expander("More details"', self.meals_source)
        self.assertIn('"Save Meal Plan"', self.meals_source)
        self.assertIn("st.dataframe", self.meals_source)
        self.assertIn('"Meal Profile"', self.meals_source)
        self.assertIn('"Publish"', self.meals_source)

    def test_allocation_workflows_are_separate_and_embedded(self) -> None:
        self.assertIn("save_exercise_member_allocation", self.exercise_source)
        self.assertIn("stop_exercise_member_allocation", self.exercise_source)
        self.assertIn("save_supplement_member_allocation", self.supplement_source)
        self.assertIn("stop_supplement_member_allocation", self.supplement_source)
        self.assertNotIn("st.switch_page", self.exercise_source)
        self.assertNotIn("st.switch_page", self.supplement_source)
        self.assertNotIn('"Allocation ID"', self.exercise_source)
        self.assertNotIn('"Allocation ID"', self.supplement_source)

    def test_view_member_plan_removes_scope_uses_ssot_and_adds_download(self) -> None:
        self.assertIn('VIEW_PROFILES_SECTION = "View Member Plan"', self.contract_source)
        self.assertIn("render_view_member_plan_compact()", self.builder_source)
        self.assertNotIn("Profile Scope", self.view_source)
        self.assertIn("build_current_member_plan", self.view_source)
        self.assertIn("def _render_member_summary", self.view_source)
        self.assertIn("mpb-member-summary-table-v1", self.view_source)
        self.assertIn("def _render_meal_week_grid", self.view_source)
        self.assertIn("def _render_flat_plan_table", self.view_source)
        self.assertIn('("Exercise", "Reps/Duration", "Timing", "Dates", "Status", "Remarks")', self.view_source)
        self.assertIn('"Download Excel"', self.view_source)
        self.assertIn('"Download PDF"', self.view_source)


if __name__ == "__main__":
    unittest.main()
