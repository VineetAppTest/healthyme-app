from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
MESSAGE_PAGE = ROOT / "pages" / "31_Admin_Member_Communication.py"
GUIDANCE_PAGE = ROOT / "pages" / "22_Admin_Daily_Log_Report.py"


class CommunicationGuidanceFormHygieneContractTest(unittest.TestCase):
    def setUp(self):
        self.message_source = MESSAGE_PAGE.read_text(encoding="utf-8")
        self.guidance_source = GUIDANCE_PAGE.read_text(encoding="utf-8")

    def test_changed_pages_compile(self):
        for path in (MESSAGE_PAGE, GUIDANCE_PAGE):
            compile(path.read_text(encoding="utf-8"), str(path), "exec")

    def test_message_send_uses_success_only_callback(self):
        self.assertIn("on_click=_send_member_message", self.message_source)
        self.assertIn('MESSAGE_MEMBER_KEY = "hm_admin_message_member"', self.message_source)
        self.assertIn('MESSAGE_SUBJECT_KEY = "hm_admin_message_subject"', self.message_source)
        self.assertIn('MESSAGE_BODY_KEY = "hm_admin_message_body"', self.message_source)

        callback = self.message_source.split("def _send_member_message", 1)[1].split(
            "st.set_page_config", 1
        )[0]
        confirmation = callback.index(
            'if not isinstance(result, dict) or not str(result.get("id") or "").strip():'
        )
        clear_subject = callback.index(
            'st.session_state[MESSAGE_SUBJECT_KEY] = ""'
        )
        clear_body = callback.index('st.session_state[MESSAGE_BODY_KEY] = ""')
        self.assertLess(confirmation, clear_subject)
        self.assertLess(confirmation, clear_body)
        self.assertIn("Your entered text has been retained", callback)
        self.assertNotIn("st.rerun()", callback)

    def test_message_success_preserves_member_selection(self):
        callback = self.message_source.split("def _send_member_message", 1)[1].split(
            "st.set_page_config", 1
        )[0]
        self.assertNotIn("pop(MESSAGE_MEMBER_KEY", callback)
        self.assertNotIn('st.session_state[MESSAGE_MEMBER_KEY] = ""', callback)
        self.assertIn("key=MESSAGE_MEMBER_KEY", self.message_source)

    def test_guidance_form_does_not_clear_on_failed_submit(self):
        self.assertIn(
            'with st.form("h9a4_daily_report_structured_note", clear_on_submit=False):',
            self.guidance_source,
        )
        self.assertIn("on_click=_publish_guidance", self.guidance_source)
        self.assertIn("key=GUIDANCE_NOTE_KEY", self.guidance_source)

        callback = self.guidance_source.split("def _publish_guidance", 1)[1].split(
            "st.set_page_config", 1
        )[0]
        confirmation = callback.index(
            'if not isinstance(note, dict) or not str(note.get("id") or "").strip():'
        )
        clear_note = callback.index('st.session_state[GUIDANCE_NOTE_KEY] = ""')
        self.assertLess(confirmation, clear_note)
        self.assertIn("Your entered text has been retained", callback)
        self.assertNotIn("st.rerun()", callback)

    def test_guidance_success_preserves_review_context(self):
        callback = self.guidance_source.split("def _publish_guidance", 1)[1].split(
            "st.set_page_config", 1
        )[0]
        for key in (
            "h9a4_single_day_note_date",
            "h9a4_range_from_date",
            "h9a4_range_to_date",
            "h9a4_general_guidance_date",
        ):
            self.assertIn(key, callback)
            self.assertNotIn(f'pop("{key}"', callback)
        self.assertNotIn("selected_daily_log_member_id] =", callback)

    def test_callbacks_add_no_read_or_reload_path(self):
        message_callback = self.message_source.split(
            "def _send_member_message", 1
        )[1].split("st.set_page_config", 1)[0]
        guidance_callback = self.guidance_source.split(
            "def _publish_guidance", 1
        )[1].split("st.set_page_config", 1)[0]
        for callback in (message_callback, guidance_callback):
            self.assertNotIn("load_db(", callback)
            self.assertNotIn("get_member_messages(", callback)
            self.assertNotIn("get_daily_food_journal_days(", callback)
            self.assertNotIn("st.rerun()", callback)


if __name__ == "__main__":
    unittest.main()
