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

    def test_member_home_compact_css_targets_current_local_style_only(self):
        source = (
            ROOT / "components/member_home_schedule_presentation.py"
        ).read_text()
        self.assertIn('id="hm-member-home-local-style-v3"', source)
        self.assertIn("hm-member-home-compact-polish-v8", source)
        self.assertNotIn("top:-2.75rem", source)
        self.assertIn("width:fit-content", source)
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

    def test_expander_divider_is_removed_and_pill_is_balanced(self):
        source = (
            ROOT / "components/member_home_schedule_presentation.py"
        ).read_text()
        self.assertIn("width:fit-content", source)
        self.assertIn("max-width:100%", source)
        self.assertIn('[data-testid="stExpanderDetails"]', source)
        self.assertIn("summary + div", source)
        self.assertIn("border-top:0", source)
        self.assertIn("hr{", source)
        self.assertIn("display:none", source)

    def test_consultation_cards_fill_their_responsive_member_home_column(self):
        source = (
            ROOT / "components/member_home_schedule_presentation.py"
        ).read_text()
        self.assertIn(".hm-v101-schedule-card", source)
        self.assertIn("width:100%", source)
        self.assertIn("max-width:none", source)
        self.assertIn("margin:0", source)
        self.assertNotIn("width:47%", source)

    def test_upcoming_pill_remains_visible_when_no_schedule_requires_action(self):
        page = (ROOT / "pages/02_Member_Home.py").read_text()
        expander = page.index("with st.expander(")
        label = page.index('f"Upcoming Consultation ({len(upcoming_schedules)})"')
        empty_guard = page.index("if not upcoming_schedules:", label)
        empty_state = page.index("No upcoming consultation requires action.", empty_guard)
        self.assertLess(expander, label)
        self.assertLess(label, empty_guard)
        self.assertLess(empty_guard, empty_state)

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
            "require_member",
        ):
            self.assertNotIn(forbidden, source)


if __name__ == "__main__":
    unittest.main()
