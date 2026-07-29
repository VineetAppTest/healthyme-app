from __future__ import annotations

import pathlib
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]


class PerformanceMeasurementOnlyTests(unittest.TestCase):
    def test_measurements_are_session_local_and_bounded(self):
        source = (ROOT / "components/performance_diagnostics.py").read_text()
        self.assertIn('HISTORY_KEY = "_hm_perf_history"', source)
        self.assertIn("MAX_HISTORY = 80", source)
        self.assertIn("MAX_OPERATIONS_PER_RUN = 250", source)
        self.assertIn("st.session_state", source)

    def test_measurement_scope_is_metadata_only(self):
        source = (ROOT / "components/performance_diagnostics.py").read_text()
        self.assertIn("No passwords, message text, health data or member notes are captured", source)
        self.assertIn("safe_details", source)
        self.assertIn("Application-state record counts", source)

    def test_backend_measurement_covers_state_and_package_contracts(self):
        source = (ROOT / "components/performance_diagnostics.py").read_text()
        for operation in (
            "db.load_db",
            "db.save_db",
            "storage.load_state",
            "storage.save_state",
            "storage.supabase_read",
            "storage.supabase_write",
            "normalized.users_workflow_read",
            "package.rpc",
        ):
            self.assertIn(operation, source)

    def test_key_pages_have_explicit_measurement_boundaries(self):
        expected = {
            "pages/10_Admin_Dashboard.py": "Admin Dashboard",
            "pages/31_Admin_Member_Communication.py": "Admin Messages",
            "pages/32_Admin_Scheduling.py": "Admin Scheduling",
            "pages/33_My_Schedule.py": "Member My Schedule",
            "pages/38_Admin_Recommendation_Profile_Builder.py": "Recommendation Profile Builder",
            "pages/41_Admin_Packages.py": "Admin Packages",
        }
        for path, label in expected.items():
            source = (ROOT / path).read_text()
            self.assertIn(f'begin_page_measurement("{label}")', source)
            self.assertIn(f'finish_and_render_page_diagnostics("{label}")', source)

    def test_auto_boundaries_cover_member_home_and_daily_log(self):
        source = (ROOT / "components/performance_diagnostics.py").read_text()
        bootstrap = (ROOT / "components/__init__.py").read_text()
        self.assertIn('"02_Member_Home.py": "Member Home"', source)
        self.assertIn('"18_Daily_Log.py": "Member Daily Log"', source)
        self.assertIn("require_admin", source)
        self.assertIn("require_member", source)
        self.assertIn("render_back_to_top", source)
        self.assertIn("inject_keepalive_guard_v96_11", source)
        self.assertIn("install_page_boundary_measurement()", bootstrap)

    def test_admin_workspace_and_current_build_label_are_present(self):
        dashboard = (ROOT / "pages/10_Admin_Dashboard.py").read_text()
        workspace = (ROOT / "pages/47_Admin_Performance_Diagnostics.py").read_text()
        diagnostics = (ROOT / "components/performance_diagnostics.py").read_text()
        build = (ROOT / "components/current_build.py").read_text()
        self.assertIn("Performance Diagnostics", dashboard)
        self.assertIn("Start measurement", workspace)
        self.assertIn("Download measurement JSON", diagnostics)
        self.assertIn('APP_BUILD_VERSION = "v102.5P1"', build)
        self.assertIn('APP_BUILD_LABEL = "Admin Performance Optimisation"', build)


if __name__ == "__main__":
    unittest.main()
