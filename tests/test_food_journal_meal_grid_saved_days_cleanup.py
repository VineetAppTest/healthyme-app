from __future__ import annotations

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class FoodJournalMealGridSavedDaysCleanupTests(unittest.TestCase):
    def test_meal_entry_uses_two_row_time_and_food_grid(self):
        source = (ROOT / "pages/18_Daily_Log.py").read_text()
        start = source.index("def _render_meal_fields")
        end = source.index("def _render_meal_toggle", start)
        block = source[start:end]
        self.assertIn('time_cols = st.columns(3, gap="medium")', block)
        self.assertIn("food_col, portion_col = st.columns([2.2, 1.25]", block)
        self.assertIn('"Hour"', block)
        self.assertIn('"Minutes"', block)
        self.assertIn('"AM/PM"', block)
        self.assertIn('f"Food Item {idx + 1}"', block)
        self.assertIn('f"Portion {idx + 1}"', block)
        self.assertIn("hm_daily_hour_v13_", block)
        self.assertIn("hm_daily_minute_v13_", block)
        self.assertIn("hm_daily_ampm_v13_", block)
        self.assertIn("hm_daily_log_add_food_item_", block)
        self.assertIn("_stage_daily_log_route()", block)
        self.assertLess(
            block.index("_stage_daily_log_route()"),
            block.index("st.rerun()"),
        )
        self.assertNotIn("st.time_input(", block)

    def test_meal_disclosure_text_is_left_aligned(self):
        source = (ROOT / "pages/18_Daily_Log.py").read_text()

        self.assertIn(
            'div[data-testid="stElementContainer"]:has(.hm-toggle-anchor)',
            source,
        )
        self.assertIn("justify-content:flex-start!important", source)
        self.assertIn("button p{width:100%!important;text-align:left!important", source)

    def test_saved_days_keeps_only_direct_three_column_cards(self):
        page = (ROOT / "pages/18_Daily_Log.py").read_text()
        dispatch = (
            ROOT / "components/member_saved_days_dispatch_runtime.py"
        ).read_text()
        cleanup = (
            ROOT / "components/member_saved_days_home_cleanup.py"
        ).read_text()

        self.assertIn('st.columns(3, gap="small")', page)
        self.assertIn("saved_day_card_html", page)
        self.assertNotIn('"Open saved day"', page)
        self.assertNotIn("Viewing saved entries for", page)
        self.assertNotIn("_render_filtered_meal_summary", dispatch)
        self.assertNotIn("dt.timedelta(days=6)", dispatch)

        saved_start = cleanup.index("def _install_saved_days_window")
        saved_end = cleanup.index("def _install_member_home_cleanup", saved_start)
        saved_block = cleanup[saved_start:saved_end]
        self.assertIn("return None", saved_block)
        self.assertNotIn("st.columns", saved_block)
        self.assertNotIn("_render_filtered_meal_summary", saved_block)

        # The independent Member Home compatibility layer remains installed.
        self.assertIn("def _install_member_home_cleanup", cleanup)
        self.assertIn("_install_member_home_cleanup()", cleanup)


if __name__ == "__main__":
    unittest.main()
