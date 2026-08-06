from __future__ import annotations

import ast
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class AuthenticatedSmokeCorrectionTests(unittest.TestCase):
    def test_setup_shows_metadata_in_aligned_sections_without_more_details(self):
        source = (ROOT / "components/member_plan_builder_setup.py").read_text()
        start = source.index("classification_cols = st.columns(")
        end = source.index('if st.button(\n        "Save Setup"', start)
        block = source[start:end]
        self.assertNotIn('st.expander("More setup details"', source)
        self.assertIn("[1.15, 1, 1, 1.15]", block)
        self.assertIn('vertical_alignment="bottom"', block)
        for label in (
            '"Region / Food Culture"',
            '"Diet Type"',
            '"Age Band"',
            '"Health Concerns"',
            '"Nutritionist Note"',
            '"Change Note"',
        ):
            self.assertIn(label, block)
        self.assertIn("note_col, change_col = st.columns(2", block)
        self.assertNotIn("Clone Complete Plan copies Setup", source)

    def test_meals_remove_redundant_guide_and_disclosures_hide_native_marker(self):
        meals = (ROOT / "components/member_plan_builder_meals_compact.py").read_text()
        css = (ROOT / "components/profile_builder_modular.py").read_text()
        self.assertNotIn("mpb-meal-guide'><b>Recipe", meals)
        self.assertIn("font-size:0!important", css)
        self.assertIn('summary [data-testid="stIconMaterial"]', css)
        self.assertIn("summary:before", css)
        self.assertIn("details[open] summary:before", css)

    def test_view_member_plan_uses_weekly_tables_without_internal_banners(self):
        source = (ROOT / "components/member_plan_builder_view_compact.py").read_text()
        page = (ROOT / "pages/38_Admin_Recommendation_Profile_Builder.py").read_text()
        self.assertIn("def _render_meal_week_grid", source)
        self.assertIn("def _render_flat_plan_table", source)
        self.assertNotIn("def _render_grouped_weekly_table", source)
        self.assertIn('("Exercise", "Reps/Duration", "Timing", "Dates", "Status", "Remarks")', source)
        self.assertIn('("Supplement", "Dosage", "Timing", "Dates", "Status", "Remarks")', source)
        self.assertNotIn("Active-plan integrity verified", source)
        self.assertIn('begin_page_measurement("Recommendation Profile Builder")', page)
        self.assertIn('finish_and_render_page_diagnostics("Recommendation Profile Builder")', page)
        self.assertIn('_HIDDEN_BUILD_LABEL = "Full Admin integration build:"', page)
        self.assertIn("_install_build_label_suppression()", page)

    def test_repository_controls_use_sharp_tabs_and_centered_row_actions(self):
        for path in (
            "pages/15_Admin_Recipe_Manager.py",
            "pages/16_Admin_Exercise_Manager.py",
            "pages/39_Admin_Supplement_Manager.py",
        ):
            source = (ROOT / path).read_text()
            self.assertIn('button[role="tab"][aria-selected="true"]', source)
            self.assertIn('vertical_alignment="center"', source)
            self.assertIn('summary [data-testid="stIconMaterial"]', source)

    def test_schedule_empty_state_and_table_are_visibly_differentiated(self):
        source = (ROOT / "components/admin_schedule_feedback_aug04.py").read_text()
        self.assertIn("border:1.4px solid #D8A84E", source)
        self.assertIn("background:#FFF7E6", source)
        self.assertGreaterEqual(source.count("text-align:center"), 2)
        self.assertIn("vertical-align:middle", source)

    def test_member_home_uses_structural_header_and_readable_schedule_controls(self):
        page = (ROOT / "pages/02_Member_Home.py").read_text()
        runtime = (ROOT / "components/member_home_global_header_runtime.py").read_text()
        schedule = (ROOT / "components/member_home_schedule_presentation.py").read_text()
        self.assertIn("hm-member-home-local-style-v3", page)
        self.assertIn("hm-member-home-root-anchor", page)
        self.assertIn("with st.container():", page)
        self.assertNotIn("html,body,#root{margin-top:0", page)
        self.assertIn("hm-member-home-global-header-v9", runtime)
        self.assertIn('id="hm-member-home-local-style-v3"', schedule)
        self.assertIn("width:fit-content!important", schedule)
        self.assertNotIn("width:min(420px,100%)", schedule)
        self.assertNotIn("top:-2.75rem", schedule)

    def test_food_journal_uses_two_rows_and_add_preserves_daily_log_route(self):
        source = (ROOT / "pages/18_Daily_Log.py").read_text()
        ast.parse(source)
        start = source.index("def _render_meal_fields")
        end = source.index("def _render_meal_toggle", start)
        block = source[start:end]
        self.assertIn("hm-meal-time-grid-anchor", source)
        self.assertIn("hm-meal-food-grid-anchor", source)
        self.assertIn('time_cols = st.columns(3, gap="medium")', block)
        self.assertIn("food_col, portion_col = st.columns([2.2, 1.25]", block)
        self.assertIn("hm_daily_log_add_food_item_", block)
        self.assertIn('st.session_state["_hm_h13r9e_pending_rerun_path"] = "Daily_Log"', block)


if __name__ == "__main__":
    unittest.main()