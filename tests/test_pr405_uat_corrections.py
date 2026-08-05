from __future__ import annotations

import ast
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class Pr405UatCorrectionTests(unittest.TestCase):
    def _source(self, path: str) -> str:
        source = (ROOT / path).read_text(encoding="utf-8")
        if path.endswith(".py"):
            ast.parse(source)
        return source

    def test_setup_hides_repeated_labels_and_preserves_natural_field_width(self):
        source = self._source("components/member_plan_builder_setup.py")
        row_start = source.index('row1 = st.columns(1')
        row_end = source.index("classification_cols = st.columns(", row_start)
        row = source[row_start:row_end]
        self.assertEqual(row.count('label_visibility="collapsed"'), 1)
        self.assertIn("[1.15, 1, 1, 1.15]", source)
        self.assertNotIn("repeat(auto-fit,minmax", source)

    def test_meal_and_exercise_details_use_natural_width_and_visible_open_body(self):
        meals = self._source("components/member_plan_builder_meals_compact.py")
        exercise = self._source("components/member_plan_builder_exercise.py")
        self.assertNotIn("mpb-responsive-detail-wide", meals)
        self.assertNotIn("mpb-exercise-detail-wide", exercise)
        self.assertIn("details[open]>div", exercise)
        self.assertIn("max-height:none!important", exercise)
        self.assertIn("safe(value)", exercise)

    def test_supplement_frequency_requires_matching_multiple_timings(self):
        source = self._source("components/member_plan_builder_supplement.py")
        self.assertIn('"Thrice": 3', source)
        self.assertIn('"Night"', source)
        self.assertGreaterEqual(source.count('.multiselect(\n            "Timing"'), 2)
        self.assertGreaterEqual(source.count("_frequency_timing_error(frequency, timing)"), 2)
        self.assertGreaterEqual(source.count('timing=", ".join(timing)'), 2)
        self.assertNotIn("source_summary(", source)

    def test_publish_creates_member_copy_before_activation(self):
        source = self._source("components/member_plan_builder_meals_compact.py")
        start = source.index("def _publish_repository_plan")
        end = source.index("def render_member_plan_meals_compact", start)
        block = source[start:end]
        self.assertIn('"start_date": clean(start_date)', block)
        self.assertIn('"clone_source_profile_id": source_id', block)
        self.assertIn('activate_profile(member_plan, "ACTIVATE")', block)
        self.assertNotIn('activate_profile(profile, "ACTIVATE")', block)

    def test_member_header_has_explicit_control_and_section_spacing(self):
        source = self._source("components/member_home_global_header_runtime.py")
        self.assertIn("hm-member-home-global-header-v8", source)
        self.assertIn("margin:.16rem 0 1rem 0!important", source)
        self.assertIn("margin-top:.78rem!important", source)
        self.assertIn(
            '[data-testid="stButton"]>button{height:2.46rem!important',
            source,
        )
        self.assertNotIn("margin-top:-", source)

    def test_food_time_controls_fill_three_columns_and_staged_route_wins(self):
        journal = self._source("pages/18_Daily_Log.py")
        router = self._source("app.py")
        self.assertIn('time_cols = st.columns(3, gap="medium")', journal)
        self.assertIn("grid-template-columns:repeat(3,minmax(7.5rem,1fr))", journal)
        self.assertIn("and not staged_path", router)

    def test_member_route_does_not_render_internal_build_footer(self):
        source = self._source("native_bridge/native_bridge_full_member_app.py")
        route_start = source.index("def _render_member_route")
        route_end = source.index("def _make_member_page", route_start)
        route_block = source[route_start:route_end]
        self.assertNotIn("Full Member integration build:", route_block)
        self.assertNotIn("spec.source_path", route_block[-400:])


if __name__ == "__main__":
    unittest.main()
