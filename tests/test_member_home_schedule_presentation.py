from __future__ import annotations

import ast
import datetime as dt
import pathlib
import unittest

from components.member_home_schedule_presentation import (
    member_home_schedule_phase,
    prepare_member_home_upcoming_schedules,
)


ROOT = pathlib.Path(__file__).resolve().parents[1]
UTC = dt.timezone.utc


class MemberHomeSchedulePresentationTests(unittest.TestCase):
    def test_latest_future_schedule_is_rendered_first_and_ended_rows_are_hidden(self):
        rows = [
            {
                "id": "morning",
                "status": "scheduled",
                "start_at_utc": "2026-07-30T05:15:00Z",
                "end_at_utc": "2026-07-30T06:15:00Z",
            },
            {
                "id": "evening-ended",
                "status": "scheduled",
                "start_at_utc": "2026-07-30T16:00:00Z",
                "end_at_utc": "2026-07-30T16:30:00Z",
            },
            {
                "id": "evening-open",
                "status": "scheduled",
                "start_at_utc": "2026-07-30T16:45:00Z",
                "end_at_utc": "2026-07-30T17:15:00Z",
            },
            {
                "id": "next-day",
                "status": "scheduled",
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

    def test_duplicate_schedule_ids_are_rendered_once(self):
        rows = [
            {
                "id": "same-schedule",
                "status": "scheduled",
                "start_at_utc": "2026-08-08T04:30:00Z",
                "end_at_utc": "2026-08-08T05:00:00Z",
                "created_at": "2026-08-04T10:00:00Z",
            },
            {
                "id": "same-schedule",
                "status": "scheduled",
                "start_at_utc": "2026-08-08T04:30:00Z",
                "end_at_utc": "2026-08-08T05:00:00Z",
                "created_at": "2026-08-04T09:00:00Z",
            },
            {
                "id": "different-schedule",
                "status": "scheduled",
                "start_at_utc": "2026-08-07T04:30:00Z",
                "end_at_utc": "2026-08-07T05:00:00Z",
            },
        ]

        visible = prepare_member_home_upcoming_schedules(
            rows,
            now_utc=dt.datetime(2026, 8, 4, tzinfo=UTC),
            limit=6,
        )

        self.assertEqual(
            [row["id"] for row in visible],
            ["same-schedule", "different-schedule"],
        )
        self.assertEqual(
            visible[0]["created_at"],
            "2026-08-04T10:00:00Z",
        )

    def test_acknowledged_schedule_disappears_from_member_home(self):
        rows = [
            {
                "id": "acknowledged",
                "status": "acknowledged",
                "start_at_utc": "2026-08-08T04:30:00Z",
                "end_at_utc": "2026-08-08T05:00:00Z",
            },
            {
                "id": "scheduled",
                "status": "scheduled",
                "start_at_utc": "2026-08-09T04:30:00Z",
                "end_at_utc": "2026-08-09T05:00:00Z",
            },
        ]

        visible = prepare_member_home_upcoming_schedules(
            rows,
            now_utc=dt.datetime(2026, 8, 4, tzinfo=UTC),
            limit=6,
        )

        self.assertEqual([row["id"] for row in visible], ["scheduled"])

    def test_acknowledged_schedule_returns_inside_48_hours_until_read(self):
        row = {
            "id": "acknowledged",
            "status": "acknowledged",
            "start_at_utc": "2026-08-08T04:30:00Z",
            "end_at_utc": "2026-08-08T05:00:00Z",
        }
        now = dt.datetime(2026, 8, 6, 5, 0, tzinfo=UTC)

        visible = prepare_member_home_upcoming_schedules(
            [row], now_utc=now, limit=6
        )

        self.assertEqual([item["id"] for item in visible], ["acknowledged"])
        self.assertEqual(visible[0]["_member_home_phase"], "reminder")
        self.assertEqual(member_home_schedule_phase(row, now_utc=now), "reminder")

        row["member_home_48h_read_at"] = "2026-08-06T05:01:00Z"
        self.assertEqual(
            prepare_member_home_upcoming_schedules([row], now_utc=now, limit=6),
            [],
        )

    def test_pending_reschedule_remains_visible_until_admin_decides(self):
        row = {
            "id": "pending",
            "status": "acknowledged",
            "reschedule_request_status": "pending",
            "start_at_utc": "2026-08-12T04:30:00Z",
            "end_at_utc": "2026-08-12T05:00:00Z",
        }
        visible = prepare_member_home_upcoming_schedules(
            [row],
            now_utc=dt.datetime(2026, 8, 4, tzinfo=UTC),
            limit=6,
        )
        self.assertEqual(visible[0]["_member_home_phase"], "reschedule_pending")

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

    def test_member_home_uses_two_pills_and_three_by_two_card_grids(self):
        source = (ROOT / "pages/02_Member_Home.py").read_text()
        ast.parse(source)
        self.assertIn("list_upcoming_member_schedules(user_id, limit=6)", source)
        self.assertIn("get_member_messages(user_id, limit=6)", source)
        self.assertIn("for row_start in range(0, len(upcoming_schedules), 3):", source)
        self.assertGreaterEqual(source.count('st.columns(3, gap="small")'), 2)
        self.assertIn("for row_start in range(0, len(unique_messages), 3):", source)
        self.assertIn('st.columns(3, gap="small")', source)
        self.assertIn("hm-home-grid-anchor", source)
        self.assertIn("hm-message-grid-anchor", source)
        self.assertLess(
            source.rindex("_has_upcoming_schedule = _render_upcoming_schedules(user_id)"),
            source.rindex("_render_messages(user_id, show_divider=_has_upcoming_schedule)"),
        )
        schedule_slice = source[
            source.index("def _render_upcoming_schedules") :
            source.index("def _render_task_button")
        ]
        schedule_empty_guard = schedule_slice.index("if not upcoming_schedules:")
        schedule_expander = schedule_slice.index("with st.expander(")
        self.assertIn(
            "return False",
            schedule_slice[schedule_empty_guard:schedule_expander],
        )
        self.assertLess(schedule_empty_guard, schedule_expander)
        self.assertIn("with st.expander(", schedule_slice)
        self.assertIn("hm-upcoming-schedule-anchor", schedule_slice)
        self.assertIn("expanded=True", schedule_slice)
        self.assertIn('f"Upcoming Consultation ({len(upcoming_schedules)})"', schedule_slice)
        self.assertNotIn("No upcoming consultation requires action.", schedule_slice)
        message_slice = source[
            source.index("def _render_messages") :
            source.index("def _render_upcoming_schedules")
        ]
        message_empty_guard = message_slice.index("if not unique_messages:")
        message_expander = message_slice.index('with st.expander("Message from Nutritionist"')
        self.assertIn(
            "return False",
            message_slice[message_empty_guard:message_expander],
        )
        self.assertLess(message_empty_guard, message_expander)
        self.assertIn('with st.expander("Message from Nutritionist"', message_slice)
        self.assertIn("hm-message-pill-anchor", message_slice)
        self.assertNotIn("No new message from your nutritionist.", message_slice)
        self.assertIn("UPCOMING_CONSULTATION_ADVISORY", schedule_slice)
        for forbidden in (
            "update_member_schedule_status(",
            "session_counted =",
            "save_db(",
        ):
            self.assertNotIn(forbidden, source)

    def test_other_fluid_time_uses_balanced_hour_minute_period_controls(self):
        source = (ROOT / "pages/18_Daily_Log.py").read_text()
        ast.parse(source)
        self.assertIn("def _render_fluid_time_selector", source)
        self.assertIn('st.columns([1, 1, 1.2], gap="small")', source)
        self.assertIn('["HH"] + [f"{value:02d}" for value in range(1, 13)]', source)
        self.assertIn('["MM"] + [f"{value:02d}" for value in range(60)]', source)
        self.assertIn('["AM/PM", "AM", "PM"]', source)
        self.assertIn("hm-fluid-time-grid-anchor", source)
        self.assertNotIn("fluid_time = st.time_input(", source)

    def test_every_eligible_home_schedule_has_accept_and_reschedule_actions(self):
        helper = (ROOT / "components/member_home_schedule_presentation.py").read_text()
        page = (ROOT / "pages/02_Member_Home.py").read_text()
        db_source = (ROOT / "components/db.py").read_text()

        self.assertIn('"Accept"', helper)
        self.assertIn('"Accepted"', helper)
        self.assertIn('"Reschedule"', helper)
        self.assertIn('"Reschedule pending"', helper)
        self.assertIn("acknowledge_member_schedule", helper)
        self.assertIn("on_click=_accept_member_home_schedule", helper)
        self.assertNotIn('"Acknowledge"', helper)
        self.assertIn('st.switch_page("pages/33_My_Schedule.py")', helper)
        self.assertIn(
            'st.session_state["hm_member_schedule_active_section"] = "Upcoming Schedule"',
            helper,
        )
        self.assertIn("hm_tz_show_reschedule_", helper)
        self.assertIn("hm-member-schedule-action-anchor", helper)
        self.assertIn("_ACTION_RENDERED_IDS_KEY", helper)
        self.assertIn("seen_schedule_keys", helper)
        self.assertIn('status == "acknowledged"', helper)
        self.assertIn('"Read"', helper)
        self.assertIn("mark_member_schedule_reminder_read", helper)

        # Advisory copy is displayed once between the pill and the compact cards.
        self.assertIn("UPCOMING_CONSULTATION_ADVISORY", page)
        self.assertIn("additional session count", page)
        self.assertIn("def mark_member_schedule_reminder_read", db_source)
        self.assertIn("if not _hm_v104b11_is_within_hours(row, hours=48)", db_source)

    def test_member_home_header_renders_before_slow_workflow_reads(self):
        source = (ROOT / "pages/02_Member_Home.py").read_text()
        self.assertIn("hm-member-home-local-style-v3", source)
        self.assertIn("hm-member-home-root-anchor", source)
        self.assertIn("# Render one structural header shell", source)
        self.assertNotIn("html,body,#root{margin-top:0", source)
        render_start = source.index("# Render one structural header shell")
        workflow_read = source.index("get_workflow(user_id)")
        self.assertLess(render_start, workflow_read)
        self.assertLess(source.index("_render_member_home_css()", render_start), workflow_read)
        self.assertLess(source.index("_render_member_utility_bar()", render_start), workflow_read)
        self.assertLess(source.index('topbar(\n        "Member Home"', render_start), workflow_read)
        self.assertEqual(source.count("    _render_member_home_css()"), 1)
        self.assertEqual(source.count("    _render_member_utility_bar()"), 1)

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
