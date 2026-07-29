from __future__ import annotations

import pathlib
import unittest

from components.performance_measurement_gate import _member_measurement_history


ROOT = pathlib.Path(__file__).resolve().parents[1]


class MemberPerformanceExportTests(unittest.TestCase):
    def test_member_history_filters_out_admin_runs(self):
        history = [
            {"page": "Member Home", "run_id": "m1"},
            {"page": "Admin Dashboard", "run_id": "a1"},
            {"page": "Member Daily Log", "run_id": "m2"},
            {"page": "Member My Schedule", "run_id": "m3"},
        ]
        self.assertEqual(
            [row["run_id"] for row in _member_measurement_history(history)],
            ["m1", "m2", "m3"],
        )

    def test_member_export_is_direct_and_session_local(self):
        source = (ROOT / "components/performance_measurement_gate.py").read_text()
        self.assertIn("Download Member measurement JSON", source)
        self.assertIn("healthyme_member_performance_measurements.json", source)
        self.assertIn("diagnostics.measurement_history()", source)
        self.assertIn("before logging out", source)

    def test_member_export_does_not_persist_diagnostics(self):
        source = (ROOT / "components/performance_measurement_gate.py").read_text()
        for forbidden in (
            "save_db",
            "save_state",
            "supabase",
            "insert(",
            "update(",
            "require_admin",
            "require_member",
            "switch_page",
        ):
            self.assertNotIn(forbidden, source)

    def test_existing_measurement_gate_remains_enabled(self):
        source = (ROOT / "components/performance_measurement_gate.py").read_text()
        self.assertIn("_hm_perf_enable_gate", source)
        self.assertIn("diagnostics.begin_page_measurement", source)
        self.assertIn("diagnostics.finish_and_render_page_diagnostics", source)

    def test_admin_instructions_cover_member_download(self):
        workspace = (ROOT / "pages/47_Admin_Performance_Diagnostics.py").read_text()
        self.assertIn("append `?perf=1`", workspace)
        self.assertIn("Member Home, Daily Log and My Schedule", workspace)
        self.assertIn("Download Member measurement JSON before logging out", workspace)


if __name__ == "__main__":
    unittest.main()
