from __future__ import annotations

import unittest

from components import flash


class _FakeStreamlit:
    def __init__(self):
        self.session_state = {}


class FlashJournalSilentFeedbackTests(unittest.TestCase):
    def setUp(self):
        self.fake_st = _FakeStreamlit()
        self.original_st = flash.st
        flash.st = self.fake_st
        # Simulate Daily Log binding the canonical function before the later
        # autosave wrapper replaces components.flash.set_system_message.
        self.bound_set_system_message = getattr(
            flash.set_system_message,
            "_hm_original",
            flash.set_system_message,
        )

    def tearDown(self):
        flash.st = self.original_st

    def test_direct_imported_autosave_success_is_silent(self):
        self.fake_st.session_state[flash.JOURNAL_AUTOSAVE_SILENT_MESSAGE_KEY] = "food"
        self.fake_st.session_state[flash.JOURNAL_AUTOSAVE_SILENT_RERUN_KEY] = "food"

        self.bound_set_system_message("Saved food journal.", "success")

        self.assertNotIn(flash.FLASH_KEY, self.fake_st.session_state)
        self.assertNotIn(
            flash.JOURNAL_AUTOSAVE_SILENT_MESSAGE_KEY,
            self.fake_st.session_state,
        )
        # The rerun wrapper consumes this separately after the save handler.
        self.assertEqual(
            self.fake_st.session_state.get(
                flash.JOURNAL_AUTOSAVE_SILENT_RERUN_KEY
            ),
            "food",
        )

    def test_manual_success_remains_visible(self):
        self.bound_set_system_message("Saved manually.", "success")

        self.assertEqual(
            self.fake_st.session_state[flash.FLASH_KEY]["message"],
            "Saved manually.",
        )
        self.assertEqual(
            self.fake_st.session_state[flash.FLASH_KEY]["level"],
            "success",
        )

    def test_autosave_error_remains_visible_and_rerun_is_not_suppressed(self):
        self.fake_st.session_state[flash.JOURNAL_AUTOSAVE_SILENT_MESSAGE_KEY] = "food"
        self.fake_st.session_state[flash.JOURNAL_AUTOSAVE_SILENT_RERUN_KEY] = "food"

        self.bound_set_system_message("Save failed.", "error")

        self.assertEqual(
            self.fake_st.session_state[flash.FLASH_KEY]["message"],
            "Save failed.",
        )
        self.assertEqual(
            self.fake_st.session_state[flash.FLASH_KEY]["level"],
            "error",
        )
        self.assertNotIn(
            flash.JOURNAL_AUTOSAVE_SILENT_RERUN_KEY,
            self.fake_st.session_state,
        )


if __name__ == "__main__":
    unittest.main()
