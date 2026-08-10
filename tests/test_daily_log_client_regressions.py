from __future__ import annotations

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class DailyLogClientRegressionTests(unittest.TestCase):
    def test_field_contrast_layer_covers_ios_normal_focus_and_placeholder_states(self):
        source = (ROOT / "components/daily_log_field_contrast.py").read_text(
            encoding="utf-8"
        )
        guards = (ROOT / "components/guards.py").read_text(encoding="utf-8")
        guard_start = guards.index("def _apply_daily_log_ui_and_autosave")
        guard_end = guards.index("def _redirect_disabled_reference_page", guard_start)
        daily_log_guard = guards[guard_start:guard_end]

        for contract in (
            'id="hm-daily-log-field-contrast-v1"',
            'div[data-testid="stTextInput"]',
            'div[data-testid="stTextArea"]',
            'div[data-testid="stTimeInput"]',
            'div[data-testid="stDateInput"]',
            'div[data-testid="stSelectbox"]',
            '[data-baseweb="input"]',
            '[data-baseweb="base-input"]',
            '[data-baseweb="select"]',
            'background-color:#FFFFFF!important',
            'color:#0F172A!important',
            '-webkit-text-fill-color:#0F172A!important',
            'caret-color:#064E3B!important',
            'color-scheme:light!important',
            '::placeholder',
            ':focus-within',
            ':-webkit-autofill',
        ):
            self.assertIn(contract, source)

        self.assertIn('[data-baseweb="base-input"]', daily_log_guard)
        self.assertIn('-webkit-text-fill-color:#0F172A!important', daily_log_guard)
        self.assertNotIn('input{border:0!important;outline:0!important;box-shadow:none!important;background:transparent', daily_log_guard)

    def test_daily_log_renders_contrast_layer_after_legacy_page_css(self):
        source = (ROOT / "pages/18_Daily_Log.py").read_text(encoding="utf-8")

        self.assertIn(
            "from components.daily_log_field_contrast import "
            "render_daily_log_field_contrast",
            source,
        )
        self.assertLess(
            source.index("_render_css()", source.index("require_member()")),
            source.index("render_daily_log_field_contrast()"),
        )

    def test_member_home_uses_staged_daily_log_switch_without_changing_other_actions(self):
        home = (ROOT / "pages/02_Member_Home.py").read_text(encoding="utf-8")
        router = (
            ROOT / "native_bridge/native_bridge_full_member_app.py"
        ).read_text(encoding="utf-8")
        start = router.index("def _embedded_switch_handler(")
        end = router.index("def _native_utility_bar", start)
        block = router[start:end]

        self.assertIn('"pages/18_Daily_Log.py"', home)
        self.assertIn('str(getattr(resolved, "url_path", "")', block)
        self.assertIn(
            "st.session_state[_PENDING_RERUN_PATH_KEY] = resolved_path",
            block,
        )
        self.assertLess(
            block.index("st.session_state[_PENDING_RERUN_PATH_KEY]"),
            block.index("_ORIGINAL_SWITCH_PAGE(resolved)"),
        )


if __name__ == "__main__":
    unittest.main()
