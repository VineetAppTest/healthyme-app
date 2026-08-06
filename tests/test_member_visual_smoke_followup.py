from __future__ import annotations

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class MemberVisualSmokeFollowupTests(unittest.TestCase):
    def test_member_header_controls_share_one_height_contract(self):
        source = (ROOT / "components/member_home_global_header_runtime.py").read_text()
        page = (ROOT / "pages/02_Member_Home.py").read_text()

        self.assertIn('div[data-testid="column"]', source)
        self.assertIn('div[data-testid="stColumn"]', source)
        self.assertIn('height:2.46rem!important', source)
        self.assertIn('justify-content:center!important', source)
        utility_start = page.index("def _render_member_utility_bar")
        utility_end = page.index("def _render_messages", utility_start)
        self.assertIn('vertical_alignment="center"', page[utility_start:utility_end])

    def test_member_task_buttons_use_short_done_labels_in_one_equal_row(self):
        runtime = (
            ROOT / "components/member_home_side_by_side_runtime.py"
        ).read_text()
        page = (ROOT / "pages/02_Member_Home.py").read_text()

        self.assertIn('"NSP Page 1 Done"', runtime)
        self.assertIn('"NSP Page 2 Done"', runtime)
        self.assertNotIn('"NSP Page 1 Completed"', runtime)
        self.assertNotIn('"NSP Page 2 Completed"', runtime)
        self.assertIn('label = "Body Mind Done" if body_done else "Body Mind"', page)
        self.assertEqual(page.count("[1, 1, 1],"), 2)
        self.assertGreaterEqual(page.count('vertical_alignment="center"'), 3)

    def test_upcoming_schedule_pill_and_card_are_content_sized(self):
        presentation = (
            ROOT / "components/member_home_schedule_presentation.py"
        ).read_text()
        page = (ROOT / "pages/02_Member_Home.py").read_text()

        self.assertIn('width:max-content!important', presentation)
        self.assertIn('min-width:15.5rem!important', presentation)
        self.assertNotIn('width:min(420px,100%)', presentation)
        self.assertIn(
            ':has(.hm-home-grid-anchor){height:auto!important;min-height:0!important',
            page,
        )
        self.assertIn('min-height:0!important;box-shadow:none!important', page)

    def test_task_progress_uses_natural_height_and_breathing_space(self):
        page = (ROOT / "pages/02_Member_Home.py").read_text()

        self.assertIn('padding:1rem 1rem 1.04rem', page)
        self.assertIn('min-height:0;box-sizing:border-box', page)
        self.assertNotIn('min-height:15.75rem', page)
        self.assertIn('margin:.56rem 0 .24rem 0', page)

    def test_open_meals_render_in_real_compact_cards(self):
        source = (ROOT / "pages/18_Daily_Log.py").read_text()

        self.assertIn('hm-meal-entry-card-anchor', source)
        self.assertIn('with st.container(border=True):', source)
        self.assertIn(
            ':has(.hm-meal-entry-card-anchor){height:auto!important;min-height:0!important',
            source,
        )
        self.assertIn('padding:.68rem .76rem .78rem', source)

    def test_saved_day_cards_have_no_fixed_empty_height(self):
        source = (
            ROOT / "components/food_saved_days_presentation.py"
        ).read_text()

        self.assertIn('height:auto!important;min-height:0!important', source)
        self.assertIn('min-height:0;}', source)
        self.assertNotIn('min-height:12rem', source)
        self.assertNotIn('min-height:8.8rem', source)

    def test_schedule_actions_use_accept_reschedule_and_callbacks(self):
        home = (
            ROOT / "components/member_home_schedule_presentation.py"
        ).read_text()
        schedule = (ROOT / "components/schedule_timezone_ui.py").read_text()

        self.assertIn('"Accept"', home)
        self.assertIn('on_click=_accept_member_home_schedule', home)
        self.assertNotIn('"Acknowledge"', home)
        self.assertIn('"Accept"', schedule)
        self.assertIn('"Reschedule"', schedule)
        self.assertIn('on_click=_accept_member_schedule_once', schedule)
        self.assertIn('on_click=_toggle_member_reschedule_form', schedule)
        self.assertNotIn('"Acknowledge schedule"', schedule)
        self.assertNotIn('"Request Reschedule"', schedule)

    def test_initial_schedule_actions_do_not_explicitly_rerun(self):
        schedule = (ROOT / "components/schedule_timezone_ui.py").read_text()
        action_start = schedule.index('schedule_id = row.get("id")')
        action_end = schedule.index(
            'if row.get("reschedule_request_status") == "pending":',
            action_start,
        )
        action_block = schedule[action_start:action_end]

        self.assertNotIn('st.rerun()', action_block)
        self.assertIn('on_click=_accept_member_schedule_once', action_block)
        self.assertIn('on_click=_toggle_member_reschedule_form', action_block)


if __name__ == "__main__":
    unittest.main()
