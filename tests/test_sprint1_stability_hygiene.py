from __future__ import annotations

import pathlib
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]


class Sprint1StabilityHygieneTests(unittest.TestCase):
    def test_expired_login_recovers_to_fresh_login(self):
        source = (ROOT / "components/login_expiry_recovery.py").read_text()
        self.assertIn("starting a fresh login", source)
        self.assertIn("window.setTimeout", source)
        self.assertIn("redirectTop(clientLoginUrl)", source)
        self.assertIn("Start fresh HealthyMe login", source)

    def test_general_guidance_uses_member_local_today(self):
        source = (ROOT / "components/daily_guidance_today_default.py").read_text()
        self.assertIn('label == "Guidance Date"', source)
        self.assertIn("member_local_today(member_id)", source)
        self.assertIn("original_key", source)

    def test_schedule_success_clears_entry_fields(self):
        source = (ROOT / "components/sprint1_schedule_hygiene.py").read_text()
        for key in (
            "hm_tz_schedule_type",
            "hm_tz_schedule_title",
            "hm_tz_schedule_date",
            "hm_tz_schedule_start",
            "hm_tz_schedule_end",
            "hm_tz_schedule_mode",
            "hm_tz_schedule_location",
            "hm_tz_schedule_notes",
        ):
            self.assertIn(key, source)
        self.assertIn('if result and not result.get("error")', source)

    def test_member_reschedule_page_installs_form_hygiene(self):
        page = (ROOT / "pages/33_My_Schedule.py").read_text()
        self.assertIn("install_sprint1_schedule_hygiene", page)
        self.assertLess(
            page.index("install_sprint1_schedule_hygiene(schedule_timezone_ui)"),
            page.index("render_member_schedule_page()"),
        )

    def test_admin_schedule_status_is_latest_first(self):
        source = (ROOT / "components/sprint1_schedule_hygiene.py").read_text()
        self.assertIn("reverse=True", source)
        self.assertIn("start_at_utc", source)

    def test_scheduling_navigation_is_visible_at_top(self):
        source = (ROOT / "components/admin_scheduling_default_navigation.py").read_text()
        self.assertIn('location="top"', source)
        self.assertLess(source.index("topbar_with_visible_navigation"), source.index("st.stop()"))

    def test_runtime_error_investigation_is_not_modified(self):
        page = (ROOT / "pages/32_Admin_Scheduling.py").read_text()
        self.assertNotIn("native router error hotfix", page.lower())


if __name__ == "__main__":
    unittest.main()
