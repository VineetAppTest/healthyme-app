from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
VIEWER = ROOT / "components" / "recommendation_profile_viewer.py"
BUILDER = ROOT / "components" / "profile_builder_modular.py"
PAGE = ROOT / "pages" / "48_Admin_View_Profiles.py"
DASHBOARD = ROOT / "pages" / "10_Admin_Dashboard.py"


class ViewProfilesLifecycleContractTest(unittest.TestCase):
    def test_changed_python_files_compile(self):
        for path in (VIEWER, BUILDER, PAGE, DASHBOARD):
            compile(path.read_text(encoding="utf-8"), str(path), "exec")

    def test_view_profiles_is_read_only_and_covers_all_lifecycle_states(self):
        source = VIEWER.read_text(encoding="utf-8")
        for status in ("draft", "active", "replaced", "archived"):
            self.assertIn(f'"{status}"', source)
        self.assertIn("load_profile_inventory", source)
        self.assertIn("load_profile_detail", source)
        for forbidden in (
            ".insert(",
            ".update(",
            ".delete(",
            ".upsert(",
            "activate_profile(",
            "save_draft_profile(",
            "save_profile_module(",
        ):
            self.assertNotIn(forbidden, source)

    def test_lifecycle_guide_explains_preview_publish_active(self):
        source = VIEWER.read_text(encoding="utf-8")
        self.assertIn("Preview does not save or change profile status", source)
        self.assertIn("saved Draft", source)
        self.assertIn("previous Active profile becomes Replaced", source)
        self.assertIn("current live consumption contract", source)
        self.assertIn("update that live profile in place", source)
        self.assertIn("render_profile_lifecycle_guide()", BUILDER.read_text(encoding="utf-8"))

    def test_view_profiles_access_and_navigation_are_connected(self):
        page_source = PAGE.read_text(encoding="utf-8")
        dashboard_source = DASHBOARD.read_text(encoding="utf-8")
        self.assertIn("require_profile_builder_access()", page_source)
        self.assertIn("profile_builder_role_utility_bar()", page_source)
        self.assertIn('nav_cell("View Profiles", "pages/48_Admin_View_Profiles.py"', dashboard_source)
        self.assertIn('st.switch_page("pages/38_Admin_Recommendation_Profile_Builder.py")', VIEWER.read_text(encoding="utf-8"))

    def test_view_profiles_does_not_change_auth_or_profile_business_rules(self):
        source = VIEWER.read_text(encoding="utf-8")
        for forbidden in (
            "authorization_id",
            "require_admin",
            "require_member",
            "session_counted",
            "package_usage",
            "mark_member_message_read",
        ):
            self.assertNotIn(forbidden, source)


if __name__ == "__main__":
    unittest.main()
