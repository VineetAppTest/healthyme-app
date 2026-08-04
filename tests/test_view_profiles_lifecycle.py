from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
LEGACY_VIEWER = ROOT / "components" / "recommendation_profile_viewer.py"
BUILDER = ROOT / "components" / "profile_builder_modular.py"
CONTRACT = ROOT / "components" / "meal_profile_builder_phase_b.py"
VIEW = ROOT / "components" / "member_plan_builder_view_compact.py"
CURRENT_PLAN = ROOT / "components" / "current_member_plan.py"
LEGACY_PAGE = ROOT / "pages" / "48_Admin_View_Profiles.py"


class ViewMemberPlanExcelSSOTContractTest(unittest.TestCase):
    def test_changed_python_files_compile(self):
        for path in (LEGACY_VIEWER, BUILDER, CONTRACT, VIEW, CURRENT_PLAN, LEGACY_PAGE):
            compile(path.read_text(encoding="utf-8"), str(path), "exec")

    def test_view_member_plan_is_final_compact_builder_task(self):
        builder = BUILDER.read_text(encoding="utf-8")
        contract = CONTRACT.read_text(encoding="utf-8")
        self.assertIn('VIEW_PROFILES_SECTION = "View Member Plan"', contract)
        self.assertIn("MEAL_PROFILE_BUILDER_SECTIONS", builder)
        self.assertIn("VIEW_PROFILES_SECTION", builder)
        self.assertIn("render_view_member_plan_compact()", builder)
        self.assertNotIn('elif section == "Active Profile Preview":', builder)
        self.assertLess(
            contract.index('SUPPLEMENT_SECTION = "Supplement Allocation"'),
            contract.index('VIEW_PROFILES_SECTION = "View Member Plan"'),
        )

    def test_legacy_standalone_route_redirects_into_view_member_plan(self):
        source = LEGACY_PAGE.read_text(encoding="utf-8")
        self.assertIn(
            'st.session_state["pbm_section"] = "View Member Plan"',
            source,
        )
        self.assertIn(
            'st.switch_page("pages/38_Admin_Recommendation_Profile_Builder.py")',
            source,
        )
        self.assertNotIn("render_view_profiles()", source)

    def test_view_removes_profile_scope_and_defaults_by_member(self):
        source = VIEW.read_text(encoding="utf-8")
        self.assertNotIn("Profile Scope", source)
        self.assertIn('"Member"', source)
        self.assertIn('"View Existing Profile"', source)
        self.assertIn("active_profiles", source)
        self.assertIn("more than one active Meal Profile", source)

    def test_active_view_uses_consolidated_member_plan_and_checks_identity(self):
        source = VIEW.read_text(encoding="utf-8")
        self.assertIn("build_current_member_plan", source)
        self.assertIn("model_profile_id != selected_id", source)
        self.assertIn("Exercise Allocations", source)
        self.assertIn("Supplement Allocations", source)
        self.assertIn("ignored_profile_rows", source)
        current = CURRENT_PLAN.read_text(encoding="utf-8")
        self.assertIn("read_only", current)
        self.assertIn("member_exercise_allocations", current)
        self.assertIn("ignored_profile_rows", current)

    def test_existing_view_remains_read_only(self):
        source = VIEW.read_text(encoding="utf-8")
        for forbidden in (
            ".insert(",
            ".update(",
            ".delete(",
            ".upsert(",
            "activate_profile(",
            "save_profile_module(",
            "save_profile_shell(",
        ):
            self.assertNotIn(forbidden, source)

    def test_download_contains_full_plan_and_audit_history(self):
        source = VIEW.read_text(encoding="utf-8")
        self.assertIn('"Download Selected Member Plan"', source)
        self.assertIn('sheet_name="Plan Summary"', source)
        self.assertIn('sheet_name="Seven Day Meals"', source)
        self.assertIn('sheet_name="Exercise Allocations"', source)
        self.assertIn('sheet_name="Supplement Allocations"', source)
        self.assertIn('sheet_name="Change Log"', source)
        self.assertIn('sheet_name="Legacy Profile Rows"', source)

    def test_legacy_viewer_is_retained_read_only_for_compatibility(self):
        source = LEGACY_VIEWER.read_text(encoding="utf-8")
        for forbidden in (
            ".insert(",
            ".update(",
            ".delete(",
            ".upsert(",
            "activate_profile(",
            "save_profile_module(",
            "save_profile_shell(",
        ):
            self.assertNotIn(forbidden, source)


if __name__ == "__main__":
    unittest.main()
