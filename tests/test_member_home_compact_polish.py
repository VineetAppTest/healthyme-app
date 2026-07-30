from __future__ import annotations

import pathlib
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]


class MemberHomeCompactPolishTests(unittest.TestCase):
    def test_exercise_repository_detail_copy_is_removed_only_from_member_row(self):
        source = (
            ROOT / "components/member_exercise_journal_layout_v4.py"
        ).read_text()
        self.assertNotIn("Repository details:", source)
        self.assertIn("base.repository_activity_catalog()", source)
        self.assertIn("base.save_member_exercise_log", source)

    def test_member_home_compact_css_targets_existing_local_style_only(self):
        source = (
            ROOT / "components/member_home_schedule_presentation.py"
        ).read_text()
        self.assertIn('id="hm-member-home-local-style-v2"', source)
        self.assertIn("hm-member-home-compact-polish-v3", source)
        self.assertIn("top:-2.75rem", source)
        self.assertIn("width:315px", source)
        self.assertIn("white-space:nowrap", source)
        self.assertIn("word-break:keep-all", source)
        self.assertIn("_install_member_home_compact_polish()", source)

    def test_expander_native_icon_is_hidden_and_custom_chevron_is_used(self):
        source = (
            ROOT / "components/member_home_schedule_presentation.py"
        ).read_text()
        self.assertIn('summary [data-testid="stExpanderToggleIcon"]', source)
        self.assertIn('summary [data-testid="stIconMaterial"]', source)
        self.assertIn("summary::before", source)
        self.assertIn('content:"›"', source)
        self.assertIn("details[open] summary::before", source)

    def test_expander_divider_is_removed_and_pill_is_wider(self):
        source = (
            ROOT / "components/member_home_schedule_presentation.py"
        ).read_text()
        self.assertIn("width:315px", source)
        self.assertIn("border-bottom:0", source)
        self.assertIn("summary::after", source)
        self.assertIn("content:none", source)

    def test_consultation_cards_are_centered_and_more_compact(self):
        source = (
            ROOT / "components/member_home_schedule_presentation.py"
        ).read_text()
        self.assertIn(".hm-v101-schedule-card", source)
        self.assertIn("width:78%", source)
        self.assertIn("max-width:760px", source)
        self.assertIn("margin:.34rem auto .52rem auto", source)
        self.assertIn("width:100%", source)

    def test_upcoming_pill_is_not_rendered_when_no_schedule_remains(self):
        page = (ROOT / "pages/02_Member_Home.py").read_text()
        empty_guard = page.index("if not upcoming_schedules:")
        empty_return = page.index("return", empty_guard)
        expander = page.index("with st.expander(", empty_guard)
        self.assertLess(empty_guard, empty_return)
        self.assertLess(empty_return, expander)

    def test_compact_polish_does_not_change_schedule_or_member_business_state(self):
        source = (
            ROOT / "components/member_home_schedule_presentation.py"
        ).read_text()
        for forbidden in (
            "save_db(",
            "update_member_schedule_status(",
            "create_timezone_aware_member_schedule(",
            "assign_or_replace_member_package(",
            "session_counted =",
            "logout_current_user",
            "switch_page",
            "require_member",
        ):
            self.assertNotIn(forbidden, source)


if __name__ == "__main__":
    unittest.main()
