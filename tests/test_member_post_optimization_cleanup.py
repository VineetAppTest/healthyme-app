from __future__ import annotations

import pathlib
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]


class MemberPostOptimizationCleanupTests(unittest.TestCase):
    def test_cleanup_is_installed_after_temporary_measurement_gate(self):
        source = (ROOT / "components/__init__.py").read_text()
        self.assertIn("install_member_post_optimization_cleanup", source)
        self.assertLess(
            source.index("install_performance_measurement_gate()"),
            source.index("install_member_post_optimization_cleanup()"),
        )

    def test_other_fluid_time_is_one_full_width_editable_field(self):
        source = (
            ROOT / "components/member_post_optimization_cleanup.py"
        ).read_text()
        self.assertIn('_FLUID_TIME_PREFIX = "hm_h9a4c_fluid_time_"', source)
        self.assertIn("corrected_time_input", source)
        self.assertIn("current_text_input(label, **text_kwargs)", source)
        self.assertIn('"placeholder": "Example: 10:30 PM"', source)
        self.assertIn('"max_chars": 8', source)
        self.assertIn('input[placeholder="Example: 10:30 PM"]', source)
        self.assertIn("min-height:2.70rem!important", source)
        self.assertIn("return parsed", source)

    def test_time_parser_supports_member_friendly_formats(self):
        source = (
            ROOT / "components/member_post_optimization_cleanup.py"
        ).read_text()
        for time_format in ("%I:%M %p", "%H:%M", "%I %p"):
            self.assertIn(time_format, source)
        self.assertIn("Enter time as HH:MM or HH:MM AM/PM", source)

    def test_member_header_and_footer_match_home_shell_gap(self):
        source = (
            ROOT / "components/member_post_optimization_cleanup.py"
        ).read_text()
        self.assertIn("hm-member-shell-production-cleanup-v1", source)
        self.assertIn("margin:0 0 .52rem 0!important", source)
        self.assertIn("height:2.46rem!important", source)
        self.assertIn("position:static!important;top:0!important", source)
        self.assertIn('div[data-testid="stElementContainer"]:has(.hm-back-to-top)', source)
        self.assertIn("height:0!important;min-height:0!important", source)

    def test_visible_performance_diagnostics_are_retired(self):
        source = (
            ROOT / "components/member_post_optimization_cleanup.py"
        ).read_text()
        self.assertIn("finish_without_visible_panel", source)
        self.assertIn("diagnostics.set_measurement_enabled(False)", source)
        self.assertIn("diagnostics.clear_measurement_history()", source)
        self.assertIn("_unwrap_performance_footer", source)
        self.assertNotIn("Member Performance Diagnostics", source)
        self.assertNotIn("Start Member performance measurement", source)
        self.assertNotIn("Download Member measurement JSON", source)

    def test_cleanup_does_not_change_auth_routing_or_business_writes(self):
        source = (
            ROOT / "components/member_post_optimization_cleanup.py"
        ).read_text()
        for forbidden in (
            "logout_current_user",
            "require_admin",
            "require_member",
            "st.switch_page",
            "save_daily_food_journal_day",
            "save_member_exercise_log",
            "assign_or_replace_member_package",
            "request_timezone_aware_reschedule",
        ):
            self.assertNotIn(forbidden, source)


if __name__ == "__main__":
    unittest.main()
