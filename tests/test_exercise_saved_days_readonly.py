from __future__ import annotations

import datetime as dt
import unittest

from components import exercise_saved_days_readonly_runtime as runtime
from components import member_exercise_journal_table as table


class _Context:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


class _FakeStreamlit:
    def __init__(self):
        self.session_state = {}
        self.markdown_calls = []
        self.caption_calls = []
        self.warning_calls = []
        self.button_calls = []

    def container(self, *args, **kwargs):
        return _Context()

    def columns(self, count, *args, **kwargs):
        size = count if isinstance(count, int) else len(count)
        return [_Context() for _ in range(size)]

    def date_input(self, label, *args, **kwargs):
        return self.session_state[kwargs["key"]]

    def markdown(self, body, *args, **kwargs):
        self.markdown_calls.append(str(body))

    def caption(self, body, *args, **kwargs):
        self.caption_calls.append(str(body))

    def warning(self, body, *args, **kwargs):
        self.warning_calls.append(str(body))

    def button(self, *args, **kwargs):
        self.button_calls.append((args, kwargs))
        raise AssertionError("Exercise saved days must not render load buttons")


class ExerciseSavedDaysReadonlyTests(unittest.TestCase):
    def setUp(self):
        self.fake_st = _FakeStreamlit()
        self.original_runtime_st = runtime.st
        self.original_loader = table.list_saved_exercise_rows
        runtime.st = self.fake_st

    def tearDown(self):
        runtime.st = self.original_runtime_st
        table.list_saved_exercise_rows = self.original_loader

    def test_history_renders_read_only_without_loading_active_form(self):
        today = dt.date(2026, 8, 2)
        runtime._india_today = lambda: today
        active_date_key = "hm_daily_log_exercise_date"
        pending_date_key = "hm_daily_log_exercise_pending_date"
        self.fake_st.session_state[active_date_key] = today
        self.fake_st.session_state[pending_date_key] = dt.date(2026, 8, 1)

        table.list_saved_exercise_rows = lambda member_id: [
            {
                "log_date": "2026-08-02",
                "item_order": 1,
                "exercise_name": "Morning Walk",
                "scheduled_time": "Morning",
                "duration_or_reps": "30 min",
                "status": "Completed",
                "completion_time": "07:30",
                "member_notes": "Comfortable pace",
            },
            {
                "log_date": "2026-08-01",
                "item_order": 1,
                "exercise_name": "Stretching",
                "scheduled_time": "Evening",
                "duration_or_reps": "2 sets",
                "status": "In Progress",
                "completion_time": None,
                "member_notes": "",
            },
            {
                "log_date": "2026-07-20",
                "item_order": 1,
                "exercise_name": "Outside Range",
                "status": "Completed",
            },
        ]

        table._render_saved_days(
            "member-1",
            "hm_daily_log_exercise",
            active_date_key,
            pending_date_key,
        )

        self.assertEqual(self.fake_st.session_state[active_date_key], today)
        self.assertEqual(
            self.fake_st.session_state[pending_date_key],
            dt.date(2026, 8, 1),
        )
        self.assertEqual(
            self.fake_st.session_state["hm_daily_log_exercise_saved_from"],
            dt.date(2026, 7, 27),
        )
        self.assertEqual(
            self.fake_st.session_state["hm_daily_log_exercise_saved_to"],
            today,
        )
        rendered = "\n".join(self.fake_st.markdown_calls)
        self.assertIn("Morning Walk", rendered)
        self.assertIn("Stretching", rendered)
        self.assertIn("Completed", rendered)
        self.assertIn("In Progress", rendered)
        self.assertNotIn("Outside Range", rendered)
        self.assertEqual(self.fake_st.button_calls, [])
        self.assertTrue(
            any("2 saved exercise day(s)" in value for value in self.fake_st.caption_calls)
        )

    def test_invalid_range_stops_before_loading_rows(self):
        today = dt.date(2026, 8, 2)
        runtime._india_today = lambda: today
        self.fake_st.session_state["exercise_saved_from"] = today
        self.fake_st.session_state["exercise_saved_to"] = today - dt.timedelta(days=1)
        calls = []
        table.list_saved_exercise_rows = lambda member_id: calls.append(member_id) or []

        table._render_saved_days(
            "member-1",
            "exercise",
            "active_date",
            "pending_date",
        )

        self.assertEqual(calls, [])
        self.assertEqual(
            self.fake_st.warning_calls,
            ["From date cannot be after To date."],
        )


if __name__ == "__main__":
    unittest.main()
