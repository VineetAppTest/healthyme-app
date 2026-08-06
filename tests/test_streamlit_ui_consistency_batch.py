from __future__ import annotations

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class StreamlitUiConsistencyBatchTests(unittest.TestCase):
    def test_food_journal_uses_two_row_time_and_food_structure(self):
        source = (ROOT / "pages/18_Daily_Log.py").read_text()
        self.assertIn("hm-meal-time-grid-anchor", source)
        self.assertIn("hm-meal-food-grid-anchor", source)
        render_start = source.index("def _render_meal_fields")
        render_end = source.index("def _render_meal_toggle", render_start)
        renderer = source[render_start:render_end]
        self.assertIn('time_cols = st.columns(3, gap="medium")', renderer)
        self.assertIn("food_col, portion_col = st.columns([2.2, 1.25]", renderer)
        self.assertIn('"Hour"', renderer)
        self.assertIn('"Minutes"', renderer)
        self.assertIn('"AM/PM"', renderer)
        self.assertIn('f"Food Item {idx + 1}"', renderer)
        self.assertIn('f"Portion {idx + 1}"', renderer)
        self.assertIn("hm_daily_log_add_food_item_", renderer)

    def test_food_autosave_uses_direct_payload_boundary(self):
        page = (ROOT / "pages/18_Daily_Log.py").read_text()
        runtime = (ROOT / "components/member_journal_server_autosave.py").read_text()

        self.assertIn("autosave_food_payload(", page)
        self.assertIn("mark_food_payload_saved(user_id, date_key, payload)", page)
        self.assertIn("save_func(user_id, date_key, current_payload)", runtime)
        self.assertIn("Never synthesize a Save Day click", runtime)
        food_branch = runtime[runtime.index('if text == _FOOD_BUTTON:'):runtime.index('if text == _EXERCISE_BUTTON')]
        self.assertIn("return clicked", food_branch)
        self.assertNotIn("_should_autosave_food()", food_branch)
        direct_api = runtime[runtime.index("def autosave_food_payload"):runtime.index("def _exercise_baseline_key")]
        self.assertNotIn("st.rerun(", direct_api)
        self.assertNotIn("set_system_message", direct_api)

    def test_repository_controls_are_sharp_aligned_and_untruncated(self):
        runtime = (ROOT / "components/repository_layout_correction_runtime.py").read_text()
        for page_path in (
            "pages/15_Admin_Recipe_Manager.py",
            "pages/16_Admin_Exercise_Manager.py",
            "pages/39_Admin_Supplement_Manager.py",
        ):
            page = (ROOT / page_path).read_text()
            self.assertIn('button[role="tab"][aria-selected="true"]', page)
            self.assertIn('vertical_alignment="center"', page)
            self.assertIn('summary [data-testid="stIconMaterial"]', page)
        self.assertIn("details[open] summary:before", runtime)
        self.assertIn("white-space:normal!important", runtime)
        self.assertIn("text-overflow:clip!important", runtime)

    def test_profile_builder_disclosures_share_full_label_contract(self):
        source = (ROOT / "components/profile_builder_modular.py").read_text()
        start = source.index('div[data-testid="stExpander"]{')
        end = source.index("@media(max-width:980px)", start)
        css = source[start:end]

        self.assertIn("summary:before", css)
        self.assertIn("details[open] summary:before", css)
        self.assertIn("white-space:normal!important", css)
        self.assertIn("overflow:visible!important", css)
        self.assertNotIn("text-overflow:ellipsis", css)

    def test_member_plan_uses_consistent_weekly_tables(self):
        source = (ROOT / "components/member_plan_builder_view_compact.py").read_text()
        self.assertIn("def _render_meal_week_grid", source)
        self.assertIn("def _render_flat_plan_table", source)
        self.assertIn("mpb-weekly-plan-grid-v1", source)
        self.assertIn("<th>Day</th>", source)
        self.assertNotIn("def _render_grouped_weekly_table", source)
        self.assertIn('("Exercise", "Reps/Duration", "Timing", "Dates", "Status", "Remarks")', source)
        self.assertIn('("Supplement", "Dosage", "Timing", "Dates", "Status", "Remarks")', source)
        self.assertNotIn("Active-plan integrity verified", source)




if __name__ == "__main__":
    unittest.main()