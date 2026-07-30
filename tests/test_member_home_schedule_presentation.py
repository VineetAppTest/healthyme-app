from __future__ import annotations

import ast
import datetime as dt
import pathlib
import unittest

from components.member_home_schedule_presentation import (
    prepare_member_home_upcoming_schedules,
)


ROOT = pathlib.Path(__file__).resolve().parents[1]
UTC = dt.timezone.utc


class MemberHomeSchedulePresentationTests(unittest.TestCase):
    def test_latest_future_schedule_is_rendered_first_and_ended_rows_are_hidden(self):
        rows = [
            {
                "id": "morning",
                "status": "acknowledged",
                "start_at_utc": "2026-07-30T05:15:00Z",
                "end_at_utc": "2026-07-30T06:15:00Z",
            },
            {
                "id": "evening-ended",
                "status": "acknowledged",
                "start_at_utc": "2026-07-30T16:00:00Z",
                "end_at_utc": "2026-07-30T16:30:00Z",
            },
            {
                "id": "evening-open",
                "status": "acknowledged",
                "start_at_utc": "2026-07-30T16:45:00Z",
                "end_at_utc": "2026-07-30T17:15:00Z",
            },
            {
                "id": "next-day",
                "status": "acknowledged",
                "start_at_utc": "2026-07-31T05:15:00Z",
                "end_at_utc": "2026-07-31T06:00:00Z",
            },
        ]

        visible = prepare_member_home_upcoming_schedules(
            rows,
            now_utc=dt.datetime(2026, 7, 30, 17, 0, tzinfo=UTC),
            limit=5,
        )

        self.assertEqual([row["id"] for row in visible], ["next-day", "evening-open"])

    def test_closed_schedule_is_not_returned(self):
        rows = [
            {
                "id": "completed",
                "status": "completed",
                "start_at_utc": "2026-08-01T05:00:00Z",
                "end_at_utc": "2026-08-01T05:30:00Z",
            }
        ]
        self.assertEqual(
            prepare_member_home_upcoming_schedules(
                rows,
                now_utc=dt.datetime(2026, 7, 30, tzinfo=UTC),
            ),
            [],
        )

    def test_legacy_member_local_time_is_supported(self):
        rows = [
            {
                "id": "legacy",
                "status": "scheduled",
                "schedule_date": "2026-07-31",
                "start_time": "10:45 AM",
                "end_time": "11:30 AM",
                "member_timezone_name": "Asia/Kolkata",
            }
        ]
        visible = prepare_member_home_upcoming_schedules(
            rows,
            now_utc=dt.datetime(2026, 7, 30, 17, 0, tzinfo=UTC),
        )
        self.assertEqual([row["id"] for row in visible], ["legacy"])

    def test_correction_does_not_change_schedule_or_package_business_state(self):
        helper = (ROOT / "components/member_home_schedule_presentation.py").read_text()
        for forbidden in (
            "save_db(",
            "update_member_schedule_status(",
            "create_timezone_aware_member_schedule(",
            "assign_or_replace_member_package(",
            'session_counted" =',
        ):
            self.assertNotIn(forbidden, helper)

    def test_member_home_upcoming_schedule_is_collapsible_after_filtering(self):
        source = (ROOT / "pages/02_Member_Home.py").read_text()
        ast.parse(source)
        self.assertIn("with st.expander(", source)
        self.assertIn('f"Upcoming Schedule ({len(upcoming_schedules)})"', source)
        self.assertLess(
            source.index("list_upcoming_member_schedules(user_id, limit=5)"),
            source.index("with st.expander("),
        )
        self.assertIn("expanded=True", source)
        for forbidden in (
            "update_member_schedule_status(",
            "session_counted =",
            "save_db(",
        ):
            self.assertNotIn(forbidden, source)

    def test_member_home_header_renders_before_slow_workflow_reads(self):
        source = (ROOT / "pages/02_Member_Home.py").read_text()
        self.assertIn("hm-member-home-local-style-v2", source)
        self.assertIn("padding-top:0!important", source)
        render_start = source.index(
            "# Render the local spacing override and first visible controls"
        )
        workflow_read = source.index("get_workflow(user_id)")
        self.assertLess(render_start, workflow_read)
        self.assertLess(source.index("\n_render_member_home_css()\n"), workflow_read)
        self.assertLess(source.index("\n_render_member_utility_bar()\n"), workflow_read)
        self.assertLess(source.index('topbar(\n    "Member Home"'), workflow_read)
        self.assertEqual(source.count("\n_render_member_home_css()\n"), 1)
        self.assertEqual(source.count("\n_render_member_utility_bar()\n"), 1)

    def test_installer_and_export_discovery_are_active(self):
        bootstrap = (ROOT / "components/__init__.py").read_text()
        gate = (ROOT / "components/performance_measurement_gate.py").read_text()
        self.assertIn("install_member_home_schedule_presentation()", bootstrap)
        self.assertIn("Member Performance Diagnostics", gate)
        self.assertIn("Start Member performance measurement", gate)
        self.assertIn("Download Member measurement JSON", gate)
        self.assertIn("before logging out", gate)


if __name__ == "__main__":
    unittest.main()
