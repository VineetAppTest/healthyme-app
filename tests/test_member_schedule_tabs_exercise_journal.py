from __future__ import annotations

import datetime as dt
import pathlib
import unittest

from components.member_exercise_journal_table import build_exercise_log_payload


ROOT = pathlib.Path(__file__).resolve().parents[1]


class MemberScheduleTabsExerciseJournalTests(unittest.TestCase):
    def test_my_schedule_uses_exact_three_tabs_and_preserves_actions(self):
        source = (ROOT / "components/member_schedule_tabbed_page.py").read_text()
        self.assertIn(
            '["Package Subscribed", "Upcoming Schedule", "Session Usage"]',
            source,
        )
        self.assertIn("schedule_ui._render_package", source)
        self.assertIn("schedule_ui._render_member_ledger", source)
        self.assertIn("Acknowledge schedule", source)
        self.assertIn("Request Reschedule", source)
        self.assertIn("Submit Reschedule Request", source)

    def test_my_schedule_page_uses_tabbed_renderer_and_keeps_measurement(self):
        source = (ROOT / "pages/33_My_Schedule.py").read_text()
        self.assertIn("render_tabbed_member_schedule_page", source)
        self.assertIn('begin_page_measurement("Member My Schedule")', source)
        self.assertIn('finish_and_render_page_diagnostics("Member My Schedule")', source)

    def test_member_selected_values_are_saved_to_daily_log_payload(self):
        payload = build_exercise_log_payload(
            member_id="member-1",
            log_date="2026-07-29",
            profile={"id": "profile-1", "profile_name": "Starter"},
            day_number=2,
            item_order=1,
            selected_activity="Walk & Stretches",
            selected_timing="Night",
            selected_duration="30 min & 2 sets of 10",
            remarks="Completed comfortably",
            status="Completed",
            completion_time=dt.time(22, 0),
            selected_definition={
                "difficulty": "Easy",
                "equipment": "None",
                "benefits": "Mobility",
                "instruction": "Walk, then stretch",
                "image_reference": "",
            },
        )
        self.assertEqual(payload["exercise_name"], "Walk & Stretches")
        self.assertEqual(payload["scheduled_time"], "Night")
        self.assertEqual(payload["duration_or_reps"], "30 min & 2 sets of 10")
        self.assertEqual(payload["member_notes"], "Completed comfortably")
        self.assertEqual(payload["completion_time"], "22:00")
        self.assertEqual(payload["status"], "Completed")

    def test_exercise_journal_has_editable_requested_columns(self):
        source = (ROOT / "components/member_exercise_journal_table.py").read_text()
        for label in ("Timing", "Activity", "Duration / Sets", "Remarks"):
            self.assertIn(label, source)
        self.assertIn("st.selectbox", source)
        self.assertIn("st.text_input", source)
        self.assertIn("Save Exercise Entry", source)
        self.assertIn("Status", source)
        self.assertIn("Completion time", source)

    def test_exercise_journal_does_not_write_to_profile_or_repository(self):
        source = (ROOT / "components/member_exercise_journal_table.py").read_text()
        for forbidden in (
            "hm_recommendation_profiles",
            "hm_recommendation_profile_items",
            "save_recommendation",
            "update_recommendation",
            "save_exercise_repository",
        ):
            self.assertNotIn(forbidden, source)
        self.assertIn("save_member_exercise_log", source)

    def test_shared_renderer_bootstrap_keeps_both_entry_points_aligned(self):
        bootstrap = (
            ROOT / "components/member_exercise_journal_table_bootstrap.py"
        ).read_text()
        components_init = (ROOT / "components/__init__.py").read_text()
        self.assertIn(
            "journal.render_member_exercise_journal = render_member_exercise_journal_table",
            bootstrap,
        )
        self.assertIn("install_member_exercise_journal_table()", components_init)


if __name__ == "__main__":
    unittest.main()
