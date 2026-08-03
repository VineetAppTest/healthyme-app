from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
VIEWER = ROOT / "components" / "recommendation_profile_viewer.py"
BUILDER = ROOT / "components" / "profile_builder_modular.py"
CONTRACT = ROOT / "components" / "meal_profile_builder_phase_b.py"
EXPORT = ROOT / "components" / "member_plan_builder_export.py"
LEGACY_PAGE = ROOT / "pages" / "48_Admin_View_Profiles.py"


class ViewMemberPlanExcelSSOTContractTest(unittest.TestCase):
    def test_changed_python_files_compile(self):
        for path in (VIEWER, BUILDER, CONTRACT, EXPORT, LEGACY_PAGE):
            compile(path.read_text(encoding="utf-8"), str(path), "exec")

    def test_view_member_plan_is_final_compact_builder_tab(self):
        builder = BUILDER.read_text(encoding="utf-8")
        contract = CONTRACT.read_text(encoding="utf-8")
        self.assertIn('VIEW_PROFILES_SECTION = "View Member Plan"', contract)
        self.assertIn("MEAL_PROFILE_BUILDER_SECTIONS", builder)
        self.assertIn("VIEW_PROFILES_SECTION", builder)
        self.assertIn("render_view_member_plan()", builder)
        self.assertNotIn('elif section == "Active Profile Preview":', builder)
        self.assertLess(
            contract.index(
                'ALLOCATION_WORKSPACE_SECTION = "Allocate Exercise & Supplement"'
            ),
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

    def test_existing_profile_filters_and_excel_structure_are_preserved(self):
        source = VIEWER.read_text(encoding="utf-8")
        for value in (
            "All Profiles",
            "All Editable Profiles",
            "All Allocated Profiles",
            "Member Profiles",
        ):
            self.assertIn(f'"{value}"', source)
        self.assertIn("on_change=_clear_selected_profile", source)
        self.assertIn('section_type="Meal"', source)
        self.assertIn('section_type="Exercise"', source)
        self.assertIn('section_type="Supplement"', source)
        self.assertIn("for day in range(1, 8):", source)
        self.assertIn("rowspan='7'", source)

    def test_existing_view_remains_read_only(self):
        source = VIEWER.read_text(encoding="utf-8")
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

    def test_download_wraps_existing_view_without_adding_writes(self):
        source = EXPORT.read_text(encoding="utf-8")
        self.assertIn("render_view_profiles()", source)
        self.assertIn("load_profile_detail_readonly", source)
        self.assertIn('"Download Selected Member Plan"', source)
        self.assertIn('"Seven Day Meals"', source)
        self.assertIn('"Change Log"', source)
        for forbidden in (
            ".insert(",
            ".update(",
            ".delete(",
            ".upsert(",
            "activate_profile(",
        ):
            self.assertNotIn(forbidden, source)


if __name__ == "__main__":
    unittest.main()
