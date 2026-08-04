from __future__ import annotations

import datetime as dt
import unittest

from components import member_journal_server_autosave as autosave


class _FakeStreamlit:
    def __init__(self):
        self.session_state = {"user_id": "member-1"}
        self.manual_clicks = {}
        self.rerun_count = 0

    def button(self, label, *args, **kwargs):
        key = str(kwargs.get("key") or label)
        return bool(self.manual_clicks.pop(key, False))

    def rerun(self, *args, **kwargs):
        self.rerun_count += 1


class MemberJournalServerAutosaveTests(unittest.TestCase):
    def setUp(self):
        self.fake_st = _FakeStreamlit()
        self.messages = []
        self.original_st = autosave.st
        self.original_page = autosave._current_page_filename
        self.original_message = autosave.flash.set_system_message
        autosave.st = self.fake_st
        autosave._current_page_filename = lambda: "18_Daily_Log.py"
        autosave.flash.set_system_message = (
            lambda message, level="info", *args, **kwargs: self.messages.append(
                (str(message), str(level))
            )
        )
        autosave.install_member_journal_server_autosave()

    def tearDown(self):
        autosave.st = self.original_st
        autosave._current_page_filename = self.original_page
        autosave.flash.set_system_message = self.original_message

    def test_food_autosaves_only_after_meaningful_change(self):
        self.fake_st.session_state["hm_food_journal_date"] = dt.date(2026, 8, 4)
        food_key = "2026-08-04_breakfast_food_0"
        self.fake_st.session_state[food_key] = "Eggs"

        self.assertFalse(self.fake_st.button("Save Day"))
        self.fake_st.session_state[food_key] = "Oats"
        self.assertTrue(self.fake_st.button("Save Day"))
        self.assertEqual(
            self.fake_st.session_state.get("_hm_last_journal_autosave"),
            "food",
        )

        autosave.flash.set_system_message("Saved food journal.", "success")
        self.fake_st.rerun()

        self.assertEqual(self.messages, [])
        self.assertEqual(self.fake_st.rerun_count, 0)
        self.assertFalse(self.fake_st.button("Save Day"))

    def test_blank_new_food_widget_does_not_trigger_autosave(self):
        self.fake_st.session_state["hm_food_journal_date"] = dt.date(2026, 8, 4)
        self.assertFalse(self.fake_st.button("Save Day"))
        self.fake_st.session_state["2026-08-04_breakfast_food_0"] = ""
        self.assertFalse(self.fake_st.button("Save Day"))

    def test_exercise_autosaves_changed_row_once_and_silently(self):
        base = "hm_daily_log_exercise_profile_1_1"
        button_key = f"{base}_save"
        self.fake_st.session_state[f"{base}_status"] = "Not Started"
        self.fake_st.session_state[f"{base}_time"] = None
        self.fake_st.session_state[f"{base}_notes"] = ""

        self.assertFalse(
            self.fake_st.button("Save Progress", key=button_key)
        )
        self.fake_st.session_state[f"{base}_status"] = "Completed"
        self.assertTrue(
            self.fake_st.button("Save Progress", key=button_key)
        )
        self.assertEqual(
            self.fake_st.session_state.get("_hm_last_journal_autosave"),
            "exercise",
        )

        autosave.flash.set_system_message("Progress saved.", "success")
        self.fake_st.rerun()

        self.assertEqual(self.messages, [])
        self.assertEqual(self.fake_st.rerun_count, 0)
        self.assertFalse(
            self.fake_st.button("Save Progress", key=button_key)
        )

    def test_manual_save_keeps_confirmation_and_rerun(self):
        self.fake_st.session_state["hm_food_journal_date"] = dt.date(2026, 8, 4)
        self.fake_st.session_state["2026-08-04_breakfast_food_0"] = "Oats"
        self.fake_st.manual_clicks["Save Day"] = True
        self.assertTrue(self.fake_st.button("Save Day"))

        autosave.flash.set_system_message("Saved manually.", "success")
        self.fake_st.rerun()

        self.assertEqual(self.messages, [("Saved manually.", "success")])
        self.assertEqual(self.fake_st.rerun_count, 1)

    def test_other_pages_do_not_autosave(self):
        autosave._current_page_filename = lambda: "02_Member_Home.py"
        self.fake_st.session_state["hm_food_journal_date"] = dt.date(2026, 8, 4)
        self.fake_st.session_state["2026-08-04_breakfast_food_0"] = "Oats"
        self.assertFalse(self.fake_st.button("Save Day"))


if __name__ == "__main__":
    unittest.main()
