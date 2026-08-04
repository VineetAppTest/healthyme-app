from __future__ import annotations

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class StreamlitUiConsistencyBatchTests(unittest.TestCase):
    def test_food_journal_keeps_exact_five_part_row(self):
        source = (ROOT / "pages/18_Daily_Log.py").read_text()
        start = source.index(".hm-meal-entry-grid-anchor")
        end = source.index(".hm-toggle-body:empty", start)
        css = source[start:end]

        self.assertIn(
            "grid-template-columns:minmax(4.75rem,.72fr) minmax(5.10rem,.78fr) minmax(5.55rem,.92fr) minmax(15rem,2.15fr) minmax(9rem,1.35fr)!important",
            css,
        )
        self.assertIn('>div[data-testid="stColumn"]', css)
        self.assertIn('>div[data-testid="column"]', css)
        self.assertIn("@media(max-width:780px)", css)
        render_start = source.index("def _render_meal_fields")
        render_end = source.index("def _render_meal_toggle", render_start)
        renderer = source[render_start:render_end]
        for label in ('"Hour"', '"Minutes"', '"AM/PM"', 'f"Food Item {idx + 1}"', 'f"Portion {idx + 1}"'):
            self.assertIn(label, renderer)

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
        source = (ROOT / "components/repository_layout_correction_runtime.py").read_text()

        self.assertIn('div[data-testid="stSegmentedControl"]', source)
        self.assertIn("border-radius:9px!important", source)
        self.assertIn('>div[data-testid="stColumn"]', source)
        self.assertIn('>div[data-testid="column"]', source)
        self.assertIn("justify-content:center!important;gap:0!important", source)
        self.assertIn("details[open] summary:before", source)
        self.assertIn("white-space:normal!important", source)
        self.assertIn("text-overflow:clip!important", source)

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

    def test_member_plan_meals_use_native_dataframe_format(self):
        source = (ROOT / "components/member_plan_builder_view_compact.py").read_text()

        self.assertIn("def _meal_plan_rows", source)
        self.assertIn('"Start Date": start_date', source)
        self.assertIn('"Type": "Meal"', source)
        self.assertIn('"Day": f"Day {day}"', source)
        self.assertIn("pd.DataFrame(_meal_plan_rows(start_date, items))", source)
        self.assertIn("use_container_width=True", source)
        self.assertIn("hide_index=True", source)
        render_start = source.index("def render_view_member_plan_compact")
        self.assertNotIn("_render_profile_table(", source[render_start:])


if __name__ == "__main__":
    unittest.main()
