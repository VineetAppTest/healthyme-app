from __future__ import annotations

import datetime as dt
import pathlib
import unittest

from components.admin_uiux_corrections import (
    _add_minutes_to_time,
    _resolve_end_after_start_change,
)


ROOT = pathlib.Path(__file__).resolve().parents[1]


class AdminUiUxCorrectionTests(unittest.TestCase):
    def test_default_end_is_thirty_minutes_after_start(self):
        self.assertEqual(_add_minutes_to_time(dt.time(10, 0)), dt.time(10, 30))
        self.assertEqual(_add_minutes_to_time(dt.time(14, 30)), dt.time(15, 0))

    def test_untouched_end_tracks_start_change(self):
        next_end, next_auto, changed = _resolve_end_after_start_change(
            dt.time(14, 30),
            dt.time(10, 30),
            dt.time(10, 30),
        )
        self.assertTrue(changed)
        self.assertEqual(next_end, dt.time(15, 0))
        self.assertEqual(next_auto, dt.time(15, 0))

    def test_manual_end_remains_editable_and_is_preserved(self):
        next_end, next_auto, changed = _resolve_end_after_start_change(
            dt.time(14, 30),
            dt.time(15, 15),
            dt.time(10, 30),
        )
        self.assertFalse(changed)
        self.assertEqual(next_end, dt.time(15, 15))
        self.assertEqual(next_auto, dt.time(10, 30))

    def test_package_selector_is_prominent_without_assignment_logic_changes(self):
        page = (ROOT / "pages/41_Admin_Packages.py").read_text()
        helper = (ROOT / "components/admin_uiux_corrections.py").read_text()
        self.assertIn("render_admin_packages_uiux_styles()", page)
        self.assertIn("st-key-hm_pkg_assign_package", helper)
        self.assertIn("Choose the active package to assign, replace or renew", helper)
        self.assertNotIn("assign_or_replace_member_package", helper)

    def test_schedule_scope_places_success_at_submit_and_keeps_form_logic(self):
        page = (ROOT / "pages/32_Admin_Scheduling.py").read_text()
        helper = (ROOT / "components/admin_uiux_corrections.py").read_text()
        scheduling = (ROOT / "components/admin_scheduling_consolidated.py").read_text()
        self.assertIn("with admin_scheduling_uiux_scope(admin_scheduling):", page)
        self.assertIn("button_with_nearby_success", helper)
        self.assertIn("original_render_flash()", helper)
        self.assertIn("_sync_schedule_end_from_start", helper)
        self.assertIn("Create Schedule / Notify Member", scheduling)
        self.assertIn("create_timezone_aware_member_schedule", scheduling)

    def test_scope_excludes_auth_routing_and_business_rules(self):
        helper = (ROOT / "components/admin_uiux_corrections.py").read_text()
        for forbidden in (
            "require_admin",
            "require_member",
            "switch_page",
            "authorization_id",
            "save_db",
            "create_timezone_aware_member_schedule",
            "assign_or_replace_member_package",
        ):
            self.assertNotIn(forbidden, helper)


if __name__ == "__main__":
    unittest.main()
