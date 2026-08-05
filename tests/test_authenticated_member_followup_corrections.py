from __future__ import annotations

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class AuthenticatedMemberFollowupCorrectionTests(unittest.TestCase):
    def test_member_home_owns_schedule_and_message_layout(self):
        source = (ROOT / "components/member_home_side_by_side_runtime.py").read_text()
        installer = source[source.index("def install_member_home_side_by_side_runtime"):]
        self.assertIn("without relocating page sections", installer)
        self.assertNotIn("ensure_pair()", installer)
        self.assertNotIn("left.expander", installer)
        self.assertNotIn("message_expander", installer)
        self.assertNotIn("margin:-", installer)

    def test_header_has_no_negative_offset_and_schedule_is_two_across(self):
        page = (ROOT / "pages/02_Member_Home.py").read_text()
        presentation = (ROOT / "components/member_home_schedule_presentation.py").read_text()
        self.assertIn('padding-top:.18rem!important', page)
        self.assertIn('f"Upcoming Schedule ({len(upcoming_schedules)})"', page)
        self.assertIn('range(0, len(upcoming_schedules), 2)', page)
        self.assertIn('st.columns(2, gap="medium")', page)
        self.assertNotIn('top:-1.75rem', presentation)
        self.assertIn('font-size:.72rem!important', presentation)

    def test_task_card_and_balanced_columns_have_breathing_space(self):
        page = (ROOT / "pages/02_Member_Home.py").read_text()
        self.assertIn('min-height:15.75rem', page)
        self.assertIn(':has(.hm-member-home-balanced-card){align-items:stretch', page)
        self.assertIn('Due date: <b>&nbsp;{due_date}</b>', page)
        self.assertIn('SHOW_MEMBER_REFERENCE_LIBRARY = False', page)

    def test_task_allocation_sentence_is_removed_only_from_member_message_body(self):
        page = (ROOT / "pages/02_Member_Home.py").read_text()
        self.assertIn('replace("Nutritionist has allocated a Task.", "")', page)
        self.assertIn("_member_message_text(msg.get('message',''))", page)

    def test_food_journal_route_and_saved_day_contract(self):
        page = (ROOT / "pages/18_Daily_Log.py").read_text()
        route = (ROOT / "components/daily_log_widget_route_preservation.py").read_text()
        self.assertIn('"hm_daily_",', route)
        self.assertIn('key=f"hm_daily_log_{date_key}_{key}_food_{idx}"', page)
        self.assertIn('key=f"hm_daily_log_{date_key}_{key}_portion_{idx}"', page)
        self.assertIn('key=f"hm_daily_log_{date_key}_{key}_mood"', page)
        self.assertIn('key=f"hm_daily_log_{date_key}_{key}_energy"', page)
        self.assertNotIn('Viewing saved entries for', page)
        self.assertNotIn('"Open saved day"', page)
        self.assertNotIn('hm_h9a4c_load_', page)


if __name__ == "__main__":
    unittest.main()
