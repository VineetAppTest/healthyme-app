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

    def test_history_defaults_to_today_without_loading_active_form(self):
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
            today,
        )
        self.assertEqual(
            self.fake_st.session_state["hm_daily_log_exercise_saved_to"],
            today,
        )
        rendered = "\n".join(self.fake_st.markdown_calls)
        self.assertIn("Morning Walk", rendered)
        self.assertIn("Completed", rendered)
        self.assertNotIn("Stretching", rendered)
        self.assertEqual(self.fake_st.button_calls, [])
        self.assertTrue(
            any("1 saved exercise day(s)" in value for value in self.fake_st.caption_calls)
        )

    def test_existing_seven_day_state_is_reset_once_to_today(self):
        today = dt.date(2026, 8, 2)
        runtime._india_today = lambda: today
        prefix = "hm_daily_log_exercise"
        self.fake_st.session_state[f"{prefix}_saved_from"] = today - dt.timedelta(days=6)
        self.fake_st.session_state[f"{prefix}_saved_to"] = today
        table.list_saved_exercise_rows = lambda member_id: []

        table._render_saved_days("member-1", prefix, "active_date", "pending_date")

        self.assertEqual(self.fake_st.session_state[f"{prefix}_saved_from"], today)
        self.assertEqual(self.fake_st.session_state[f"{prefix}_saved_to"], today)
        self.assertTrue(
            self.fake_st.session_state[f"{prefix}_saved_filter_today_v2"]
        )

    def test_invalid_range_stops_before_loading_rows_after_initialisation(self):
        today = dt.date(2026, 8, 2)
        runtime._india_today = lambda: today
        prefix = "exercise"
        self.fake_st.session_state[f"{prefix}_saved_filter_today_v2"] = True
        self.fake_st.session_state[f"{prefix}_saved_from"] = today
        self.fake_st.session_state[f"{prefix}_saved_to"] = today - dt.timedelta(days=1)
        calls = []
        table.list_saved_exercise_rows = lambda member_id: calls.append(member_id) or []

        table._render_saved_days(
            "member-1",
            prefix,
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
