from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
VIEWER = ROOT / "components" / "recommendation_profile_viewer.py"
BUILDER = ROOT / "components" / "profile_builder_modular.py"
LEGACY_PAGE = ROOT / "pages" / "48_Admin_View_Profiles.py"


class ViewProfilesExcelSSOTContractTest(unittest.TestCase):
    def test_changed_python_files_compile(self):
        for path in (VIEWER, BUILDER, LEGACY_PAGE):
            compile(path.read_text(encoding="utf-8"), str(path), "exec")

    def test_view_profiles_is_the_tab_after_active(self):
        source = BUILDER.read_text(encoding="utf-8")
        self.assertIn('VIEW_PROFILES_SECTION = "View Profiles"', source)
        self.assertIn("visible_sections.append(VIEW_PROFILES_SECTION)", source)
        self.assertIn('elif section == "Active Profile Preview":', source)
        self.assertIn("render_active_profile_preview_contract()", source)
        self.assertIn("render_view_profiles()", source)
        self.assertLess(
            source.index('elif section == "Active Profile Preview":'),
            source.index("render_view_profiles()"),
        )

    def test_legacy_standalone_route_redirects_into_builder_tab(self):
        source = LEGACY_PAGE.read_text(encoding="utf-8")
        self.assertIn('st.session_state["pbm_section"] = "View Profiles"', source)
        self.assertIn(
            'st.switch_page("pages/38_Admin_Recommendation_Profile_Builder.py")',
            source,
        )
        self.assertNotIn("render_view_profiles()", source)

    def test_profile_scope_values_match_excel_legend(self):
        source = VIEWER.read_text(encoding="utf-8")
        for value in (
            "All Profiles",
            "All Editable Profiles",
            "All Allocated Profiles",
            "Member Profiles",
        ):
            self.assertIn(f'"{value}"', source)

    def test_existing_profile_is_dependent_and_dates_are_optional(self):
        source = VIEWER.read_text(encoding="utf-8")
        self.assertIn("on_change=_clear_selected_profile", source)
        self.assertIn("eligible = _scope_profiles(profiles, scope)", source)
        self.assertIn(
            "eligible = _date_filtered_profiles(eligible, date_from, date_to)",
            source,
        )
        self.assertIn('"View Existing Profile"', source)
        self.assertIn('"Date - From"', source)
        self.assertIn('"Date - To"', source)
        self.assertGreaterEqual(source.count("value=None"), 2)

    def test_excel_section_structure_is_preserved(self):
        source = VIEWER.read_text(encoding="utf-8")
        self.assertIn('section_type="Meal"', source)
        self.assertIn('headers=("Timing", "Meal", "Liquid", "Remarks")', source)
        self.assertIn('section_type="Exercise"', source)
        self.assertIn(
            'headers=("Timing", "Activity", "Duration/Sets", "Remarks")',
            source,
        )
        self.assertIn('section_type="Supplement"', source)
        self.assertIn(
            'headers=("Timing", "Supplement", "Dosage", "Remarks")',
            source,
        )
        self.assertIn('table_headers = ("Start Date", "Type", "Day") + headers', source)
        self.assertIn("for day in range(1, 8):", source)
        self.assertIn("rowspan='7'", source)

    def test_all_profile_stages_and_partial_profiles_remain_reviewable(self):
        source = VIEWER.read_text(encoding="utf-8")
        for status in ("draft", "active", "replaced", "archived"):
            self.assertIn(f'"{status}"', source)
        self.assertIn('.select("*")', source)
        self.assertIn("No created profiles match", source)

    def test_view_profiles_remains_read_only(self):
        source = VIEWER.read_text(encoding="utf-8")
        for forbidden in (
            ".insert(",
            ".update(",
            ".delete(",
            ".upsert(",
            "activate_profile(",
            "save_draft_profile(",
            "save_profile_module(",
            "save_profile_shell(",
        ):
            self.assertNotIn(forbidden, source)

    def test_lifecycle_guide_retains_preview_publish_active_clarity(self):
        source = VIEWER.read_text(encoding="utf-8")
        self.assertIn("Preview does not save or change profile status", source)
        self.assertIn("saved Draft", source)
        self.assertIn("previous Active profile becomes Replaced", source)
        self.assertIn("current live consumption contract", source)


if __name__ == "__main__":
    unittest.main()
