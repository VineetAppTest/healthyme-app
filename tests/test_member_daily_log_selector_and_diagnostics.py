from __future__ import annotations

import pathlib
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]


class MemberDailyLogSelectorAndDiagnosticsTests(unittest.TestCase):
    def test_daily_log_selector_uses_explicit_primary_button_state(self):
        source = (
            ROOT / "components/member_exercise_journal_table_bootstrap.py"
        ).read_text()
        self.assertIn('st.columns(2, gap="small")', source)
        self.assertIn('if current_value == _DAILY_LOG_LABELS[1]', source)
        self.assertIn('else "secondary"', source)

    def test_selector_does_not_mutate_its_widget_key_after_creation(self):
        source = (
            ROOT / "components/member_exercise_journal_table_bootstrap.py"
        ).read_text()
        forbidden = 'st.session_state[_DAILY_LOG_SELECTOR_KEY] = selected'
        self.assertNotIn(forbidden, source)
        self.assertIn("if current_value not in _DAILY_LOG_LABELS:", source)
        self.assertIn("on_click=_activate_daily_log_journal", source)

    def test_only_selected_daily_log_renderer_executes(self):
        source = (
            ROOT / "components/member_exercise_journal_table_bootstrap.py"
        ).read_text()
        self.assertIn("render_food_only_when_selected", source)
        self.assertIn("render_exercise_only_when_selected", source)
        self.assertIn("return [contextlib.nullcontext(), contextlib.nullcontext()]", source)

    def test_disabled_measurement_uses_footer_panel_only(self):
        source = (ROOT / "components/performance_measurement_gate.py").read_text()
        self.assertIn("if resolved_page.startswith(_MEMBER_PAGE_PREFIX):", source)
        self.assertIn("if diagnostics.measurement_enabled():", source)
        self.assertIn("if not diagnostics.measurement_enabled():", source)

    def test_diagnostics_remain_session_local_and_do_not_touch_routing(self):
        source = (ROOT / "components/performance_measurement_gate.py").read_text()
        for forbidden in (
            "switch_page",
            "require_member",
            "require_admin",
            "save_db",
            "save_state",
            "supabase",
        ):
            self.assertNotIn(forbidden, source)


if __name__ == "__main__":
    unittest.main()
