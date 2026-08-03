from __future__ import annotations

import pathlib
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
DASHBOARD = ROOT / "pages" / "10_Admin_Dashboard.py"
BUILDER = ROOT / "components" / "profile_builder_modular.py"
CONTRACT = ROOT / "components" / "meal_profile_builder_phase_b.py"
ALLOCATION = ROOT / "components" / "profile_builder_allocation_workspace.py"


class Issue260ProfileBuilderUICleanupTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.dashboard_source = DASHBOARD.read_text(encoding="utf-8")
        cls.builder_source = BUILDER.read_text(encoding="utf-8")
        cls.contract_source = CONTRACT.read_text(encoding="utf-8")
        cls.allocation_source = ALLOCATION.read_text(encoding="utf-8")

    def test_dashboard_view_profiles_shortcut_is_removed(self) -> None:
        self.assertNotIn('nav_cell("View Profiles"', self.dashboard_source)
        self.assertIn("Recommendation Profile Builder", self.dashboard_source)
        self.assertIn(
            '"pages/38_Admin_Recommendation_Profile_Builder.py"',
            self.dashboard_source,
        )

    def test_dashboard_duplicate_allocation_shortcuts_are_removed(self) -> None:
        self.assertNotIn('"Exercise Member Allocation"', self.dashboard_source)
        self.assertNotIn('"Supplement Member Allocation"', self.dashboard_source)
        self.assertIn('"Exercises"', self.dashboard_source)
        self.assertIn('"Supplements"', self.dashboard_source)

    def test_builder_lifecycle_guide_is_not_rendered(self) -> None:
        self.assertNotIn("render_profile_lifecycle_guide", self.builder_source)
        self.assertNotIn("Recommendation Profile lifecycle", self.builder_source)

    def test_builder_status_copy_is_removed(self) -> None:
        self.assertNotIn("Profile Builder store is ready", self.builder_source)
        self.assertNotIn("Profile Builder store is not ready", self.builder_source)
        self.assertNotIn("st.caption(source_message)", self.builder_source)
        self.assertNotIn("check_profile_builder_store()", self.builder_source)

    def test_view_profiles_remains_inside_builder(self) -> None:
        self.assertIn('VIEW_PROFILES_SECTION = "View Profiles"', self.contract_source)
        self.assertIn("VIEW_PROFILES_SECTION", self.builder_source)
        self.assertIn("render_view_profiles()", self.builder_source)

    def test_profile_source_loading_and_compact_workflows_remain(self) -> None:
        self.assertIn("load_profile_builder_sources()", self.builder_source)
        self.assertIn("render_setup(options)", self.builder_source)
        self.assertIn('render_module("meal", options)', self.builder_source)
        self.assertIn("render_profile_publish_control()", self.builder_source)
        self.assertIn('"Preview Meal Plan"', self.builder_source)
        self.assertIn('"Publish Meal Plan"', self.builder_source)
        self.assertIn("render_profile_builder_allocation_workspace()", self.builder_source)
        self.assertNotIn("render_active_profile_preview_contract()", self.builder_source)

    def test_allocation_workspace_remains_compact(self) -> None:
        self.assertIn('"Allocate Exercise"', self.allocation_source)
        self.assertIn('"Allocate Supplement"', self.allocation_source)
        self.assertNotIn("save_exercise_member_allocation", self.allocation_source)
        self.assertNotIn("save_supplement_member_allocation", self.allocation_source)


if __name__ == "__main__":
    unittest.main()
